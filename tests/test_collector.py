from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pandas as pd

from speedtest_dashboard import collector


def _row(timestamp: datetime) -> dict:
    return {
        "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
        "ping_ms": 10.0,
        "download_mbps": 100.0,
        "upload_mbps": 20.0,
        "server_id": "123.0",
        "server_name": "Example",
        "engine": "test",
    }


def test_sanitize_server_information():
    assert collector.sanitize_server_info("123.0", " Example ") == ("123", "Example")
    assert collector.sanitize_server_info("nan", "None") == ("", "")


def test_ensure_paths_creates_configured_data_directories(tmp_path, monkeypatch):
    csv_path = tmp_path / "configured" / "speedtest_results.csv"
    archive_dir = csv_path.parent / "archive"
    monkeypatch.setattr(collector, "DEFAULT_CSV", csv_path)
    monkeypatch.setattr(collector, "ARCHIVE_DIR", archive_dir)

    collector.ensure_paths()

    assert csv_path.parent.is_dir()
    assert archive_dir.is_dir()


def test_configure_ssl_certificate_bundle_uses_certifi_when_default_is_missing(tmp_path, monkeypatch):
    certifi_bundle = tmp_path / "cacert.pem"
    certifi_bundle.write_text("test certificate bundle", encoding="utf-8")
    monkeypatch.delenv("SSL_CERT_FILE", raising=False)
    monkeypatch.setattr(
        collector.ssl,
        "get_default_verify_paths",
        lambda: SimpleNamespace(cafile=None),
    )
    monkeypatch.setattr(collector.certifi, "where", lambda: str(certifi_bundle))

    selected = collector.configure_ssl_certificate_bundle()

    assert selected == certifi_bundle
    assert collector.os.environ["SSL_CERT_FILE"] == str(certifi_bundle)


def test_configure_ssl_certificate_bundle_preserves_explicit_override(tmp_path, monkeypatch):
    explicit_bundle = tmp_path / "managed.pem"
    monkeypatch.setenv("SSL_CERT_FILE", str(explicit_bundle))

    selected = collector.configure_ssl_certificate_bundle()

    assert selected == explicit_bundle
    assert collector.os.environ["SSL_CERT_FILE"] == str(explicit_bundle)


def test_run_one_falls_back_when_detected_ookla_cli_fails(monkeypatch, capsys):
    fallback_result = _row(datetime.now(timezone.utc))
    monkeypatch.setattr(collector, "find_ookla_cli", lambda configured_path="": collector.Path("/official/speedtest"))
    monkeypatch.setattr(
        collector,
        "run_one_via_ookla",
        lambda server_id, executable: (_ for _ in ()).throw(RuntimeError("empty JSON response")),
    )
    monkeypatch.setattr(collector, "run_one_via_python", lambda server_id: fallback_result)

    result = collector.run_one(None, prefer_ookla=True, allow_python_fallback=True)

    assert result == fallback_result
    assert "Compatibility mode is using the Python engine" in capsys.readouterr().out


def test_run_one_does_not_fall_back_when_ookla_is_required(monkeypatch):
    monkeypatch.setattr(collector, "find_ookla_cli", lambda configured_path="": collector.Path("/official/speedtest"))
    monkeypatch.setattr(
        collector,
        "run_one_via_ookla",
        lambda server_id, executable: (_ for _ in ()).throw(RuntimeError("empty JSON response")),
    )

    try:
        collector.run_one(None, prefer_ookla=True, allow_python_fallback=False)
    except RuntimeError as exc:
        assert str(exc) == "empty JSON response"
    else:
        raise AssertionError("Expected the required Ookla failure to be raised")


def test_prune_main_removes_rows_older_than_retention_period():
    now = datetime.now(timezone.utc)
    frame = pd.DataFrame([
        _row(now - timedelta(days=31)),
        _row(now - timedelta(days=1)),
    ])

    pruned = collector.prune_main(frame)

    assert len(pruned) == 1
    assert float(pruned.iloc[0]["download_mbps"]) == 100.0


def test_archive_keeps_only_twelve_monthly_files(tmp_path, monkeypatch):
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    monkeypatch.setattr(collector, "ARCHIVE_DIR", archive_dir)

    start = pd.Timestamp("2025-01-01", tz="UTC")
    for offset in range(13):
        timestamp = (start + pd.DateOffset(months=offset)).to_pydatetime()
        collector.archive_append(_row(timestamp))

    archives = sorted(archive_dir.glob("speedtest_*.csv"))
    assert len(archives) == 12
    assert archives[0].name == "speedtest_2025-02.csv"
    assert archives[-1].name == "speedtest_2026-01.csv"


def test_calibrate_preferred_area_matches_and_ranks_regional_servers(monkeypatch):
    austin = {
        "id": "101",
        "sponsor": "Example Fiber",
        "name": "Austin, TX",
        "country": "United States",
        "cc": "US",
    }
    dallas = {
        "id": "202",
        "sponsor": "Other Fiber",
        "name": "Dallas, TX",
        "country": "United States",
        "cc": "US",
    }

    class FakeSpeedtest:
        def get_servers(self):
            return {10.0: [dallas], 20.0: [austin]}

        def get_best_server(self, candidates):
            assert candidates == [austin]
            return austin

    monkeypatch.setattr(collector, "_new_python_speedtest", FakeSpeedtest)

    calibrated = collector.calibrate_preferred_area("Austin, TX")

    assert calibrated == [
        {"id": "101", "label": "101 - Example Fiber - Austin, TX"}
    ]


def test_preferred_targets_calibrate_and_persist_candidates(tmp_path, monkeypatch):
    from speedtest_dashboard.app_config import load_settings, set_server_preference

    set_server_preference("preferred_area", "Austin, TX", tmp_path)
    monkeypatch.setattr(
        collector,
        "calibrate_preferred_area",
        lambda area: [
            {"id": "101", "label": "101 - Primary - Austin, TX"},
            {"id": "102", "label": "102 - Backup - Austin, TX"},
        ],
    )

    targets, preferred = collector.preferred_targets(tmp_path)

    assert preferred
    assert targets == ["101", "102", None]
    assert load_settings(tmp_path)["server_selection"]["server_ids"] == [
        "101",
        "102",
    ]


def test_collector_fails_over_between_saved_regional_servers(tmp_path, monkeypatch):
    from speedtest_dashboard.app_config import (
        save_server_calibration,
        set_server_preference,
    )

    set_server_preference("preferred_area", "Austin, TX", tmp_path)
    save_server_calibration(
        "Austin, TX",
        [
            {"id": "101", "label": "101 - Primary - Austin, TX"},
            {"id": "102", "label": "102 - Backup - Austin, TX"},
        ],
        override=tmp_path,
    )
    calls = []

    def fake_run_one(server_id, prefer_ookla, allow_python_fallback, configured_path=""):
        calls.append(server_id)
        if server_id == "101":
            raise RuntimeError("primary unavailable")
        return _row(datetime.now(timezone.utc)) | {
            "server_id": server_id,
            "server_name": "Backup - Austin, TX",
        }

    monkeypatch.setattr(collector, "run_one", fake_run_one)

    assert collector.main(["--data-dir", str(tmp_path), "--no-ookla"])
    assert calls == ["101", "102"]
    written = pd.read_csv(tmp_path / "speedtest_results.csv")
    assert written.iloc[-1]["server_id"] == 102


def test_collector_labels_unrestricted_fallback_after_regional_failures(
    tmp_path, monkeypatch
):
    from speedtest_dashboard.app_config import (
        save_server_calibration,
        set_server_preference,
    )

    set_server_preference("preferred_area", "Austin, TX", tmp_path)
    save_server_calibration(
        "Austin, TX",
        [{"id": "101", "label": "101 - Primary - Austin, TX"}],
        override=tmp_path,
    )

    def fake_run_one(server_id, prefer_ookla, allow_python_fallback, configured_path=""):
        if server_id is not None:
            raise RuntimeError("regional server unavailable")
        return _row(datetime.now(timezone.utc)) | {
            "server_id": "999",
            "server_name": "Provider Choice - Remote, WA",
        }

    monkeypatch.setattr(collector, "run_one", fake_run_one)

    assert collector.main(["--data-dir", str(tmp_path), "--no-ookla"])
    written = pd.read_csv(tmp_path / "speedtest_results.csv")
    assert written.iloc[-1]["server_name"] == (
        "Automatic fallback - Provider Choice - Remote, WA"
    )


def test_official_cli_detection_rejects_python_speedtest_command(tmp_path, monkeypatch):
    executable = tmp_path / "speedtest"
    executable.write_text("placeholder", encoding="utf-8")
    monkeypatch.setattr(
        collector.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout="speedtest-cli 2.1.3",
            stderr="",
        ),
    )

    assert not collector.is_official_ookla_cli(executable)


def test_official_cli_detection_accepts_ookla_binary(tmp_path, monkeypatch):
    executable = tmp_path / "speedtest"
    executable.write_text("placeholder", encoding="utf-8")
    monkeypatch.setattr(
        collector.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout="Speedtest by Ookla 1.2.0.84",
            stderr="",
        ),
    )

    assert collector.is_official_ookla_cli(executable)


def test_default_collection_pauses_when_official_cli_is_missing(tmp_path, monkeypatch):
    from speedtest_dashboard.app_config import load_collector_status

    monkeypatch.setattr(collector, "find_ookla_cli", lambda configured_path="": None)
    monkeypatch.setattr(
        collector,
        "run_one_via_python",
        lambda server_id: (_ for _ in ()).throw(
            AssertionError("Python compatibility engine must not run by default")
        ),
    )

    assert not collector.main(["--data-dir", str(tmp_path)])
    status = load_collector_status(tmp_path)
    assert status["state"] == "setup_required"
    assert "official Ookla CLI" in status["message"]
