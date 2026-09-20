#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required.  Install Python 3, then run this file again."
  read -r -p "Press Return to close..."
  exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
  echo "Creating the local Python environment..."
  python3 -m venv .venv
fi

echo "Installing or updating Speedtest Dashboard..."
".venv/bin/python" -m pip install --upgrade pip
".venv/bin/python" -m pip install -e .

echo "Starting Speedtest Dashboard..."
echo "Results will be saved in: $HOME/SpeedtestDashboard"
exec ".venv/bin/python" -m speedtest_dashboard "$@"
