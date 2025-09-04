#!/usr/bin/env python3
"""
Generate a year of dummy Speedtest data with realistic variability and outages.

Defaults:
- Start: 2024-08-13 00:00:00Z
- End:   2025-08-13 23:59:59Z
- Interval: 2 minutes
- Uptime target: ~97% (>=95%) with outages of 10–240 minutes each, non-overlapping
- Columns: timestamp,ping_ms,download_mbps,upload_mbps,server_id,server_name
- Timezone: UTC (timestamps end in 'Z')

Usage examples:
  python generate_dummy_history.py --out "C:\\Users\\niles\\Dropbox\\Python Code\\Speedtest\\speedtest_history_2024-08-13_to_2025-08-13.csv"

  # Optional: split into monthly archive files instead of one large CSV
  python generate_dummy_history.py --split-monthly --outdir "C:\\Users\\niles\\Dropbox\\Python Code\\Speedtest\\archive"

  # Adjust parameters if needed
  python generate_dummy_history.py --interval 2 --uptime 0.97 --seed 42
"""

from __future__ import annotations
import argparse
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd


def build_time_index(start_iso: str, end_iso: str, interval_minutes: int) -> pd.DatetimeIndex:
    return pd.date_range(
        pd.Timestamp(start_iso, tz="UTC"),
        pd.Timestamp(end_iso, tz="UTC"),
        freq=f"{interval_minutes}min",
        inclusive="both",
    )


def generate_series(ts: pd.DatetimeIndex, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generate download, upload, ping with diurnal pattern, noise, and some spikes."""
    n = len(ts)
    hours = ts.tz_convert("UTC").hour.values

    # Diurnal pattern: a couple of sinusoids for daily rhythm
    diurnal = 0.15 * np.sin((hours - 4) / 24 * 2 * np.pi) - 0.10 * np.sin((hours - 21) / 24 * 2 * np.pi)

    base_down = 300 * (1 + diurnal)               # ~300 Mbps baseline
    base_up   =  90 * (1 + 0.5 * diurnal)         # ~90 Mbps baseline

    noise_down = rng.normal(0, 25, size=n)
    noise_up   = rng.normal(0, 8,  size=n)

    download = np.clip(base_down + noise_down, 30, None)
    upload   = np.clip(base_up   + noise_up,   5,  None)

    ping = 35 + rng.normal(0, 4, size=n) + (320 - np.clip(download, 50, 320)) / 80.0
    ping = np.clip(ping, 10, 120)

    # Occasional brief perturbations
    spikes = rng.choice(n, size=max(1, int(0.002 * n)), replace=False)
    download[spikes] *= rng.uniform(0.5, 1.1, size=spikes.size)
    upload[spikes]   *= rng.uniform(0.5, 1.1, size=spikes.size)
    ping[spikes]     += rng.uniform(10, 60, size=spikes.size)

    return download, upload, ping


def build_outages(ts: pd.DatetimeIndex, interval_minutes: int, rng: np.random.Generator,
                  target_uptime: float) -> np.ndarray:
    """
    Create a boolean mask for outages.  Each outage is 10–240 minutes, non-overlapping.
    Total downtime chosen so uptime >= target_uptime (defaults around 97%).
    """
    n = len(ts)
    total_minutes = (ts[-1] - ts[0]).total_seconds() / 60 + interval_minutes
    # Plan for slightly more than needed so we can prune later if necessary
    target_downtime = max(0, (1 - target_uptime) * total_minutes)

    outage_mask = np.zeros(n, dtype=bool)
    max_outage = 240     # minutes
    min_outage = 10      # minutes
    added = 0.0
    attempts = 0
    max_attempts = 4000

    while added < target_downtime and attempts < max_attempts:
        attempts += 1
        dur_min = rng.integers(min_outage, max_outage + 1)
        steps = int(np.ceil(dur_min / interval_minutes))
        start_idx = rng.integers(0, n - steps)
        if outage_mask[start_idx:start_idx + steps].any():
            continue
        outage_mask[start_idx:start_idx + steps] = True
        added += steps * interval_minutes

    # If we overshot, trim some blocks randomly
    if added > target_downtime:
        excess = added - target_downtime
        idx = np.where(outage_mask)[0]
        if idx.size:
            cut = int(min(idx.size, np.floor(excess / interval_minutes)))
            if cut > 0:
                drop_idx = rng.choice(idx, size=cut, replace=False)
                outage_mask[drop_idx] = False

    return outage_mask


def inject_outages(download: np.ndarray, upload: np.ndarray, ping: np.ndarray,
                   outage_mask: np.ndarray, rng: np.random.Generator) -> None:
    download[outage_mask] = 0.0
    upload[outage_mask]   = 0.0
    # Elevated ping or packet loss proxy during outages
    ping[outage_mask]     = rng.uniform(200, 600, size=outage_mask.sum())


def add_servers(ts: pd.DatetimeIndex, n: int, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Assign server_id/server_name sparsely for realism."""
    server_id = np.array([""] * n, dtype=object)
    server_name = np.array([""] * n, dtype=object)

    # More labels in more recent periods
    mask_202501 = ts >= pd.Timestamp("2025-01-01T00:00:00Z")
    mask_202506 = ts >= pd.Timestamp("2025-06-01T00:00:00Z")

    idx_202501 = np.where(mask_202501)[0]
    idx_202506 = np.where(mask_202506)[0]

    if idx_202501.size:
        sel_30 = rng.choice(idx_202501, size=int(0.30 * idx_202501.size), replace=False)
        server_id[sel_30] = "20013"
        server_name[sel_30] = "OneNet - Tulsa, OK"

    if idx_202506.size:
        sel_60 = rng.choice(idx_202506, size=int(0.60 * idx_202506.size), replace=False)
        server_id[sel_60] = "20013"
        server_name[sel_60] = "OneNet - Tulsa, OK"

    # Sprinkle a couple of alternative servers
    alt = [("12345", "ExampleTel - Dallas, TX"), ("33021", "MetroNet - Oklahoma City, OK")]
    for sid, sname in alt:
        picks = rng.choice(n, size=max(1, int(0.01 * n)), replace=False)
        server_id[picks] = sid
        server_name[picks] = sname

    return server_id, server_name


def generate_dataframe(start: str, end: str, interval: int, uptime: float, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    ts = build_time_index(start, end, interval)
    n = len(ts)

    download, upload, ping = generate_series(ts, rng)
    outage_mask = build_outages(ts, interval, rng, uptime)
    inject_outages(download, upload, ping, outage_mask, rng)

    sid, sname = add_servers(ts, n, rng)

    df = pd.DataFrame({
        "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ping_ms": np.round(ping, 3),
        "download_mbps": np.round(download, 3),
        "upload_mbps": np.round(upload, 3),
        "server_id": sid,
        "server_name": sname,
    })
    return df


def write_single(df: pd.DataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"[OK] Wrote: {out_path}  rows={len(df):,}")


def write_monthly(df: pd.DataFrame, outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    ts = pd.to_datetime(df["timestamp"], utc=True)
    df["_year"] = ts.dt.year
    df["_month"] = ts.dt.month
    for (y, m), g in df.groupby(["_year", "_month"]):
        p = outdir / f"speedtest_{y:04d}-{m:02d}.csv"
        g.drop(columns=["_year", "_month"]).to_csv(p, index=False)
        print(f"[OK] Wrote: {p}  rows={len(g):,}")
    df.drop(columns=["_year", "_month"], inplace=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2024-08-13T00:00:00Z")
    ap.add_argument("--end",   default="2025-08-13T23:59:59Z")
    ap.add_argument("--interval", type=int, default=2, help="Minutes between samples")
    ap.add_argument("--uptime", type=float, default=0.97, help="Target uptime in [0,1]")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", help="Path to write a single CSV")
    ap.add_argument("--split-monthly", action="store_true", help="Write monthly files to --outdir instead of single CSV")
    ap.add_argument("--outdir", help="Directory for monthly files if --split-monthly is set")
    args = ap.parse_args()

    df = generate_dataframe(args.start, args.end, args.interval, args.uptime, args.seed)

    if args.split_monthly:
        outdir = Path(args.outdir) if args.outdir else Path.cwd() / "archive_generated"
        write_monthly(df, outdir)
    else:
        out_path = Path(args.out) if args.out else Path.cwd() / "speedtest_history.csv"
        write_single(df, out_path)


if __name__ == "__main__":
    main()
