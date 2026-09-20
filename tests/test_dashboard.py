import base64
from datetime import datetime, timezone
from pathlib import Path
import tomllib

import pandas as pd
from streamlit.testing.v1 import AppTest


def test_dashboard_renders_without_data(tmp_path, monkeypatch):
    monkeypatch.setenv("SPEEDTEST_DASHBOARD_DATA_DIR", str(tmp_path))
    dashboard_path = Path(__file__).parents[1] / "src" / "speedtest_dashboard" / "dashboard.py"
    app = AppTest.from_file(dashboard_path)

    app.run(timeout=20)

    assert not app.exception
    assert any("Speedtest Monitor" in block.value for block in app.markdown)
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
    assert [metric.label for metric in app.metric] == [
        "Download",
        "Upload",
        "Ping",
        "Recorded",
    ]
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


def test_help_navigation_is_specific_to_speedtest(tmp_path, monkeypatch):
    monkeypatch.setenv("SPEEDTEST_DASHBOARD_DATA_DIR", str(tmp_path))
    dashboard_path = Path(__file__).parents[1] / "src" / "speedtest_dashboard" / "dashboard.py"
    app = AppTest.from_file(dashboard_path)

    app.run(timeout=20)
    help_button = next(
        button for button in app.button if button.label == "Help with this page"
    )
    help_button.click().run(timeout=20)

    assert not app.exception
    assert any("Using the Speedtest Monitor" in block.value for block in app.markdown)
    assert any(
        "collector normally records a result every five minutes" in block.value
        for block in app.markdown
    )
    assert app.code[0].value == "./RunSpeedTest.command --interval 300"

    close_button = next(button for button in app.button if button.label == "Close X")
    close_button.click().run(timeout=20)
    assert not any(
        "Using the Speedtest Monitor" in block.value for block in app.markdown
    )


def test_ramrattan_logo_asset_is_a_packaged_png():
    asset_path = (
        Path(__file__).parents[1]
        / "src"
        / "speedtest_dashboard"
        / "assets"
        / "ramrattan-logo.png.b64"
    )
    logo_bytes = base64.b64decode(asset_path.read_text(encoding="utf-8"))

    assert logo_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    assert len(logo_bytes) > 20_000


def test_packaged_help_uses_desktop_controller_instructions(tmp_path, monkeypatch):
    monkeypatch.setenv("SPEEDTEST_DASHBOARD_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SPEEDTEST_DASHBOARD_DESKTOP", "1")
    monkeypatch.setenv("SPEEDTEST_DASHBOARD_DESKTOP_PLATFORM", "macos")
    dashboard_path = Path(__file__).parents[1] / "src" / "speedtest_dashboard" / "dashboard.py"
    app = AppTest.from_file(dashboard_path)

    app.run(timeout=20)
    next(button for button in app.button if button.label == "Help with this page").click().run(timeout=20)

    assert not app.exception
    help_text = "\n".join(block.value for block in app.markdown)
    assert "Open Speedtest Monitor from the Applications folder" in help_text
    assert "close the browser tab without stopping collection" in help_text
    assert "Quit Monitor" in help_text
    assert "Install or update the private pilot" in help_text
    assert "not code-signed or notarized" in help_text
    assert "Data and privacy" in help_text
    assert "Measurements are stored locally" in help_text
    assert not app.code


def test_windows_packaged_help_uses_installer_and_start_menu(tmp_path, monkeypatch):
    monkeypatch.setenv("SPEEDTEST_DASHBOARD_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SPEEDTEST_DASHBOARD_DESKTOP", "1")
    monkeypatch.setenv("SPEEDTEST_DASHBOARD_DESKTOP_PLATFORM", "windows")
    dashboard_path = Path(__file__).parents[1] / "src" / "speedtest_dashboard" / "dashboard.py"
    app = AppTest.from_file(dashboard_path)

    app.run(timeout=20)
    next(button for button in app.button if button.label == "Help with this page").click().run(timeout=20)

    assert not app.exception
    help_text = "\n".join(block.value for block in app.markdown)
    assert "Open Speedtest Monitor from the Windows Start menu" in help_text
    assert "Run the current Windows x64 pilot installer" in help_text
    assert "Microsoft Defender SmartScreen" in help_text
    assert "not code-signed" in help_text
    assert "Applications folder" not in help_text
    assert "disk image" not in help_text


def test_streamlit_theme_uses_ramrattan_palette():
    config_path = Path(__file__).parents[1] / ".streamlit" / "config.toml"
    with config_path.open("rb") as config_file:
        theme = tomllib.load(config_file)["theme"]

    assert theme["primaryColor"] == "#173F63"
    assert theme["backgroundColor"] == "#F3F7FA"
    assert theme["secondaryBackgroundColor"] == "#FFFFFF"
