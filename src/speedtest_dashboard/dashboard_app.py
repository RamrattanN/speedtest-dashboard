from __future__ import annotations

import importlib.util
import subprocess
import sys

def main(argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    spec = importlib.util.find_spec("speedtest_dashboard.dashboard")
    if spec is None or spec.origin is None:
        raise RuntimeError("The dashboard module is not installed.")

    cmd = [sys.executable, "-m", "streamlit", "run", spec.origin]
    cmd.extend(argv)  # allow --server.port etc.
    subprocess.run(cmd, check=True)
