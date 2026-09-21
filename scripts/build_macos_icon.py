"""Build a full-size macOS icon source from the packaged Ramrattan logo."""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

from PIL import Image


def build_icon_source(source: Path, target: Path) -> None:
    """Crop transparent padding, enlarge the logo, and centre it on the icon canvas."""
    logo = Image.open(
        BytesIO(base64.b64decode(source.read_text(encoding="utf-8")))
    ).convert("RGBA")
    bounds = logo.getchannel("A").getbbox()
    if bounds is None:
        raise ValueError("The Ramrattan logo contains no visible pixels.")
    logo = logo.crop(bounds)

    maximum = 860
    scale = min(maximum / logo.width, maximum / logo.height)
    size = (round(logo.width * scale), round(logo.height * scale))
    logo = logo.resize(size, Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    canvas.alpha_composite(logo, ((1024 - logo.width) // 2, (1024 - logo.height) // 2))
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target)


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    build_icon_source(
        project_root
        / "src"
        / "speedtest_dashboard"
        / "assets"
        / "ramrattan-logo.png.b64",
        project_root / "build" / "macos-icon" / "source.png",
    )
