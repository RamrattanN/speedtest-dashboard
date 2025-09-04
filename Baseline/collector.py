#!/usr/bin/env python3
"""
Speedtest collector.

- Runs a speed test and appends results to a CSV "spreadsheet".
- Keeps only the last 30 days of data.
- Default storage: r"C:\\Users\\niles\\Dropbox\\Python Code\\Speedtest\\speedtest_results.csv"

Usage examples:
  python collector.py
  python collector.py --daemon --interval 120
  python collector.py --path "C:\\Users\\niles\\Dropbox\\Python Code\\Speedtest\\speedtest_results.csv"
"""
from __future__ import annotations

import argparse
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import speedtest  # pip install speedtest-cli

# ---- Configuration ----
COLUMNS = ["timestamp", "ping_ms", "download_mbps", "upload_mbps"]
DEFAULT_CSV = Path(r"C:\Users\niles\Dropbox\Python Code\Speedtest\speedtest_results.csv")


def resolve_output_path(custom_path: str | None) -> Path:
    out = Path(custom_path) if custom_path else DEFAULT_CSV
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


def ensure_csv_exists(path: Path) -> None:
    """Create an empty CSV with headers if it does not exist yet."""
    if not path.exists():
        pd.DataFrame(columns=COLUMNS).to_csv(path, index=False)


def run_speedtest() -> dict:
    st = speedtest.Speedtest()
    st.get_best_server()
    download_bps = st.download()
    upload_bps = st.upload()
    ping_ms = float(st.results.ping)
    ts = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    return {
        "timestamp": ts,
        "ping_ms": ping_ms,
        "download_mbps": round(download_bps / 1_000_000, 3),
        "upload_mbps": round(upload_bps / 1_000_000, 3),
    }


def load_existing(path: Path) -> pd.DataFrame:
    if path.exists():
        try:
            df = pd.read_csv(path)
            for c in COLUMNS:
                if c not in df.columns:
                    df[c] = pd.NA
            return df[COLUMNS]
        except Exception:
            return pd.DataFrame(columns=COLUMNS)
    return pd.DataFrame(columns=COLUMNS)


def prune_30_days(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    cutoff = pd.Timestamp.utcnow() - pd.Timedelta(days=30)
    df = df[df["timestamp"] >= cutoff]
    df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return df


def save_atomic(df: pd.DataFrame, path: Path) -> None:
    """
    Write CSV atomically with Windows-friendly retries.
    Handles transient file locks from Excel/Dropbox/AV and the dashboard reader.
    """
    path = Path(path)
    tmp_dir = path.parent

    # Write to a unique temp file in the same directory
    with tempfile.NamedTemporaryFile(
        delete=False,
        dir=tmp_dir,
        prefix=path.stem + "_",
        suffix=".tmp",
        mode="w",
        newline="",
        encoding="utf-8",
    ) as f:
        df.to_csv(f, index=False)
        tmp_path = Path(f.name)

    # Try to replace with exponential backoff
    last_err = None
    for attempt in range(8):
        try:
            os.replace(tmp_path, path)  # atomic if not locked
            return
        except PermissionError as e:
            last_err = e
            time.sleep(0.5 * (attempt + 1))

    # Fallback: try direct write if replace kept failing
    try:
        df.to_csv(path, index=False)
    except Exception:
        # If even direct write fails, re-raise the original lock error
        raise last_err
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", help="Full path to speedtest_results.csv")
    ap.add_argument(
        "--interval",
        type=int,
        default=120,  # 2 minutes by default
        help="Seconds between tests when --daemon is used.",
    )
    ap.add_argument(
        "--daemon",
        action="store_true",
        help="Run continuously every --interval seconds.",
    )
    args = ap.parse_args()

    out_path = resolve_output_path(args.path)
    ensure_csv_exists(out_path)

    def once():
        row = run_speedtest()
        df = load_existing(out_path)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True) if not df.empty else pd.DataFrame([row])
        df = prune_30_days(df)
        save_atomic(df, out_path)
        print(
            f"[{row['timestamp']}] ping={row['ping_ms']} ms, down={row['download_mbps']} Mbps, "
            f"up={row['upload_mbps']} Mbps  ->  {out_path}"
        )

    if args.daemon:
        while True:
            once()
            time.sleep(max(5, int(args.interval)))
    else:
        once()


if __name__ == "__main__":
    main()
