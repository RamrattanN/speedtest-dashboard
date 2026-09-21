"""Shared filesystem configuration for the collector and dashboard."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any


DATA_DIR_ENV = "SPEEDTEST_DASHBOARD_DATA_DIR"
SETTINGS_FILENAME = "settings.json"
STATUS_FILENAME = "collector_status.json"
RESTART_REQUEST_FILENAME = "restart_collection.request"
DATA_LOCK_FILENAME = ".measurement_data.lock"
MEASUREMENT_COLUMNS = [
    "timestamp",
    "ping_ms",
    "download_mbps",
    "upload_mbps",
    "server_id",
    "server_name",
    "engine",
]
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


def restart_request_path(override: str | Path | None = None) -> Path:
    """Return the cross-process request used to start a fresh collection cycle."""

    return get_data_dir(override) / RESTART_REQUEST_FILENAME


@contextmanager
def measurement_data_lock(
    override: str | Path | None = None,
    *,
    timeout: float = 15.0,
):
    """Serialize short CSV and archive mutations across dashboard and collector."""

    lock_path = get_data_dir(override) / DATA_LOCK_FILENAME
    deadline = time.monotonic() + timeout
    descriptor: int | None = None
    while descriptor is None:
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(descriptor, str(os.getpid()).encode("ascii", errors="ignore"))
        except FileExistsError:
            try:
                stale = time.time() - lock_path.stat().st_mtime > 600
            except OSError:
                stale = False
            if stale:
                try:
                    lock_path.unlink()
                except OSError:
                    pass
                continue
            if time.monotonic() >= deadline:
                raise TimeoutError("Timed out waiting to update measurement data.")
            time.sleep(0.1)
    try:
        yield
    finally:
        try:
            os.close(descriptor)
        finally:
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass


def request_collection_restart(override: str | Path | None = None) -> Path:
    """Request one immediate collector cycle after any current work completes.

    Repeated requests coalesce into the same file, so the dashboard cannot
    queue multiple overlapping measurements.
    """

    path = restart_request_path(override)
    path.write_text(
        datetime.now(timezone.utc).isoformat().replace("+00:00", "Z") + "\n",
        encoding="utf-8",
    )
    return path


def collection_restart_pending(override: str | Path | None = None) -> bool:
    """Return whether an immediate collector cycle is already queued."""

    return restart_request_path(override).is_file()


def consume_collection_restart(override: str | Path | None = None) -> bool:
    """Consume and acknowledge a pending collection restart request."""

    path = restart_request_path(override)
    try:
        path.unlink()
    except FileNotFoundError:
        return False
    return True


def wait_for_collection_restart(
    timeout: float,
    override: str | Path | None = None,
    *,
    stop_event: Any = None,
) -> bool:
    """Wait for a restart request, returning early when one is received."""

    deadline = time.monotonic() + max(0.0, timeout)
    while True:
        if consume_collection_restart(override):
            return True
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False
        pause = min(1.0, remaining)
        if stop_event is not None:
            if stop_event.wait(pause):
                return False
        else:
            time.sleep(pause)


def reset_measurement_history(override: str | Path | None = None) -> Path:
    """Delete recorded measurements while preserving application settings."""

    csv_path, archive_dir = configure_data_paths(override)
    with measurement_data_lock(csv_path.parent):
        with tempfile.NamedTemporaryFile(
            delete=False,
            dir=csv_path.parent,
            prefix="speedtest_results_",
            suffix=".tmp",
            mode="w",
            encoding="utf-8",
            newline="",
        ) as handle:
            handle.write(",".join(MEASUREMENT_COLUMNS) + "\n")
            temporary = Path(handle.name)
        os.replace(temporary, csv_path)
        for archive in archive_dir.glob("speedtest_*.csv"):
            archive.unlink(missing_ok=True)

    request_collection_restart(csv_path.parent)
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    save_collector_status(
        "starting",
        "Measurement history reset.  Starting a fresh collection cycle...",
        now,
        csv_path.parent,
    )
    return csv_path


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
