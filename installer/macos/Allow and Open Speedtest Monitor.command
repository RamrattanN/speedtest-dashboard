#!/bin/zsh
set -euo pipefail

APP_PATH="/Applications/Speedtest Monitor.app"

echo "Speedtest Monitor security approval helper"
echo
echo "Use this helper only for Speedtest Monitor downloaded from the official project."
echo "It will remove the macOS quarantine attribute only from:"
echo "  $APP_PATH"
echo "macOS will request an administrator password, then the application will open."
echo

if [[ ! -d "$APP_PATH" ]]; then
  echo "Speedtest Monitor is not installed in Applications."
  echo "Drag the application from the disk image to Applications, then run this helper again."
  echo
  read -r "?Press Return to close this window."
  exit 1
fi

read -r "reply?Continue? [y/N] "
case "$reply" in
  y|Y|yes|YES|Yes)
    ;;
  *)
    echo "No changes were made."
    exit 0
    ;;
esac

sudo /usr/bin/xattr -dr com.apple.quarantine "$APP_PATH"
/usr/bin/open "$APP_PATH"

echo
echo "Speedtest Monitor was approved and opened."
