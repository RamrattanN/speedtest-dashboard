import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import tomllib

import pandas as pd
from streamlit.testing.v1 import AppTest

from speedtest_dashboard.app_config import load_settings


def test_dashboard_renders_without_data(tmp_path, monkeypatch):
    monkeypatch.setenv("SPEEDTEST_DASHBOARD_DATA_DIR", str(tmp_path))
    dashboard_path = Path(__file__).parents[1] / "src" / "speedtest_dashboard" / "dashboard.py"
    app = AppTest.from_file(dashboard_path)

    app.run(timeout=20)

    assert not app.exception
    assert any("Speedtest Monitor" in block.value for block in app.markdown)
    assert not any("LOCAL MONITOR" in block.value for block in app.markdown)
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
    rendered_markdown = [block.value for block in app.markdown]
    trend_index = next(
        index
        for index, value in enumerate(rendered_markdown)
        if "PERFORMANCE TREND" in value
    )
    latest_index = next(
        index
        for index, value in enumerate(rendered_markdown)
        if "LATEST RESULT" in value
    )
    overview_index = next(
        index
        for index, value in enumerate(rendered_markdown)
        if "CONNECTION OVERVIEW" in value
    )
    range_index = next(
        index
        for index, value in enumerate(rendered_markdown)
        if "SELECTED WINDOW" in value
    )
    assert trend_index < latest_index < range_index < overview_index
    assert len(app.dataframe) == 1
    range_table = app.dataframe[0].value
    assert list(range_table.columns) == ["Minimum", "Average", "Peak"]
    assert list(range_table.index) == [
        "Download (Mbps)",
        "Upload (Mbps)",
        "Ping (ms)",
    ]
    assert range_table.loc["Download (Mbps)", "Peak"] == 181.2
    assert any(
        "Test engine: Python fallback" in caption.value
        for caption in app.caption
    )


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
    refresh_button = next(
        button for button in app.button if button.label == "Refresh now"
    )
    assert refresh_button.disabled
    assert app.multiselect[0].value == ["1 · First Server"]

    app.toggle[0].set_value(False).run(timeout=20)
    assert not app.exception
    assert app.toggle[0].value is False
    refresh_button = next(
        button for button in app.button if button.label == "Refresh now"
    )
    assert not refresh_button.disabled

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


def test_chart_type_redraws_chart_and_manual_refresh_tracks_auto_refresh(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("SPEEDTEST_DASHBOARD_DATA_DIR", str(tmp_path))
    now = datetime.now(timezone.utc)
    pd.DataFrame(
        [
            {
                "timestamp": now.isoformat().replace("+00:00", "Z"),
                "ping_ms": 50.0,
                "download_mbps": 100.0,
                "upload_mbps": 40.0,
                "server_id": "1",
                "server_name": "First Server",
                "engine": "python-lib",
            }
        ]
    ).to_csv(tmp_path / "speedtest_results.csv", index=False)
    dashboard_path = Path(__file__).parents[1] / "src" / "speedtest_dashboard" / "dashboard.py"
    app = AppTest.from_file(dashboard_path)

    app.run(timeout=20)
    bar_spec = json.loads(app.get("plotly_chart")[0].proto.spec)
    assert [trace["type"] for trace in bar_spec["data"]] == [
        "bar",
        "bar",
        "scatter",
    ]
    assert bar_spec["layout"]["xaxis"]["fixedrange"] is False
    assert bar_spec["layout"]["yaxis"]["fixedrange"] is True
    assert bar_spec["layout"]["yaxis2"]["fixedrange"] is True
    assert next(
        button for button in app.button if button.label == "Refresh now"
    ).disabled

    app.radio[0].set_value("Line / Curve").run(timeout=20)
    line_spec = json.loads(app.get("plotly_chart")[0].proto.spec)
    assert app.radio[0].value == "Line / Curve"
    assert [trace["type"] for trace in line_spec["data"]] == [
        "scatter",
        "scatter",
        "scatter",
    ]

    app.toggle[0].set_value(False).run(timeout=20)
    refresh_button = next(
        button for button in app.button if button.label == "Refresh now"
    )
    assert not refresh_button.disabled
    refresh_button.click().run(timeout=20)
    assert not app.exception


def test_dashboard_saves_location_neutral_server_preference(tmp_path, monkeypatch):
    monkeypatch.setenv("SPEEDTEST_DASHBOARD_DATA_DIR", str(tmp_path))
    pd.DataFrame(
        [
            {
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "ping_ms": 50.0,
                "download_mbps": 100.0,
                "upload_mbps": 40.0,
                "server_id": "1",
                "server_name": "Automatic Server",
                "engine": "python-lib",
            }
        ]
    ).to_csv(tmp_path / "speedtest_results.csv", index=False)
    dashboard_path = Path(__file__).parents[1] / "src" / "speedtest_dashboard" / "dashboard.py"
    app = AppTest.from_file(dashboard_path)

    app.run(timeout=20)
    mode = next(box for box in app.selectbox if box.label == "Selection mode")
    mode.set_value("Preferred city or region").run(timeout=20)
    area = next(field for field in app.text_input if field.label == "Preferred city or region")
    area.set_value("Austin, TX").run(timeout=20)
    next(
        button
        for button in app.button
        if button.label == "Save test server preference"
    ).click().run(timeout=20)

    selection = load_settings(tmp_path)["server_selection"]
    assert selection["mode"] == "preferred_area"
    assert selection["area"] == "Austin, TX"
    assert selection["server_ids"] == []


def test_dashboard_requires_explicit_python_compatibility_mode(tmp_path, monkeypatch):
    monkeypatch.setenv("SPEEDTEST_DASHBOARD_DATA_DIR", str(tmp_path))
    pd.DataFrame(
        [
            {
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "ping_ms": 50.0,
                "download_mbps": 100.0,
                "upload_mbps": 40.0,
                "server_id": "1",
                "server_name": "Example Server",
                "engine": "ookla-cli",
            }
        ]
    ).to_csv(tmp_path / "speedtest_results.csv", index=False)
    dashboard_path = Path(__file__).parents[1] / "src" / "speedtest_dashboard" / "dashboard.py"
    app = AppTest.from_file(dashboard_path)

    app.run(timeout=20)
    policy = next(box for box in app.selectbox if box.label == "Engine policy")
    assert policy.value == "Official Ookla CLI only (recommended)"
    policy.set_value("Compatibility mode (allow Python fallback)").run(timeout=20)
    next(
        button for button in app.button if button.label == "Save measurement engine"
    ).click().run(timeout=20)

    assert load_settings(tmp_path)["measurement_engine"]["mode"] == "compatibility"


def test_dashboard_defaults_chart_and_ranges_to_latest_engine(tmp_path, monkeypatch):
    monkeypatch.setenv("SPEEDTEST_DASHBOARD_DATA_DIR", str(tmp_path))
    now = datetime.now(timezone.utc)
    pd.DataFrame(
        [
            {
                "timestamp": (now - pd.Timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
                "ping_ms": 90.0,
                "download_mbps": 40.0,
                "upload_mbps": 20.0,
                "server_id": "1",
                "server_name": "Compatibility Server",
                "engine": "python-lib",
            },
            {
                "timestamp": now.isoformat().replace("+00:00", "Z"),
                "ping_ms": 15.0,
                "download_mbps": 400.0,
                "upload_mbps": 100.0,
                "server_id": "2",
                "server_name": "Official Server",
                "engine": "ookla-cli",
            },
        ]
    ).to_csv(tmp_path / "speedtest_results.csv", index=False)
    dashboard_path = Path(__file__).parents[1] / "src" / "speedtest_dashboard" / "dashboard.py"
    app = AppTest.from_file(dashboard_path)

    app.run(timeout=20)

    engine_filter = next(
        field for field in app.multiselect if field.label == "Measurement engines"
    )
    assert engine_filter.value == ["ookla-cli"]
    range_table = app.dataframe[0].value
    assert range_table.loc["Download (Mbps)", "Average"] == 400.0


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
    assert any(
        "Turn off Refresh display every 60s" in block.value
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
    assert "Install or update the application" in help_text
    assert "not code-signed or notarized" in help_text
    assert "Data and privacy" in help_text
    assert "Measurements are stored locally" in help_text
    install_card = next(
        block.value
        for block in app.markdown
        if "Install or update the application" in block.value
    )
    assert install_card.startswith('<section class="rr-help-card">')
    assert "<ol><li>" in install_card
    assert "version 1.1.0" in install_card
    assert "helper itself" in install_card
    assert "Open Anyway" in install_card
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
    assert "Run the current Windows x64 installer" in help_text
    assert "Microsoft Defender SmartScreen" in help_text
    assert "not code-signed" in help_text
    install_card = next(
        block.value
        for block in app.markdown
        if "Install or update the application" in block.value
    )
    assert install_card.startswith('<section class="rr-help-card">')
    assert "<ol><li>" in install_card
    assert "version 1.1.0" in install_card
    assert "Applications folder" not in help_text
    assert "disk image" not in help_text


def test_streamlit_theme_uses_ramrattan_palette():
    config_path = Path(__file__).parents[1] / ".streamlit" / "config.toml"
    with config_path.open("rb") as config_file:
        theme = tomllib.load(config_file)["theme"]

    assert theme["primaryColor"] == "#173F63"
    assert theme["backgroundColor"] == "#F3F7FA"
    assert theme["secondaryBackgroundColor"] == "#FFFFFF"
