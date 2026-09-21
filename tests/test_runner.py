from io import BytesIO, TextIOWrapper
from types import SimpleNamespace

from speedtest_dashboard import macos_app, runner, windows_app


class FakeProcess:
    def __init__(self):
        self.terminated = False

    def terminate(self):
        self.terminated = True

    def poll(self):
        return 0


def test_runner_passes_shared_configuration_to_both_processes(tmp_path, monkeypatch):
    origins = {
        "speedtest_dashboard.dashboard": str(tmp_path / "dashboard.py"),
    }
    monkeypatch.setattr(
        runner.importlib.util,
        "find_spec",
        lambda name: SimpleNamespace(origin=origins[name]),
    )

    collector_call = {}
    dashboard_call = {}
    fake_process = FakeProcess()

    def fake_popen(command, env):
        collector_call.update(command=command, env=env)
        return fake_process

    def fake_run(command, check, env):
        dashboard_call.update(command=command, check=check, env=env)

    monkeypatch.setattr(runner.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(
        runner.sys,
        "argv",
        [
            "speedtest-dashboard",
            "--interval",
            "300",
            "--port",
            "8600",
            "--headless",
            "--data-dir",
            str(tmp_path / "data"),
        ],
    )

    runner.main()

    data_dir = str((tmp_path / "data").resolve())
    assert collector_call["command"][-4:] == [
        "--interval",
        "300",
        "--data-dir",
        data_dir,
    ]
    assert collector_call["env"][runner.DATA_DIR_ENV] == data_dir
    assert "8600" in dashboard_call["command"]
    assert "--server.headless" in dashboard_call["command"]
    assert dashboard_call["env"][runner.DATA_DIR_ENV] == data_dir
    assert fake_process.terminated


def test_macos_service_command_uses_module_in_source_mode(tmp_path, monkeypatch):
    monkeypatch.setattr(macos_app, "is_frozen", lambda: False)
    command = macos_app.service_command(8600, 300, tmp_path)

    assert command[:3] == [
        macos_app.sys.executable,
        "-m",
        "speedtest_dashboard.macos_app",
    ]
    assert command[-6:] == [
        "--port",
        "8600",
        "--interval",
        "300",
        "--data-dir",
        str(tmp_path),
    ]


def test_macos_dashboard_path_uses_pyinstaller_bundle(tmp_path, monkeypatch):
    monkeypatch.setattr(macos_app.sys, "_MEIPASS", str(tmp_path), raising=False)

    assert macos_app.dashboard_script_path() == (
        tmp_path / "speedtest_dashboard" / "dashboard.py"
    )


def test_macos_streamlit_options_disable_packaged_development_mode():
    options = macos_app.streamlit_options(8600)

    assert options["global.developmentMode"] is False
    assert options["server.address"] == "127.0.0.1"
    assert options["server.port"] == 8600
    assert options["browser.serverAddress"] == "127.0.0.1"
    assert options["browser.serverPort"] == 8600
    assert macos_app.APP_BUILD == "0.2.0-pilot.4"


def test_macos_service_loads_options_before_starting_server(tmp_path, monkeypatch):
    events = []

    class FakeBootstrap:
        @staticmethod
        def load_config_options(options):
            events.append(("load", options.copy()))

        @staticmethod
        def run(script, is_hello, args, options):
            events.append(("run", options.copy()))

    class FakeCollector:
        @staticmethod
        def main(args):
            return None

    monkeypatch.setitem(macos_app.sys.modules, "streamlit.web", SimpleNamespace(bootstrap=FakeBootstrap))
    monkeypatch.setattr(
        macos_app,
        "threading",
        SimpleNamespace(Thread=lambda **kwargs: SimpleNamespace(start=lambda: None)),
    )
    monkeypatch.setitem(
        macos_app.sys.modules,
        "speedtest_dashboard.collector",
        FakeCollector,
    )

    macos_app.run_services(8600, 300, tmp_path)

    assert [event[0] for event in events] == ["load", "run"]
    assert events[0][1]["global.developmentMode"] is False
    assert events[1][1]["server.port"] == 8600


def test_windows_service_command_uses_module_in_source_mode(tmp_path, monkeypatch):
    monkeypatch.setattr(windows_app, "is_frozen", lambda: False)
    command = windows_app.service_command(8600, 300, tmp_path)

    assert command[:3] == [
        windows_app.sys.executable,
        "-m",
        "speedtest_dashboard.windows_app",
    ]
    assert command[-6:] == [
        "--port",
        "8600",
        "--interval",
        "300",
        "--data-dir",
        str(tmp_path),
    ]


def test_windows_dashboard_path_uses_pyinstaller_bundle(tmp_path, monkeypatch):
    monkeypatch.setattr(windows_app.sys, "_MEIPASS", str(tmp_path), raising=False)

    assert windows_app.dashboard_script_path() == (
        tmp_path / "speedtest_dashboard" / "dashboard.py"
    )


def test_windows_streamlit_options_disable_packaged_development_mode():
    options = windows_app.streamlit_options(8600)

    assert options["global.developmentMode"] is False
    assert options["server.address"] == "127.0.0.1"
    assert options["server.port"] == 8600
    assert options["browser.serverAddress"] == "127.0.0.1"
    assert options["browser.serverPort"] == 8600
    assert windows_app.APP_BUILD == "0.2.0-windows-pilot.4"


def test_windows_log_directory_uses_local_app_data(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    assert windows_app.log_directory() == (
        tmp_path / "Ramrattan Speedtest Monitor" / "Logs"
    )


def test_windows_windowed_service_restores_output_streams(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr(windows_app.sys, "stdout", None)
    monkeypatch.setattr(windows_app.sys, "stderr", None)
    monkeypatch.setattr(windows_app, "_SERVICE_LOG_HANDLE", None)

    windows_app.ensure_service_output_streams()
    print("collector output is available", flush=True)

    assert windows_app.sys.stdout is not None
    assert windows_app.sys.stderr is windows_app.sys.stdout
    assert "collector output is available" in (
        tmp_path / "Ramrattan Speedtest Monitor" / "Logs" / "monitor.log"
    ).read_text(encoding="utf-8")


def test_windows_service_reconfigures_redirected_output_as_utf8():
    raw = BytesIO()
    stream = TextIOWrapper(raw, encoding="cp1252")

    windows_app._configure_utf8_output(stream)
    stream.write("Unicode logging: \u2192")
    stream.flush()

    assert stream.encoding.lower() == "utf-8"
    assert raw.getvalue().decode("utf-8") == "Unicode logging: \u2192"


def test_windows_service_loads_options_before_starting_server(tmp_path, monkeypatch):
    events = []

    class FakeBootstrap:
        @staticmethod
        def load_config_options(options):
            events.append(("load", options.copy()))

        @staticmethod
        def run(script, is_hello, args, options):
            events.append(("run", options.copy()))

    monkeypatch.setitem(
        windows_app.sys.modules,
        "streamlit.web",
        SimpleNamespace(bootstrap=FakeBootstrap),
    )

    windows_app.run_services(8600, 300, tmp_path, start_collector=False)

    assert [event[0] for event in events] == ["load", "run"]
    assert events[0][1]["global.developmentMode"] is False
    assert events[1][1]["server.port"] == 8600
