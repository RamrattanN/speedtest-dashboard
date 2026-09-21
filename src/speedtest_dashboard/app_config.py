"""Shared filesystem configuration for the collector and dashboard."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


DATA_DIR_ENV = "SPEEDTEST_DASHBOARD_DATA_DIR"
SETTINGS_FILENAME = "settings.json"
STATUS_FILENAME = "collector_status.json"
DEFAULT_SETTINGS: dict[str, Any] = {
    "measurement_engine": {
        "mode": "official_only",
        "ookla_path": "",
    },
    "server_selection": {
        "mode": "automatic",
        "area": "",
        "server_ids": [],
        "server_labels": [],
        "calibrated_at": "",
        "last_error": "",
    }
}


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


def settings_path(override: str | Path | None = None) -> Path:
    """Return the per-user settings file for the selected data directory."""

    return get_data_dir(override) / SETTINGS_FILENAME


def collector_status_path(override: str | Path | None = None) -> Path:
    """Return the collector health file beside the measurement CSV."""

    return get_data_dir(override) / STATUS_FILENAME


def load_collector_status(override: str | Path | None = None) -> dict[str, str]:
    """Load the latest collector state without failing the controller or dashboard."""

    try:
        raw = json.loads(collector_status_path(override).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError):
        raw = {}
    return {
        "state": str(raw.get("state") or "starting"),
        "message": str(raw.get("message") or "Starting the measurement service..."),
        "updated_at": str(raw.get("updated_at") or ""),
    }


def save_collector_status(
    state: str,
    message: str,
    updated_at: str,
    override: str | Path | None = None,
) -> Path:
    """Atomically publish collector health for the native controllers and dashboard."""

    path = collector_status_path(override)
    with tempfile.NamedTemporaryFile(
        delete=False,
        dir=path.parent,
        prefix="collector_status_",
        suffix=".tmp",
        mode="w",
        encoding="utf-8",
    ) as handle:
        json.dump(
            {"state": state, "message": message, "updated_at": updated_at},
            handle,
            indent=2,
            sort_keys=True,
        )
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)
    return path


def load_settings(override: str | Path | None = None) -> dict[str, Any]:
    """Load settings while tolerating missing or partially written files."""

    path = settings_path(override)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError):
        raw = {}

    raw_engine = raw.get("measurement_engine", {})
    if not isinstance(raw_engine, dict):
        raw_engine = {}
    default_engine = DEFAULT_SETTINGS["measurement_engine"]
    engine = {key: raw_engine.get(key, value) for key, value in default_engine.items()}
    if engine["mode"] not in {"official_only", "compatibility"}:
        engine["mode"] = "official_only"
    engine["ookla_path"] = str(engine["ookla_path"] or "").strip().strip('"')

    raw_selection = raw.get("server_selection", {})
    if not isinstance(raw_selection, dict):
        raw_selection = {}
    default_selection = DEFAULT_SETTINGS["server_selection"]
    selection = {
        key: raw_selection.get(key, value) for key, value in default_selection.items()
    }
    if selection["mode"] not in {"automatic", "preferred_area"}:
        selection["mode"] = "automatic"
    for key in ("server_ids", "server_labels"):
        value = selection[key]
        selection[key] = (
            [str(item).strip() for item in value if str(item).strip()]
            if isinstance(value, list)
            else []
        )
    for key in ("area", "calibrated_at", "last_error"):
        selection[key] = str(selection[key] or "").strip()

    return {
        **raw,
        "measurement_engine": engine,
        "server_selection": selection,
    }


def save_settings(settings: dict[str, Any], override: str | Path | None = None) -> Path:
    """Atomically save per-user settings."""

    path = settings_path(override)
    with tempfile.NamedTemporaryFile(
        delete=False,
        dir=path.parent,
        prefix="settings_",
        suffix=".tmp",
        mode="w",
        encoding="utf-8",
    ) as handle:
        json.dump(settings, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)
    return path


def set_server_preference(
    mode: str,
    area: str,
    override: str | Path | None = None,
) -> dict[str, Any]:
    """Save a location-neutral server choice and request recalibration."""

    normalized_mode = (
        mode if mode in {"automatic", "preferred_area"} else "automatic"
    )
    normalized_area = area.strip() if normalized_mode == "preferred_area" else ""
    settings = load_settings(override)
    current = settings["server_selection"]
    current.update({"mode": normalized_mode, "area": normalized_area, "last_error": ""})
    current.update({"server_ids": [], "server_labels": [], "calibrated_at": ""})
    save_settings(settings, override)
    return settings


def set_measurement_engine(
    mode: str,
    ookla_path: str = "",
    override: str | Path | None = None,
) -> dict[str, Any]:
    """Save the production engine policy and an optional explicit CLI path."""

    normalized_mode = mode if mode in {"official_only", "compatibility"} else "official_only"
    settings = load_settings(override)
    settings["measurement_engine"] = {
        "mode": normalized_mode,
        "ookla_path": ookla_path.strip().strip('"'),
    }
    save_settings(settings, override)
    return settings


def save_server_calibration(
    area: str,
    servers: list[dict[str, str]],
    *,
    error: str = "",
    calibrated_at: str = "",
    override: str | Path | None = None,
) -> bool:
    """Save calibration only when the user has not changed the requested area."""

    settings = load_settings(override)
    selection = settings["server_selection"]
    if (
        selection["mode"] != "preferred_area"
        or selection["area"].casefold() != area.strip().casefold()
    ):
        return False
    selection["server_ids"] = [server["id"] for server in servers if server.get("id")]
    selection["server_labels"] = [server["label"] for server in servers if server.get("id")]
    selection["calibrated_at"] = calibrated_at
    selection["last_error"] = error
    save_settings(settings, override)
    return True
