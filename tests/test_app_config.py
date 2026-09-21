from pathlib import Path

from speedtest_dashboard.app_config import DATA_DIR_ENV, configure_data_paths, get_data_dir


def test_explicit_data_directory_has_priority(tmp_path, monkeypatch):
    monkeypatch.setenv(DATA_DIR_ENV, str(tmp_path / "environment"))
    explicit = tmp_path / "explicit"

    assert get_data_dir(explicit) == explicit.resolve()


def test_environment_data_directory_is_used(tmp_path, monkeypatch):
    configured = tmp_path / "configured"
    monkeypatch.setenv(DATA_DIR_ENV, str(configured))

    csv_path, archive_dir = configure_data_paths()

    assert csv_path == configured.resolve() / "speedtest_results.csv"
    assert archive_dir == configured.resolve() / "archive"
    assert archive_dir.is_dir()


def test_default_is_visible_folder_in_user_home(tmp_path, monkeypatch):
    monkeypatch.delenv(DATA_DIR_ENV, raising=False)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))

    assert get_data_dir() == (tmp_path / "SpeedtestDashboard").resolve()
