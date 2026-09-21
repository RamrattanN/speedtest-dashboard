"""Build the Windows icon from the packaged Ramrattan logo."""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

from PIL import Image


root = Path(__file__).resolve().parents[1]
source = root / "src" / "speedtest_dashboard" / "assets" / "ramrattan-logo.png.b64"
target = root / "build" / "windows-icon" / "SpeedtestMonitor.ico"
target.parent.mkdir(parents=True, exist_ok=True)

logo = Image.open(BytesIO(base64.b64decode(source.read_text(encoding="utf-8")))).convert("RGBA")
canvas = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
logo.thumbnail((210, 210), Image.Resampling.LANCZOS)
canvas.alpha_composite(logo, ((256 - logo.width) // 2, (256 - logo.height) // 2))
canvas.save(target, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print(f"Created: {target}")
