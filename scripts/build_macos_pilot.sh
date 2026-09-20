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

PILOT_DIR="$ROOT/dist/pilot"
DMG_PATH="$ROOT/dist/Speedtest-Monitor-macOS-Intel-pilot-4.dmg"
rm -rf "$PILOT_DIR" "$DMG_PATH"
mkdir -p "$PILOT_DIR"
cp -R "$ROOT/dist/Speedtest Monitor.app" "$PILOT_DIR/"
ln -s /Applications "$PILOT_DIR/Applications"

hdiutil create \
  -volname "Speedtest Monitor Pilot" \
  -srcfolder "$PILOT_DIR" \
  -ov \
  -format UDZO \
  "$DMG_PATH"

echo "Created: $DMG_PATH"
