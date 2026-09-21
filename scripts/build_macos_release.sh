#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ICON_ROOT="$ROOT/build/macos-icon"
ICONSET="$ICON_ROOT/SpeedtestMonitor.iconset"
SOURCE_PNG="$ICON_ROOT/source.png"

rm -rf "$ICONSET"
mkdir -p "$ICONSET"

python scripts/build_macos_icon.py

for size in 16 32 128 256 512; do
  sips -z "$size" "$size" "$SOURCE_PNG" --out "$ICONSET/icon_${size}x${size}.png" >/dev/null
  double=$((size * 2))
  sips -z "$double" "$double" "$SOURCE_PNG" --out "$ICONSET/icon_${size}x${size}@2x.png" >/dev/null
done

iconutil -c icns "$ICONSET" -o "$ICON_ROOT/SpeedtestMonitor.icns"

python -m PyInstaller --clean --noconfirm SpeedtestMonitor.spec

RELEASE_DIR="$ROOT/dist/release"
DMG_PATH="$ROOT/dist/Speedtest-Monitor-macOS-Intel-0.2.0.dmg"
rm -rf "$RELEASE_DIR" "$DMG_PATH"
mkdir -p "$RELEASE_DIR"
cp -R "$ROOT/dist/Speedtest Monitor.app" "$RELEASE_DIR/"
ln -s /Applications "$RELEASE_DIR/Applications"

hdiutil create \
  -volname "Speedtest Monitor" \
  -srcfolder "$RELEASE_DIR" \
  -ov \
  -format UDZO \
  "$DMG_PATH"

echo "Created: $DMG_PATH"
