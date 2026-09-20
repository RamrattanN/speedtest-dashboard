from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_dashboard_renders_without_data(tmp_path, monkeypatch):
    monkeypatch.setenv("SPEEDTEST_DASHBOARD_DATA_DIR", str(tmp_path))
    dashboard_path = Path(__file__).parents[1] / "src" / "speedtest_dashboard" / "dashboard.py"
    app = AppTest.from_file(dashboard_path)

    app.run(timeout=20)

    assert not app.exception
    assert [title.value for title in app.title] == ["Speedtest Monitor"]
    assert any("No data yet" in message.value for message in app.info)
