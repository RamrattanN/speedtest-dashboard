from pathlib import Path
import subprocess
import sys

import pytest

from speedtest_dashboard.app_config import (
    InstanceAlreadyRunningError,
    collection_restart_pending,
    DATA_DIR_ENV,
    MEASUREMENT_COLUMNS,
    configure_data_paths,
    consume_collection_restart,
    get_data_dir,
    instance_lock,
    load_settings,
    request_collection_restart,
    reset_measurement_history,
    save_server_calibration,
    set_measurement_engine,
    set_server_preference,
    wait_for_collection_restart,
)


def test_explicit_data_directory_has_priority(tmp_path, monkeypatch):
    monkeypatch.setenv(DATA_DIR_ENV, str(tmp_path / "environment"))
    explicit = tmp_path / "explicit"

    assert get_data_dir(explicit) == explicit.resolve()


def test_environment_data_directory_is_used(tmp_path, monkeypatch):
    configured = tmp_path / "configured"
    monkeypatch.setenv(DATA_DIR_ENV, str(configured))

    csv_path, archive_dir = configure_data_paths()

    assert csv_path == configured.resolve() / "speedtest_results.csv"
    assert archive_dir == configured.resolve() / "archive"
    assert archive_dir.is_dir()


def test_instance_lock_rejects_duplicate_role_and_releases_cleanly(tmp_path):
    with instance_lock("collector", tmp_path):
        try:
            with instance_lock("collector", tmp_path):
                raise AssertionError("duplicate collector lock unexpectedly succeeded")
        except InstanceAlreadyRunningError:
            pass

        with instance_lock("controller", tmp_path):
            pass

    with instance_lock("collector", tmp_path):
        pass


def test_instance_lock_excludes_a_second_process(tmp_path):
    script = """
import sys
import time
from speedtest_dashboard.app_config import instance_lock

with instance_lock("collector", sys.argv[1]):
    print("locked", flush=True)
    time.sleep(30)
"""
    process = subprocess.Popen(
        [sys.executable, "-c", script, str(tmp_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert process.stdout is not None
        assert process.stdout.readline().strip() == "locked"
        with pytest.raises(InstanceAlreadyRunningError):
            with instance_lock("collector", tmp_path):
                pass
    finally:
        process.terminate()
        process.wait(timeout=5)

    with instance_lock("collector", tmp_path):
        pass


def test_instance_lock_rejects_unknown_role(tmp_path):
    try:
        with instance_lock("unknown", tmp_path):
            pass
    except ValueError as exc:
        assert "Unsupported instance-lock role" in str(exc)
    else:
        raise AssertionError("unknown instance-lock role unexpectedly succeeded")


def test_reset_measurement_history_clears_csv_and_archives_but_keeps_settings(
    tmp_path,
):
    csv_path, archive_dir = configure_data_paths(tmp_path)
    csv_path.write_text(
        ",".join(MEASUREMENT_COLUMNS)
        + "\n2026-09-21T00:00:00Z,10,20,30,1,Example,ookla-cli\n",
        encoding="utf-8",
    )
    (archive_dir / "speedtest_2026-09.csv").write_text(
        csv_path.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    set_server_preference("preferred_area", "Fort Worth, TX", tmp_path)

    reset_measurement_history(tmp_path)

    assert csv_path.read_text(encoding="utf-8") == ",".join(MEASUREMENT_COLUMNS) + "\n"
    assert not list(archive_dir.glob("speedtest_*.csv"))
    assert load_settings(tmp_path)["server_selection"]["area"] == "Fort Worth, TX"
    assert consume_collection_restart(tmp_path)
    assert not consume_collection_restart(tmp_path)


def test_restart_request_wakes_collection_wait_immediately(tmp_path):
    request_collection_restart(tmp_path)

    assert collection_restart_pending(tmp_path)
    assert wait_for_collection_restart(60, tmp_path)
    assert not collection_restart_pending(tmp_path)
    assert not consume_collection_restart(tmp_path)


def test_repeated_restart_requests_coalesce(tmp_path):
    first = request_collection_restart(tmp_path)
    first_contents = first.read_text(encoding="utf-8")
    second = request_collection_restart(tmp_path)

    assert first == second
    assert collection_restart_pending(tmp_path)
    assert second.read_text(encoding="utf-8") == first_contents
    assert first_contents != ""
    assert consume_collection_restart(tmp_path)
    assert not consume_collection_restart(tmp_path)


def test_default_is_visible_folder_in_user_home(tmp_path, monkeypatch):
    monkeypatch.delenv(DATA_DIR_ENV, raising=False)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))

    assert get_data_dir() == (tmp_path / "SpeedtestDashboard").resolve()


def test_server_preferences_default_to_automatic(tmp_path):
    selection = load_settings(tmp_path)["server_selection"]

    assert selection["mode"] == "automatic"
    assert selection["server_ids"] == []


def test_measurement_engine_defaults_to_official_only(tmp_path):
    engine = load_settings(tmp_path)["measurement_engine"]

    assert engine == {"mode": "official_only", "ookla_path": ""}


def test_measurement_engine_compatibility_mode_is_explicit(tmp_path):
    set_measurement_engine(
        "compatibility",
        "/opt/tools/speedtest",
        tmp_path,
    )

    engine = load_settings(tmp_path)["measurement_engine"]
    assert engine["mode"] == "compatibility"
    assert engine["ookla_path"] == "/opt/tools/speedtest"


def test_preferred_area_save_requests_and_records_calibration(tmp_path):
    set_server_preference("preferred_area", "Austin, TX", tmp_path)

    pending = load_settings(tmp_path)["server_selection"]
    assert pending["area"] == "Austin, TX"
    assert pending["server_ids"] == []

    saved = save_server_calibration(
        "Austin, TX",
        [{"id": "123", "label": "123 - Example - Austin, TX"}],
        calibrated_at="2026-09-21T00:00:00Z",
        override=tmp_path,
    )

    assert saved
    calibrated = load_settings(tmp_path)["server_selection"]
    assert calibrated["server_ids"] == ["123"]
    assert calibrated["calibrated_at"] == "2026-09-21T00:00:00Z"


def test_stale_calibration_does_not_overwrite_new_area(tmp_path):
    set_server_preference("preferred_area", "Austin, TX", tmp_path)

    assert not save_server_calibration(
        "Dallas, TX",
        [{"id": "999", "label": "Wrong area"}],
        override=tmp_path,
    )
    assert load_settings(tmp_path)["server_selection"]["server_ids"] == []


def test_returning_to_automatic_removes_saved_regional_candidates(tmp_path):
    set_server_preference("preferred_area", "Austin, TX", tmp_path)
    save_server_calibration(
        "Austin, TX",
        [{"id": "123", "label": "123 - Example - Austin, TX"}],
        override=tmp_path,
    )

    set_server_preference("automatic", "ignored", tmp_path)

    selection = load_settings(tmp_path)["server_selection"]
    assert selection["mode"] == "automatic"
    assert selection["area"] == ""
    assert selection["server_ids"] == []
