from io import BytesIO, TextIOWrapper
import threading
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


def test_macos_service_command_identifies_owning_controller(tmp_path, monkeypatch):
    monkeypatch.setattr(macos_app, "is_frozen", lambda: False)

    command = macos_app.service_command(8600, 300, tmp_path, controller_pid=43299)

    assert command[-2:] == ["--controller-pid", "43299"]


def test_macos_finds_only_reparented_legacy_service_for_same_data_dir(tmp_path):
    data_dir = tmp_path / "SpeedtestDashboard"
    other_dir = tmp_path / "OtherDashboard"
    process_table = f"""
43299 1 /Applications/Speedtest Monitor.app/Contents/MacOS/Speedtest Monitor
43356 43299 /Applications/Speedtest Monitor.app/Contents/MacOS/Speedtest Monitor --service --port 8501 --interval 300 --data-dir {data_dir}
38042 1 /Applications/Speedtest Monitor.app/Contents/MacOS/Speedtest Monitor --service --port 8501 --interval 300 --data-dir {data_dir}
38043 1 /Applications/Speedtest Monitor.app/Contents/MacOS/Speedtest Monitor --service --port 8502 --interval 300 --data-dir {other_dir}
"""

    assert macos_app.legacy_orphan_service_pids(data_dir, process_table) == [38042]


def test_macos_service_exits_when_owning_controller_is_gone(monkeypatch):
    exits = []
    monkeypatch.setattr(macos_app.os, "getppid", lambda: 1)
    monkeypatch.setattr(macos_app.os, "_exit", lambda code: exits.append(code))

    macos_app._exit_when_controller_stops(43299, poll_seconds=0)

    assert exits == [0]


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
    assert macos_app.APP_BUILD == "1.1.0"


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


def test_windows_service_command_identifies_owning_controller(tmp_path, monkeypatch):
    monkeypatch.setattr(windows_app, "is_frozen", lambda: False)

    command = windows_app.service_command(8600, 300, tmp_path, controller_pid=41856)

    assert command[-2:] == ["--controller-pid", "41856"]


def test_windows_service_exits_when_owning_controller_is_gone(monkeypatch):
    exits = []
    monkeypatch.setattr(windows_app.os, "getppid", lambda: 1)
    monkeypatch.setattr(windows_app.os, "_exit", lambda code: exits.append(code))

    windows_app._exit_when_controller_stops(41856, poll_seconds=0)

    assert exits == [0]


def test_windows_collector_command_uses_isolated_one_shot_process(tmp_path, monkeypatch):
    monkeypatch.setattr(windows_app, "is_frozen", lambda: False)

    assert windows_app.collector_command(tmp_path) == [
        windows_app.sys.executable,
        "-m",
        "speedtest_dashboard.windows_app",
        "--collect-once",
        "--data-dir",
        str(tmp_path),
    ]


def test_windows_collector_cycle_terminates_frozen_measurement(tmp_path, monkeypatch):
    class FrozenProcess:
        def wait(self, timeout):
            raise windows_app.subprocess.TimeoutExpired("collector", timeout)

    frozen = FrozenProcess()
    terminated = []
    monkeypatch.setattr(windows_app.subprocess, "Popen", lambda *args, **kwargs: frozen)
    monkeypatch.setattr(
        windows_app,
        "terminate_process_tree",
        lambda process: terminated.append(process),
    )

    completed = windows_app.run_collector_cycle(tmp_path, timeout=180)

    assert not completed
    assert terminated == [frozen]


def test_windows_collector_cycle_recovers_after_child_failure(tmp_path, monkeypatch):
    class FailedProcess:
        def wait(self, timeout):
            return 7

    monkeypatch.setattr(
        windows_app.subprocess,
        "Popen",
        lambda *args, **kwargs: FailedProcess(),
    )

    assert not windows_app.run_collector_cycle(tmp_path)


def test_windows_supervisor_consumes_one_request_as_one_additional_cycle(
    tmp_path,
    monkeypatch,
):
    stop_event = threading.Event()
    cycles = []

    def fake_cycle(data_dir, timeout):
        cycles.append(data_dir)
        if len(cycles) == 2:
            stop_event.set()
        return True

    restart_checks = []

    def fake_wait(wait_seconds, data_dir, stop_event=None):
        restart_checks.append((wait_seconds, data_dir))
        return len(restart_checks) == 1

    monkeypatch.setattr(windows_app, "run_collector_cycle", fake_cycle)
    monkeypatch.setattr(windows_app, "wait_for_collection_restart", fake_wait)

    windows_app.supervise_collector(
        300,
        tmp_path,
        stop_event=stop_event,
    )

    assert cycles == [tmp_path, tmp_path]
    assert len(restart_checks) == 2


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
    assert windows_app.APP_BUILD == "1.1.0"


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
    assert stream.line_buffering
    assert stream.write_through
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
