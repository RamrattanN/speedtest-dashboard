#!/usr/bin/env python3
"""
Speedtest collector with engine tagging and an explicit production engine policy.

Features:
- Uses the official Ookla CLI by default with explicit license/GDPR acceptance flags.
- Offers the Python speedtest-cli engine only through explicit compatibility mode.
- Retries with exponential backoff on transient errors (e.g., 403) and rc=1 license prompts.
- Records UTC timestamps.
- Main CSV and monthly archives use a rolling 365-day retention boundary.
- Multi-server support (--servers "id1,id2").
- Atomic writes with retries (Dropbox/Excel/AV friendly).
- Engine column indicates 'ookla-cli' or 'python-lib'.

Usage:
  python collector.py                                  # run once (best server)
  python collector.py --daemon --interval 120          # every 2 minutes
  python collector.py --servers 20013,12345            # test specific server IDs
  python collector.py --list-servers 10                # list 10 nearby servers and exit

Optional flags:
  --require-ookla    Require the official Ookla CLI.  This is the default.
  --compatibility    Allow the Python fallback when the official CLI is unavailable.
  --no-ookla         Do not use Ookla CLI even if present.

Prereqs:
  pip install pandas speedtest-cli
  Install the official Ookla CLI from https://www.speedtest.net/apps/cli.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import ssl
import subprocess
import sys
import tempfile
import time
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Tuple

import certifi
import pandas as pd

from speedtest_dashboard.app_config import (
    InstanceAlreadyRunningError,
    MEASUREMENT_COLUMNS,
    configure_data_paths,
    load_settings,
    instance_lock,
    measurement_data_lock,
    save_collector_status,
    save_server_calibration,
    wait_for_collection_restart,
)

# ---------- Paths / Config ----------
DEFAULT_CSV, ARCHIVE_DIR = configure_data_paths()

COLUMNS = MEASUREMENT_COLUMNS
MAIN_RETENTION_DAYS = 365
NETWORK_TIMEOUT_SECONDS = 15
MAX_PING_MS = 60_000.0
MAX_AREA_CANDIDATES = 25
OOKLA_PATH_ENV = "SPEEDTEST_OOKLA_CLI"
OOKLA_DOWNLOAD_URL = "https://www.speedtest.net/apps/cli"

# One-time info flag
_ookla_guidance_printed = False


# ---------- Filesystem helpers ----------
def ensure_paths() -> None:
    DEFAULT_CSV.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


def ensure_csv_exists(path: Path) -> None:
    if not path.exists():
        pd.DataFrame(columns=COLUMNS).to_csv(path, index=False)


def configure_ssl_certificate_bundle() -> Path | None:
    """Use certifi when Python has no usable default CA file.

    Respect an explicit ``SSL_CERT_FILE`` value so managed or corporate
    environments can provide their own certificate bundle.
    """
    explicit_bundle = os.environ.get("SSL_CERT_FILE")
    if explicit_bundle:
        return Path(explicit_bundle)

    default_bundle = ssl.get_default_verify_paths().cafile
    if default_bundle and Path(default_bundle).is_file():
        return Path(default_bundle)

    certifi_bundle = Path(certifi.where())
    if certifi_bundle.is_file():
        os.environ["SSL_CERT_FILE"] = str(certifi_bundle)
        return certifi_bundle

    return None


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
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=MAIN_RETENTION_DAYS)
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
    retained = prune_main(df)
    if retained.empty:
        path.unlink(missing_ok=True)
    else:
        save_atomic(retained, path)

    for archive in ARCHIVE_DIR.glob("speedtest_*.csv"):
        if archive == path:
            continue
        try:
            existing = load_existing(archive)
            retained = prune_main(existing)
            if retained.empty:
                archive.unlink(missing_ok=True)
            elif len(retained) != len(existing):
                save_atomic(retained, archive)
        except OSError:
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


def validate_measurement(row: Dict) -> Dict:
    """Reject corrupt or impossible measurements before they reach history."""

    values = {
        "ping_ms": float(row.get("ping_ms", math.nan)),
        "download_mbps": float(row.get("download_mbps", math.nan)),
        "upload_mbps": float(row.get("upload_mbps", math.nan)),
    }
    invalid = [
        name
        for name, value in values.items()
        if not math.isfinite(value) or value < 0
    ]
    if values["ping_ms"] > MAX_PING_MS:
        invalid.append("ping_ms")
    if invalid:
        fields = ", ".join(sorted(set(invalid)))
        raise RuntimeError(f"Speedtest returned an invalid measurement ({fields}).")
    return row


# ---------- Ookla CLI vs Python library ----------
def _ookla_candidates(configured_path: str = "") -> list[Path]:
    """Return platform-appropriate CLI candidates in priority order."""

    candidates: list[Path] = []
    for value in (configured_path, os.environ.get(OOKLA_PATH_ENV, "")):
        if value:
            candidates.append(Path(value).expanduser())

    discovered = shutil.which("speedtest")
    if discovered:
        candidates.append(Path(discovered))

    if os.name == "nt":
        for variable in ("LOCALAPPDATA", "ProgramFiles", "ProgramFiles(x86)"):
            root = os.environ.get(variable)
            if root:
                candidates.extend(
                    [
                        Path(root) / "Ookla Speedtest CLI" / "speedtest.exe",
                        Path(root) / "Speedtest CLI" / "speedtest.exe",
                        Path(root) / "Ookla" / "speedtest.exe",
                    ]
                )
        candidates.append(Path.home() / "Tools" / "OoklaSpeedtest" / "speedtest.exe")
    else:
        candidates.extend(
            [
                Path("/usr/local/bin/speedtest"),
                Path("/opt/homebrew/bin/speedtest"),
                Path.home() / ".local" / "bin" / "speedtest",
                Path.home() / "bin" / "speedtest",
            ]
        )

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        normalized = str(candidate)
        if normalized not in seen:
            seen.add(normalized)
            unique.append(candidate)
    return unique


def is_official_ookla_cli(path: Path) -> bool:
    """Reject the similarly named Python command and accept only Ookla's CLI."""

    if not path.is_file():
        return False
    try:
        result = subprocess.run(
            [str(path), "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    output = f"{result.stdout}\n{result.stderr}".casefold()
    return result.returncode == 0 and "ookla" in output and "speedtest" in output


def find_ookla_cli(configured_path: str = "") -> Path | None:
    """Locate and verify the official CLI without relying only on GUI-app PATH."""

    for candidate in _ookla_candidates(configured_path):
        if is_official_ookla_cli(candidate):
            return candidate.resolve()
    return None


def configured_ookla_cli(data_dir: Path | None = None) -> Path | None:
    """Resolve the official CLI using the current per-user settings."""

    configured_path = load_settings(data_dir)["measurement_engine"]["ookla_path"]
    return find_ookla_cli(configured_path)


def have_ookla_cli(configured_path: str = "") -> bool:
    return find_ookla_cli(configured_path) is not None


def print_ookla_install_guidance_once() -> None:
    global _ookla_guidance_printed
    if _ookla_guidance_printed:
        return
    _ookla_guidance_printed = True
    print(
        "\n[ATTENTION] The official Ookla Speedtest CLI was not found.\n"
        "            Production measurements are paused to avoid mixing incompatible engines.\n"
        f"            Download it from {OOKLA_DOWNLOAD_URL}, or select Compatibility mode in the dashboard.\n"
    )


def _build_ookla_cmd(
    server_id: Optional[str],
    fmt_variant: str = "long",
    executable: str = "speedtest",
) -> list[str]:
    """
    Build Ookla CLI command with license acceptance flags.
    fmt_variant: 'long' uses --format=json, 'short' uses -f json.
    """
    cmd = [executable, "--progress=no", "--accept-license", "--accept-gdpr"]
    if fmt_variant == "long":
        cmd += ["--format=json"]
    else:
        cmd += ["-f", "json"]
    if server_id:
        cmd += ["--server-id", str(int(server_id))]
    return cmd


def run_one_via_ookla(
    server_id: Optional[str] = None,
    executable: Path | str | None = None,
) -> Dict:
    """
    Use Ookla CLI with acceptance flags.  Try both format variants.
    Tag engine='ookla-cli'.
    """
    last_err: Optional[Exception] = None
    for fmt in ("long", "short"):
        cli = str(executable or find_ookla_cli() or "speedtest")
        cmd = _build_ookla_cmd(server_id, fmt_variant=fmt, executable=cli)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                last_err = RuntimeError(f"Ookla CLI returned non-JSON output: {e}.  stdout[:200]={result.stdout[:200]}")
                continue

            dl_bps = float(data.get("download", {}).get("bandwidth", 0.0) * 8.0)  # bytes/s to bits/s
            ul_bps = float(data.get("upload", {}).get("bandwidth", 0.0) * 8.0)
            ping_ms = float(data.get("ping", {}).get("latency", 0.0))
            server = data.get("server", {}) or {}
            sid = str(server.get("id") or "")
            sname = " - ".join([p for p in [server.get("name"), server.get("location")] if p])
            sid, sname = sanitize_server_info(sid, sname)
            return validate_measurement({
                "timestamp": utc_now_iso(),
                "ping_ms": round(ping_ms, 3),
                "download_mbps": round(dl_bps / 1_000_000.0, 3),
                "upload_mbps": round(ul_bps / 1_000_000.0, 3),
                "server_id": sid,
                "server_name": sname,
                "engine": "ookla-cli",
            })

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


def _new_python_speedtest():
    """Create the fallback client with bounded individual network requests."""

    configure_ssl_certificate_bundle()
    import speedtest  # lazy import

    return speedtest.Speedtest(timeout=NETWORK_TIMEOUT_SECONDS)


def run_one_via_python(server_id: Optional[str] = None) -> Dict:
    """
    Use Python speedtest-cli.  Tag engine='python-lib'.
    """
    st = _new_python_speedtest()
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

    return validate_measurement({
        "timestamp": utc_now_iso(),
        "ping_ms": round(ping_ms, 3),
        "download_mbps": round(download_bps / 1_000_000.0, 3),
        "upload_mbps": round(upload_bps / 1_000_000.0, 3),
        "server_id": sid,
        "server_name": sname,
        "engine": "python-lib",
    })


def run_one(
    server_id: Optional[str],
    prefer_ookla: bool,
    allow_python_fallback: bool,
    configured_path: str = "",
) -> Dict:
    """
    Try Ookla first if requested/available.  Fall back to Python lib if allowed.
    Retried by caller on failure.
    """
    if prefer_ookla:
        executable = find_ookla_cli(configured_path)
        if executable:
            try:
                return run_one_via_ookla(server_id, executable)
            except Exception as exc:
                if not allow_python_fallback:
                    raise
                print(f"[WARN] Ookla CLI failed: {exc}.  Compatibility mode is using the Python engine.")
        else:
            print_ookla_install_guidance_once()
            if not allow_python_fallback:
                raise RuntimeError(
                    "Official Ookla CLI required but not found.  Install it from "
                    f"{OOKLA_DOWNLOAD_URL} or configure its executable path in the dashboard."
                )

    return run_one_via_python(server_id)


# ---------- Public API ----------
def list_nearby_servers(n: int = 10):
    """List nearby servers via Python lib (sufficient for discovery)."""
    try:
        st = _new_python_speedtest()
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


def _area_terms(area: str) -> list[str]:
    """Return normalized city/region terms used to match server metadata."""

    return [term for term in re.findall(r"[a-z0-9]+", area.casefold()) if len(term) > 1]


def calibrate_preferred_area(area: str) -> list[dict[str, str]]:
    """Find and latency-rank servers whose metadata matches a city or region."""

    terms = _area_terms(area)
    if not terms:
        raise ValueError("Enter a city and state, province, or country.")

    st = _new_python_speedtest()
    grouped = st.get_servers()
    candidates = []
    for distance in sorted(grouped):
        for server in grouped[distance]:
            searchable = " ".join(
                str(server.get(key) or "")
                for key in ("name", "sponsor", "country", "cc")
            ).casefold()
            if all(term in searchable for term in terms):
                candidates.append(server)

    if not candidates:
        raise RuntimeError(f"No Speedtest servers matched '{area}'.")

    candidates = candidates[:MAX_AREA_CANDIDATES]
    best = st.get_best_server(candidates)
    ordered = [best, *[server for server in candidates if str(server.get("id")) != str(best.get("id"))]]
    calibrated = []
    for server in ordered:
        sid, name = sanitize_server_info(
            str(server.get("id") or ""),
            " - ".join(part for part in [server.get("sponsor"), server.get("name")] if part),
        )
        if sid:
            calibrated.append({"id": sid, "label": f"{sid} - {name}"})
    return calibrated


def preferred_targets(data_dir: Path) -> tuple[list[Optional[str]], bool]:
    """Return saved regional failover targets, calibrating when necessary."""

    selection = load_settings(data_dir)["server_selection"]
    if selection["mode"] != "preferred_area" or not selection["area"]:
        return [None], False

    area = selection["area"]
    server_ids = selection["server_ids"]
    if not server_ids:
        print(f"[INFO] Calibrating Speedtest servers for preferred area: {area}", flush=True)
        try:
            servers = calibrate_preferred_area(area)
        except Exception as exc:
            message = str(exc) or type(exc).__name__
            save_server_calibration(area, [], error=message, override=data_dir)
            print(f"[WARN] Preferred-area calibration failed: {message}.  Using automatic selection this cycle.", flush=True)
            return [None], False
        save_server_calibration(
            area,
            servers,
            calibrated_at=utc_now_iso(),
            override=data_dir,
        )
        server_ids = [server["id"] for server in servers]
        print(f"[INFO] Preferred area calibrated with {len(server_ids)} regional server candidates.", flush=True)

    return [*server_ids, None], True


# ---------- Main ----------
def main(argv: list[str] | None = None) -> bool:
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=120, help="Seconds between tests when --daemon is used.")
    parser.add_argument("--servers", type=str, help="Comma-separated Speedtest server IDs to test.")
    parser.add_argument("--list-servers", type=int, metavar="N", help="List N nearby servers and exit.")
    parser.add_argument("--daemon", action="store_true", help="Run continuously every --interval seconds.")
    engine_group = parser.add_mutually_exclusive_group()
    engine_group.add_argument(
        "--require-ookla",
        action="store_true",
        help="Require the official Ookla CLI.  This is the default.",
    )
    engine_group.add_argument(
        "--compatibility",
        action="store_true",
        help="Allow the Python engine when the official Ookla CLI is unavailable.",
    )
    engine_group.add_argument(
        "--no-ookla",
        action="store_true",
        help="Developer option: use only the Python compatibility engine.",
    )
    parser.add_argument(
        "--data-dir",
        help="Folder for speedtest_results.csv and monthly archives. "
        "Defaults to SPEEDTEST_DASHBOARD_DATA_DIR or ~/SpeedtestDashboard.",
    )
    args = parser.parse_args(argv)

    global DEFAULT_CSV, ARCHIVE_DIR
    DEFAULT_CSV, ARCHIVE_DIR = configure_data_paths(args.data_dir)

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
        return bool(near)

    cli_engine_override = None
    if args.no_ookla:
        cli_engine_override = "python_only"
    elif args.compatibility:
        cli_engine_override = "compatibility"
    elif args.require_ookla:
        cli_engine_override = "official_only"

    server_ids = [sid.strip() for sid in args.servers.split(",")] if args.servers else []

    def once() -> bool:
        engine_settings = load_settings(DEFAULT_CSV.parent)["measurement_engine"]
        engine_mode = cli_engine_override or engine_settings["mode"]
        prefer_ookla = engine_mode != "python_only"
        allow_python_fallback = engine_mode in {"compatibility", "python_only"}
        configured_path = engine_settings["ookla_path"]
        resolved_cli = find_ookla_cli(configured_path) if prefer_ookla else None
        if prefer_ookla and not resolved_cli:
            print_ookla_install_guidance_once()
            if not allow_python_fallback:
                save_collector_status(
                    "setup_required",
                    "Install or configure the official Ookla CLI to start production measurements.",
                    utc_now_iso(),
                    DEFAULT_CSV.parent,
                )
                return False
        if resolved_cli or allow_python_fallback:
            save_collector_status(
                "testing",
                (
                    "Running a connection test with the official Ookla CLI."
                    if resolved_cli
                    else "Running a connection test in explicit compatibility mode."
                ),
                utc_now_iso(),
                DEFAULT_CSV.parent,
            )

        rows: List[Dict] = []
        preferred_failover = False
        if server_ids:
            targets: list[Optional[str]] = server_ids
        else:
            targets, preferred_failover = preferred_targets(DEFAULT_CSV.parent)
        for sid in targets:
            delay = 2.0
            last_err: Optional[Exception] = None
            attempt_limit = 1 if preferred_failover and sid else 4
            for attempt in range(attempt_limit):
                try:
                    result = run_one(
                        sid,
                        prefer_ookla=prefer_ookla,
                        allow_python_fallback=allow_python_fallback,
                        configured_path=configured_path,
                    )
                    if preferred_failover and sid is None:
                        result["server_name"] = (
                            f"Automatic fallback - {result['server_name']}"
                        ).rstrip(" -")
                    rows.append(result)
                    last_err = None
                    break
                except Exception as e:
                    last_err = e
                    msg = (str(e) or "").lower()
                    retry_note = (
                        f"  Backing off {delay:.0f}s before retry."
                        if attempt + 1 < attempt_limit
                        else ""
                    )
                    if "403" in msg or "forbidden" in msg:
                        print(f"[WARN] 403/Forbidden from speedtest backend (attempt {attempt+1}/{attempt_limit}).{retry_note}")
                    elif "license" in msg:
                        print(f"[WARN] License acceptance needed or not persisted (attempt {attempt+1}/{attempt_limit}).{retry_note}")
                    else:
                        print(f"[WARN] Speedtest attempt {attempt+1}/{attempt_limit} failed: {e}.{retry_note}")
                    if attempt + 1 < attempt_limit:
                        time.sleep(delay)
                    delay *= 2
            if last_err:
                print(f"[ERROR] Giving up for this cycle for server {sid or '(best)'}: {last_err}")
                continue
            if preferred_failover and rows:
                break

        if not rows:
            if not (prefer_ookla and not resolved_cli and not allow_python_fallback):
                save_collector_status(
                    "error",
                    "The measurement failed.  The monitor will retry on the next cycle.",
                    utc_now_iso(),
                    DEFAULT_CSV.parent,
                )
            return False

        with measurement_data_lock(DEFAULT_CSV.parent):
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
        save_collector_status(
            "healthy",
            f"Last measurement completed with {rows[-1]['engine']}.",
            rows[-1]["timestamp"],
            DEFAULT_CSV.parent,
        )
        return True

    def run_daemon() -> bool:
        while True:
            once()
            jitter = 5 if args.interval >= 20 else 0
            jitter_offset = (
                int(time.time()) % (2 * jitter) - jitter if jitter else 0
            )
            wait_seconds = max(5, int(args.interval)) + jitter_offset
            if wait_for_collection_restart(wait_seconds, DEFAULT_CSV.parent):
                print(
                    "[INFO] One-shot measurement request acknowledged.  "
                    "Starting one measurement cycle.",
                    flush=True,
                )

    if args.daemon:
        try:
            with instance_lock("collector", DEFAULT_CSV.parent):
                return run_daemon()
        except InstanceAlreadyRunningError as exc:
            print(f"[INFO] {exc}  This collector will not start.", flush=True)
            return False

    return once()


if __name__ == "__main__":
    main()
