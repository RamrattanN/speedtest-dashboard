from types import SimpleNamespace

from speedtest_dashboard import runner


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
