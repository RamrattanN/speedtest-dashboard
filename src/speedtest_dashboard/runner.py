from __future__ import annotations
import argparse
import importlib.util
import os
import subprocess
import sys
import time

from .app_config import DATA_DIR_ENV, get_data_dir

def main() -> None:
    p = argparse.ArgumentParser(prog="speedtest-dashboard", description="Launch collector + dashboard")
    p.add_argument("--interval", type=int, default=120, help="Collector interval in seconds (default 120)")
    p.add_argument("--port", type=int, default=8501, help="Dashboard port (default 8501)")
    p.add_argument("--headless", action="store_true", help="Do not open browser automatically")
    p.add_argument(
        "--data-dir",
        help="Folder for results and archives (default: ~/SpeedtestDashboard)",
    )
    args, unknown = p.parse_known_args()

    dashboard_spec = importlib.util.find_spec("speedtest_dashboard.dashboard")
    if dashboard_spec is None or dashboard_spec.origin is None:
        raise RuntimeError("The dashboard module is not installed.")

    data_dir = get_data_dir(args.data_dir)
    child_env = os.environ.copy()
    child_env[DATA_DIR_ENV] = str(data_dir)

    col_cmd = [
        sys.executable,
        "-m",
        "speedtest_dashboard.collector",
        "--daemon",
        "--interval",
        str(args.interval),
        "--data-dir",
        str(data_dir),
    ]
    col_proc = subprocess.Popen(col_cmd, env=child_env)

    dash_cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        dashboard_spec.origin,
        "--server.port",
        str(args.port),
    ]
    if args.headless:
        dash_cmd += ["--browser.gatherUsageStats", "false", "--server.headless", "true"]
    dash_cmd += unknown

    try:
        subprocess.run(dash_cmd, check=True, env=child_env)
    finally:
        try:
            col_proc.terminate()
            for _ in range(10):
                if col_proc.poll() is not None:
                    break
                time.sleep(0.2)
        except Exception:
            pass

if __name__ == "__main__":
    main()
