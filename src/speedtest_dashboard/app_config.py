"""Shared filesystem configuration for the collector and dashboard."""

from __future__ import annotations

import os
from pathlib import Path


DATA_DIR_ENV = "SPEEDTEST_DASHBOARD_DATA_DIR"


def get_data_dir(override: str | Path | None = None) -> Path:
    """Return the data directory, creating it when necessary.

    Priority is an explicit override, then ``SPEEDTEST_DASHBOARD_DATA_DIR``,
    then a visible folder in the current user's home directory.
    """

    configured = override or os.environ.get(DATA_DIR_ENV)
    path = Path(configured).expanduser() if configured else Path.home() / "SpeedtestDashboard"
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def configure_data_paths(override: str | Path | None = None) -> tuple[Path, Path]:
    """Return the primary CSV path and monthly archive directory."""

    data_dir = get_data_dir(override)
    archive_dir = data_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "speedtest_results.csv", archive_dir
