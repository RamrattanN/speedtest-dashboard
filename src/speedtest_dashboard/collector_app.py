from __future__ import annotations
import runpy
import pathlib
import sys

def main(argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    # Try to find collector.py at the project root inside the wheel/sdist
    root = pathlib.Path(__file__).resolve().parents[2]
    candidate = root / "collector.py"
    if not candidate.exists():
        # fallback if you later move the file under the package
        alt = pathlib.Path(__file__).resolve().parent / "collector.py"
        if alt.exists():
            candidate = alt

    sys.argv = ["collector.py"] + argv
    runpy.run_path(str(candidate), run_name="__main__")
