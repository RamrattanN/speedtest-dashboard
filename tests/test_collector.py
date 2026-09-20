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
    monkeypatch.setattr(collector, "have_ookla_cli", lambda: True)
    monkeypatch.setattr(
        collector,
        "run_one_via_ookla",
        lambda server_id: (_ for _ in ()).throw(RuntimeError("empty JSON response")),
    )
    monkeypatch.setattr(collector, "run_one_via_python", lambda server_id: fallback_result)

    result = collector.run_one(None, prefer_ookla=True, allow_python_fallback=True)

    assert result == fallback_result
    assert "Falling back to Python speedtest-cli" in capsys.readouterr().out


def test_run_one_does_not_fall_back_when_ookla_is_required(monkeypatch):
    monkeypatch.setattr(collector, "have_ookla_cli", lambda: True)
    monkeypatch.setattr(
        collector,
        "run_one_via_ookla",
        lambda server_id: (_ for _ in ()).throw(RuntimeError("empty JSON response")),
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
