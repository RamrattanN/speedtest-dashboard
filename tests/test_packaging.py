import base64
import importlib.util
from io import BytesIO
from pathlib import Path
import tomllib

from PIL import Image

from speedtest_dashboard import __version__


def test_macos_icon_source_fills_canvas(tmp_path):
    project_root = Path(__file__).parents[1]
    module_path = project_root / "scripts" / "build_macos_icon.py"
    spec = importlib.util.spec_from_file_location("build_macos_icon", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = (
        project_root
        / "src"
        / "speedtest_dashboard"
        / "assets"
        / "ramrattan-logo.png.b64"
    )
    target = tmp_path / "source.png"

    module.build_icon_source(source, target)

    icon = Image.open(target).convert("RGBA")
    bounds = icon.getchannel("A").getbbox()
    assert icon.size == (1024, 1024)
    assert bounds is not None
    assert bounds[2] - bounds[0] >= 600
    assert bounds[3] - bounds[1] >= 850


def test_packaged_logo_remains_valid_base64_png():
    project_root = Path(__file__).parents[1]
    source = (
        project_root
        / "src"
        / "speedtest_dashboard"
        / "assets"
        / "ramrattan-logo.png.b64"
    )

    logo = Image.open(BytesIO(base64.b64decode(source.read_text(encoding="utf-8"))))
    assert logo.format == "PNG"


def test_production_version_is_consistent_across_platform_packages():
    project_root = Path(__file__).parents[1]
    with (project_root / "pyproject.toml").open("rb") as project_file:
        project_version = tomllib.load(project_file)["project"]["version"]

    assert __version__ == "1.1.0"
    assert project_version == __version__
    expected_references = {
        "SpeedtestMonitor.spec": '"CFBundleShortVersionString": "1.1.0"',
        "installer/windows/SpeedtestMonitor.iss": '#define AppVersion "1.1.0"',
        "installer/windows/version_info.txt": "StringStruct('ProductVersion', '1.1.0')",
        "scripts/build_macos_release.sh": "-1.1.0.dmg",
        "scripts/build_windows_release.ps1": "-1.1.0.exe",
        ".github/workflows/macos-release.yml": "-1.1.0.dmg",
        ".github/workflows/windows-release.yml": "-1.1.0.exe",
        ".github/workflows/publish-production-release.yml": 'default: "1.1.0"',
    }
    for relative_path, expected in expected_references.items():
        contents = (project_root / relative_path).read_text(encoding="utf-8")
        assert expected in contents, relative_path


def test_macos_approval_helper_is_scoped_to_installed_application():
    project_root = Path(__file__).parents[1]
    helper = (
        project_root
        / "installer"
        / "macos"
        / "Allow and Open Speedtest Monitor.command"
    ).read_text(encoding="utf-8")

    assert 'APP_PATH="/Applications/Speedtest Monitor.app"' in helper
    assert 'sudo /usr/bin/xattr -dr com.apple.quarantine "$APP_PATH"' in helper
    assert '/usr/bin/open "$APP_PATH"' in helper
    assert 'read -r "reply?Continue? [y/N] "' in helper
    assert "Open Anyway" in helper
    assert "Read Me First - macOS Security.txt" in helper
    assert "rm -rf" not in helper

    read_me_path = (
        project_root
        / "installer"
        / "macos"
        / "Read Me First - macOS Security.txt"
    )
    read_me = read_me_path.read_text(encoding="utf-8")
    assert "helper is also unsigned" in read_me
    assert "message about Allow and Open Speedtest Monitor.command" in read_me
    assert "sudo xattr -dr com.apple.quarantine" in read_me
    assert 'open "/Applications/Speedtest Monitor.app"' in read_me

    build_script = (project_root / "scripts" / "build_macos_release.sh").read_text(
        encoding="utf-8"
    )
    assert 'installer/macos/Allow and Open Speedtest Monitor.command' in build_script
    assert 'installer/macos/Read Me First - macOS Security.txt' in build_script
    assert 'installer/macos/Install Official Ookla CLI.webloc' in build_script
    assert 'chmod +x "$RELEASE_DIR/Allow and Open Speedtest Monitor.command"' in build_script


def test_installers_link_to_official_ookla_cli_without_bundling_it():
    project_root = Path(__file__).parents[1]
    windows_installer = (
        project_root / "installer" / "windows" / "SpeedtestMonitor.iss"
    ).read_text(encoding="utf-8")
    macos_link = (
        project_root / "installer" / "macos" / "Install Official Ookla CLI.webloc"
    ).read_text(encoding="utf-8")

    official_url = "https://www.speedtest.net/apps/cli"
    assert official_url in windows_installer
    assert official_url in macos_link
    assert "speedtest.exe" not in windows_installer
