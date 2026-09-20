from datetime import datetime, timedelta, timezone

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
