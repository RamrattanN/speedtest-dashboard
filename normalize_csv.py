#!/usr/bin/env python3
"""
Normalize Speedtest CSVs so server filters work correctly.

What it does:
- Forces server_id to string, strips whitespace, removes a trailing '.0'
- Replaces 'nan'/'NaN'/'None'/NaN with '' (empty) for server_id and server_name
- Strips whitespace on server_name
- Writes back atomically after creating a timestamped backup

Usage:
  python normalize_csv.py --path "C:\\Users\\niles\\Dropbox\\Python Code\\Speedtest\\speedtest_results.csv"
  # Optional: also normalize monthly archives in the 'archive' folder
  python normalize_csv.py --path "C:\\Users\\niles\\Dropbox\\Python Code\\Speedtest\\speedtest_results.csv" --archives
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd


COLUMNS = ["timestamp", "ping_ms", "download_mbps", "upload_mbps", "server_id", "server_name"]


def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure expected columns exist
    for c in COLUMNS:
        if c not in df.columns:
            df[c] = pd.NA

    # server_id: to string, drop NaN/None/nan, strip, remove trailing ".0"
    sid = df["server_id"].astype(str)
    sid = sid.replace(to_replace=r"^(nan|NaN|None)$", value="", regex=True)
    sid = sid.str.strip()
    sid = sid.str.replace(r"\.0$", "", regex=True)
    df["server_id"] = sid

    # server_name: to string, drop NaN/None/nan, strip
    sname = df["server_name"].astype(str)
    sname = sname.replace(to_replace=r"^(nan|NaN|None)$", value="", regex=True)
    sname = sname.str.strip()
    df["server_name"] = sname

    return df[COLUMNS]


def atomic_write_csv(df: pd.DataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        delete=False, dir=out_path.parent, prefix=out_path.stem + "_", suffix=".tmp", mode="w", newline="", encoding="utf-8"
    ) as f:
        df.to_csv(f, index=False)
        tmp = Path(f.name)
    tmp.replace(out_path)


def backup_path(path: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return path.with_name(path.stem + f"_backup_{ts}" + path.suffix)


def normalize_file(csv_path: Path) -> None:
    if not csv_path.exists():
        print(f"[WARN] File not found: {csv_path}")
        return
    # Read as strings to preserve values exactly
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=True)
    df = normalize_df(df)
    # Backup and write
    bkp = backup_path(csv_path)
    shutil.copy2(csv_path, bkp)
    atomic_write_csv(df, csv_path)
    print(f"[OK] Normalized: {csv_path}\n     Backup:     {bkp}")


def normalize_archives(main_csv: Path) -> None:
    arch_dir = main_csv.parent / "archive"
    if not arch_dir.exists():
        print(f"[INFO] Archive folder not found: {arch_dir}")
        return
    files = sorted(arch_dir.glob("speedtest_*.csv"))
    if not files:
        print(f"[INFO] No archive files in: {arch_dir}")
        return
    for f in files:
        try:
            normalize_file(f)
        except Exception as e:
            print(f"[ERROR] Failed to normalize {f}: {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True, help="Path to speedtest_results.csv")
    ap.add_argument("--archives", action="store_true", help="Also normalize monthly archive CSVs")
    args = ap.parse_args()

    csv_path = Path(args.path)
    normalize_file(csv_path)
    if args.archives:
        normalize_archives(csv_path)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
