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

    assert __version__ == "1.0.0"
    assert project_version == __version__
    expected_references = {
        "SpeedtestMonitor.spec": '"CFBundleShortVersionString": "1.0.0"',
        "installer/windows/SpeedtestMonitor.iss": '#define AppVersion "1.0.0"',
        "installer/windows/version_info.txt": "StringStruct('ProductVersion', '1.0.0')",
        "scripts/build_macos_release.sh": "-1.0.0.dmg",
        "scripts/build_windows_release.ps1": "-1.0.0.exe",
        ".github/workflows/macos-release.yml": "-1.0.0.dmg",
        ".github/workflows/windows-release.yml": "-1.0.0.exe",
    }
    for relative_path, expected in expected_references.items():
        contents = (project_root / relative_path).read_text(encoding="utf-8")
        assert expected in contents, relative_path
