#!/usr/bin/env python3
"""
Speedtest collector with engine tagging, Ookla license handling, and safe fallbacks.

Features:
- Prefers Ookla CLI with explicit license/GDPR acceptance flags.  Falls back to Python speedtest-cli on failure or if CLI is missing.
- Retries with exponential backoff on transient errors (e.g., 403) and rc=1 license prompts.
- Records UTC timestamps.
- Main CSV retains 30 days.  Monthly archives retain 12 months.
- Multi-server support (--servers "id1,id2").
- Atomic writes with retries (Dropbox/Excel/AV friendly).
- Engine column indicates 'ookla-cli' or 'python-lib'.

Usage:
  python collector.py                                  # run once (best server)
  python collector.py --daemon --interval 120          # every 2 minutes
  python collector.py --servers 20013,12345            # test specific server IDs
  python collector.py --list-servers 10                # list 10 nearby servers and exit

Optional flags:
  --require-ookla    Error out if Ookla CLI is not installed.
  --no-ookla         Do not use Ookla CLI even if present.

Prereqs:
  pip install pandas speedtest-cli
  (Recommended) Install Ookla CLI and add to PATH.  If missing, this script will still run via Python fallback.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Tuple

import pandas as pd

# ---------- Paths / Config ----------
ROOT = Path(r"C:\Users\niles\Dropbox\Python Code\Speedtest")
DEFAULT_CSV = ROOT / "speedtest_results.csv"
ARCHIVE_DIR = ROOT / "archive"

COLUMNS = ["timestamp", "ping_ms", "download_mbps", "upload_mbps", "server_id", "server_name", "engine"]
MAIN_RETENTION_DAYS = 30
ARCHIVE_RETENTION_MONTHS = 12

# One-time info flag
_ookla_guidance_printed = False


# ---------- Filesystem helpers ----------
def ensure_paths() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


def ensure_csv_exists(path: Path) -> None:
    if not path.exists():
        pd.DataFrame(columns=COLUMNS).to_csv(path, index=False)


def save_atomic(df: pd.DataFrame, path: Path) -> None:
    """Atomic write with retries to survive transient Windows locks (Excel/Dropbox/AV)."""
    path = Path(path)
    tmp_dir = path.parent
    with tempfile.NamedTemporaryFile(
        delete=False, dir=tmp_dir, prefix=path.stem + "_", suffix=".tmp", mode="w", newline="", encoding="utf-8"
    ) as f:
        df.to_csv(f, index=False)
        tmp_path = Path(f.name)

    last_err = None
    for attempt in range(8):
        try:
            os.replace(tmp_path, path)
            return
        except PermissionError as e:
            last_err = e
            time.sleep(0.5 * (attempt + 1))

    # Fallback direct write
    try:
        df.to_csv(path, index=False)
    except Exception:
        if last_err:
            raise last_err
        raise
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass


# ---------- Data helpers ----------
def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_existing(path: Path) -> pd.DataFrame:
    if path.exists():
        try:
            df = pd.read_csv(path)
        except Exception:
            df = pd.DataFrame()
    else:
        df = pd.DataFrame()

    for c in COLUMNS:
        if c not in df.columns:
            df[c] = pd.NA

    return df[COLUMNS]


def append_row_inplace(df: pd.DataFrame, row: Dict) -> None:
    for c in COLUMNS:
        if c not in df.columns:
            df[c] = pd.NA
    df.loc[len(df)] = [row.get(c, pd.NA) for c in COLUMNS]


def prune_main(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    ts = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    cutoff = pd.Timestamp.utcnow() - pd.Timedelta(days=MAIN_RETENTION_DAYS)
    kept = df[ts >= cutoff].copy()
    kept["timestamp"] = pd.to_datetime(kept["timestamp"], utc=True, errors="coerce").dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return kept


def archive_append(row: Dict) -> None:
    ts = pd.to_datetime(row["timestamp"], utc=True, errors="coerce")
    key = ts.strftime("%Y-%m")
    path = ARCHIVE_DIR / f"speedtest_{key}.csv"

    if path.exists():
        try:
            df = pd.read_csv(path)
        except Exception:
            df = pd.DataFrame()
    else:
        df = pd.DataFrame()

    for c in COLUMNS:
        if c not in df.columns:
            df[c] = pd.NA

    append_row_inplace(df, row)
    save_atomic(df, path)

    files = sorted(ARCHIVE_DIR.glob("speedtest_*.csv"))
    if len(files) > ARCHIVE_RETENTION_MONTHS:
        for f in files[: len(files) - ARCHIVE_RETENTION_MONTHS]:
            try:
                f.unlink()
            except Exception:
                pass


# ---------- Server info sanitation ----------
def sanitize_server_info(server_id: Optional[str], server_name: Optional[str]) -> Tuple[str, str]:
    sid = "" if server_id is None else str(server_id).strip()
    if sid.lower() in {"nan", "none"}:
        sid = ""
    if sid.endswith(".0"):
        sid = sid[:-2]
    sname = (server_name or "").strip()
    if sname.lower() in {"nan", "none"}:
        sname = ""
    return sid, sname


# ---------- Ookla CLI vs Python library ----------
def have_ookla_cli() -> bool:
    exe = shutil.which("speedtest")
    return exe is not None


def print_ookla_install_guidance_once() -> None:
    global _ookla_guidance_printed
    if _ookla_guidance_printed:
        return
    _ookla_guidance_printed = True
    print(
        "\n[INFO] Ookla Speedtest CLI was not found on PATH.  Using the Python speedtest-cli fallback.\n"
        "       The official Ookla CLI is more reliable and avoids 403 errors.\n"
        "       Install it on Windows via ZIP: https://www.speedtest.net/apps/cli  → extract to e.g. C:\\Tools\\OoklaSpeedtest\n"
        "       Then add that folder to your PATH.  Verify with:  speedtest -V\n"
    )


def _build_ookla_cmd(server_id: Optional[str], fmt_variant: str = "long") -> list[str]:
    """
    Build Ookla CLI command with license acceptance flags.
    fmt_variant: 'long' uses --format=json, 'short' uses -f json.
    """
    cmd = ["speedtest", "--progress=no", "--accept-license", "--accept-gdpr"]
    if fmt_variant == "long":
        cmd += ["--format=json"]
    else:
        cmd += ["-f", "json"]
    if server_id:
        cmd += ["--server-id", str(int(server_id))]
    return cmd


def run_one_via_ookla(server_id: Optional[str] = None) -> Dict:
    """
    Use Ookla CLI with acceptance flags.  Try both format variants.
    Tag engine='ookla-cli'.
    """
    last_err: Optional[Exception] = None
    for fmt in ("long", "short"):
        cmd = _build_ookla_cmd(server_id, fmt_variant=fmt)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                last_err = RuntimeError(f"Ookla CLI returned non‑JSON output: {e}.  stdout[:200]={result.stdout[:200]}")
                continue

            dl_bps = float(data.get("download", {}).get("bandwidth", 0.0) * 8.0)  # bytes/s → bits/s
            ul_bps = float(data.get("upload", {}).get("bandwidth", 0.0) * 8.0)
            ping_ms = float(data.get("ping", {}).get("latency", 0.0))
            server = data.get("server", {}) or {}
            sid = str(server.get("id") or "")
            sname = " - ".join([p for p in [server.get("name"), server.get("location")] if p])
            sid, sname = sanitize_server_info(sid, sname)
            return {
                "timestamp": utc_now_iso(),
                "ping_ms": round(ping_ms, 3),
                "download_mbps": round(dl_bps / 1_000_000.0, 3),
                "upload_mbps": round(ul_bps / 1_000_000.0, 3),
                "server_id": sid,
                "server_name": sname,
                "engine": "ookla-cli",
            }

        # If license text still appears, surface a clear error
        lc_stderr = (result.stderr or "").lower()
        lc_stdout = (result.stdout or "").lower()
        if "license" in lc_stderr or "personal, non-commercial use" in lc_stderr or \
           "license" in lc_stdout or "personal, non-commercial use" in lc_stdout:
            raise RuntimeError(
                "Ookla CLI requires license acceptance.  This script passes --accept-license and --accept-gdpr, "
                "but your binary still exited with rc=1.  Run once manually to seed acceptance, then retry:\n"
                "  speedtest --accept-license --accept-gdpr -f json --progress=no"
            )

        last_err = RuntimeError(f"Ookla CLI failed (rc={result.returncode}): {(result.stderr or '')[:200]}")

    assert last_err is not None
    raise last_err


def run_one_via_python(server_id: Optional[str] = None) -> Dict:
    """
    Use Python speedtest-cli.  Tag engine='python-lib'.
    """
    import speedtest  # lazy import

    st = speedtest.Speedtest()
    if server_id:
        st.get_servers([int(server_id)])
        server = st.get_best_server()
    else:
        st.get_servers()
        server = st.get_best_server()

    download_bps = st.download()
    upload_bps = st.upload()
    ping_ms = float(st.results.ping)

    sid = str(server.get("id") or "")
    sname = " - ".join([p for p in [server.get("sponsor"), server.get("name")] if p])
    sid, sname = sanitize_server_info(sid, sname)

    return {
        "timestamp": utc_now_iso(),
        "ping_ms": round(ping_ms, 3),
        "download_mbps": round(download_bps / 1_000_000.0, 3),
        "upload_mbps": round(upload_bps / 1_000_000.0, 3),
        "server_id": sid,
        "server_name": sname,
        "engine": "python-lib",
    }


def run_one(server_id: Optional[str], prefer_ookla: bool, allow_python_fallback: bool) -> Dict:
    """
    Try Ookla first if requested/available.  Fall back to Python lib if allowed.
    Retried by caller on failure.
    """
    if prefer_ookla and have_ookla_cli():
        return run_one_via_ookla(server_id)

    if prefer_ookla and not have_ookla_cli():
        print_ookla_install_guidance_once()
        if not allow_python_fallback:
            raise RuntimeError("Ookla CLI is required by --require-ookla but was not found on PATH.")

    return run_one_via_python(server_id)


# ---------- Public API ----------
def list_nearby_servers(n: int = 10):
    """List nearby servers via Python lib (sufficient for discovery)."""
    try:
        import speedtest
        st = speedtest.Speedtest()
        st.get_servers()
        nearby = st.get_closest_servers()
        out = []
        for s in nearby[:max(1, n)]:
            sid, sname = sanitize_server_info(str(s.get("id")), f"{s.get('sponsor')} - {s.get('name')}")
            out.append(
                {"id": sid, "label": f"{sid}  {sname}", "country": s.get("country"), "host": s.get("host")}
            )
        return out
    except Exception as e:
        print(f"[WARN] Could not list servers: {e}")
        return []


# ---------- Main ----------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=120, help="Seconds between tests when --daemon is used.")
    parser.add_argument("--servers", type=str, help="Comma-separated Speedtest server IDs to test.")
    parser.add_argument("--list-servers", type=int, metavar="N", help="List N nearby servers and exit.")
    parser.add_argument("--daemon", action="store_true", help="Run continuously every --interval seconds.")
    parser.add_argument("--require-ookla", action="store_true", help="Fail if Ookla CLI is not installed.")
    parser.add_argument("--no-ookla", action="store_true", help="Do not use Ookla CLI even if present.")
    args = parser.parse_args()

    ensure_paths()
    ensure_csv_exists(DEFAULT_CSV)

    if args.list_servers:
        near = list_nearby_servers(args.list_servers)
        if near:
            print("\nNearby servers:")
            for s in near:
                print(f"{s['id']:>6}  {s['label']}  ({s.get('country','')})  {s.get('host','')}")
        else:
            print("No server list available.")
        return

    prefer_ookla = not args.no_ookla
    allow_python_fallback = not args.require_ookla

    if prefer_ookla and not have_ookla_cli():
        print_ookla_install_guidance_once()

    server_ids = [sid.strip() for sid in args.servers.split(",")] if args.servers else []

    def once():
        rows: List[Dict] = []
        targets = server_ids or [None]
        for sid in targets:
            delay = 2.0
            last_err: Optional[Exception] = None
            for attempt in range(4):
                try:
                    rows.append(run_one(sid, prefer_ookla=prefer_ookla, allow_python_fallback=allow_python_fallback))
                    last_err = None
                    break
                except Exception as e:
                    last_err = e
                    msg = (str(e) or "").lower()
                    if "403" in msg or "forbidden" in msg:
                        print(f"[WARN] 403/Forbidden from speedtest backend (attempt {attempt+1}/4).  Backing off {delay:.0f}s …")
                    elif "license" in msg:
                        print(f"[WARN] License acceptance needed or not persisted (attempt {attempt+1}/4).  Backing off {delay:.0f}s …")
                    else:
                        print(f"[WARN] Speedtest attempt {attempt+1}/4 failed: {e}.  Backing off {delay:.0f}s …")
                    time.sleep(delay)
                    delay *= 2
            if last_err:
                print(f"[ERROR] Giving up for this cycle for server {sid or '(best)'}: {last_err}")
                continue

        if not rows:
            return

        main_df = load_existing(DEFAULT_CSV)
        if main_df.empty:
            main_df = pd.DataFrame(columns=COLUMNS)
        for r in rows:
            append_row_inplace(main_df, r)
        main_df = prune_main(main_df)
        save_atomic(main_df, DEFAULT_CSV)

        for r in rows:
            archive_append(r)

        for r in rows:
            print(
                f"[{r['timestamp']}] ping={r['ping_ms']} ms, down={r['download_mbps']} Mbps, "
                f"up={r['upload_mps'] if 'upload_mps' in r else r['upload_mbps']} Mbps, "
                f"server={r['server_id']} {r['server_name']}, engine={r['engine']}  ->  {DEFAULT_CSV}"
            )

    if args.daemon:
        while True:
            once()
            jitter = 5 if args.interval >= 20 else 0
            time.sleep(max(5, int(args.interval)) + (int(time.time()) % (2 * jitter) - jitter))
    else:
        once()


if __name__ == "__main__":
    main()
