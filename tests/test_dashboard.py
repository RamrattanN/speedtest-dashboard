from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest


def test_dashboard_renders_without_data(tmp_path, monkeypatch):
    monkeypatch.setenv("SPEEDTEST_DASHBOARD_DATA_DIR", str(tmp_path))
    dashboard_path = Path(__file__).parents[1] / "src" / "speedtest_dashboard" / "dashboard.py"
    app = AppTest.from_file(dashboard_path)

    app.run(timeout=20)

    assert not app.exception
    assert [title.value for title in app.title] == ["Speedtest Monitor"]
    assert any("No data yet" in message.value for message in app.info)


def test_dashboard_renders_recorded_measurement(tmp_path, monkeypatch):
    monkeypatch.setenv("SPEEDTEST_DASHBOARD_DATA_DIR", str(tmp_path))
    pd.DataFrame(
        [
            {
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "ping_ms": 62.571,
                "download_mbps": 181.202,
                "upload_mbps": 74.786,
                "server_id": "29471",
                "server_name": "Janus Networks - San Diego, CA",
                "engine": "python-lib",
            }
        ]
    ).to_csv(tmp_path / "speedtest_results.csv", index=False)
    dashboard_path = Path(__file__).parents[1] / "src" / "speedtest_dashboard" / "dashboard.py"
    app = AppTest.from_file(dashboard_path)

    app.run(timeout=20)

    assert not app.exception
    assert [heading.value for heading in app.subheader] == ["Summary (window above)"]
    assert len(app.dataframe) == 1


def test_dashboard_redraw_includes_new_server(tmp_path, monkeypatch):
    monkeypatch.setenv("SPEEDTEST_DASHBOARD_DATA_DIR", str(tmp_path))
    csv_path = tmp_path / "speedtest_results.csv"
    first = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "ping_ms": 50.0,
        "download_mbps": 100.0,
        "upload_mbps": 40.0,
        "server_id": "1",
        "server_name": "First Server",
        "engine": "python-lib",
    }
    pd.DataFrame([first]).to_csv(csv_path, index=False)
    dashboard_path = Path(__file__).parents[1] / "src" / "speedtest_dashboard" / "dashboard.py"
    app = AppTest.from_file(dashboard_path)

    app.run(timeout=20)
    assert app.toggle[0].label == "Refresh display every 60s"
    assert app.multiselect[0].value == ["1 · First Server"]

    second = {
        **first,
        "server_id": "2",
        "server_name": "Second Server",
    }
    pd.DataFrame([first, second]).to_csv(csv_path, index=False)
    app.run(timeout=20)

    assert set(app.multiselect[0].value) == {
        "1 · First Server",
        "2 · Second Server",
    }
