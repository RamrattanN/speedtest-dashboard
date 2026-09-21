from __future__ import annotations

import sys

from .collector import main as collector_main

def main(argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]
    if not collector_main(argv):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
