from __future__ import annotations
import pathlib
import subprocess
import sys

def main(argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    root = pathlib.Path(__file__).resolve().parents[2]
    app = root / "dashboard.py"
    if not app.exists():
        alt = pathlib.Path(__file__).resolve().parent / "dashboard.py"
        if alt.exists():
            app = alt

    cmd = [sys.executable, "-m", "streamlit", "run", str(app)]
    cmd.extend(argv)  # allow --server.port etc.
    subprocess.run(cmd, check=True)
