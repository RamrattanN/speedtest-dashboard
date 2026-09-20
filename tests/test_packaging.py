import base64
from io import BytesIO
from pathlib import Path

from PIL import Image


def test_macos_icon_source_fills_canvas(tmp_path):
    from scripts.build_macos_icon import build_icon_source

    project_root = Path(__file__).parents[1]
    source = (
        project_root
        / "src"
        / "speedtest_dashboard"
        / "assets"
        / "ramrattan-logo.png.b64"
    )
    target = tmp_path / "source.png"

    build_icon_source(source, target)

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
