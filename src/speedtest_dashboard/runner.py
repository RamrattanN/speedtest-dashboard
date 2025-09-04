from __future__ import annotations
import argparse
import subprocess
import sys
import time
import pathlib

def main() -> None:
    p = argparse.ArgumentParser(prog="speedtest-dashboard", description="Launch collector + dashboard")
    p.add_argument("--interval", type=int, default=120, help="Collector interval in seconds (default 120)")
    p.add_argument("--port", type=int, default=8501, help="Dashboard port (default 8501)")
    p.add_argument("--headless", action="store_true", help="Do not open browser automatically")
    args, unknown = p.parse_known_args()

    root = pathlib.Path(__file__).resolve().parents[2]
    collector = root / "collector.py"
    dashboard = root / "dashboard.py"

    col_cmd = [sys.executable, str(collector), "--daemon", "--interval", str(args.interval)]
    col_proc = subprocess.Popen(col_cmd)

    dash_cmd = [sys.executable, "-m", "streamlit", "run", str(dashboard), "--server.port", str(args.port)]
    if args.headless:
        dash_cmd += ["--browser.gatherUsageStats", "false", "--server.headless", "true"]
    dash_cmd += unknown

    try:
        subprocess.run(dash_cmd, check=True)
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
