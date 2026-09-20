# Speedtest Dashboard

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B)
[![CI](https://github.com/RamrattanN/speedtest-dashboard/actions/workflows/ci.yml/badge.svg)](https://github.com/RamrattanN/speedtest-dashboard/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/RamrattanN/speedtest-dashboard?sort=semver)](https://github.com/RamrattanN/speedtest-dashboard/releases)

A self-hosted internet speed monitor for macOS and Windows.  It periodically
collects ping, download, and upload results using the official Ookla Speedtest
CLI when available, with the Python `speedtest-cli` library as a fallback.
Results are stored locally in CSV files and displayed in a Streamlit dashboard.

![Speedtest Dashboard Screenshot](assets/dashboard_preview.png?v=2025-09-04-1)

## Features

- Configurable test interval, dashboard port, and data folder.
- Approximately 30 days of results in the main CSV.
- Up to 12 monthly archive files.
- Bar and line charts with previous-period comparison.
- Timezone, theme, color, server, and date-window controls.
- macOS and Windows launchers using an isolated local Python environment.
- Installable command-line package.
- Automated tests that do not perform real internet speed tests.

## Quick start on macOS

Install Python 3.11 or newer, then clone the repository and run:

```bash
chmod +x RunSpeedTest.command
./RunSpeedTest.command
```

The dashboard opens at <http://localhost:8501>.  Results are stored in
`~/SpeedtestDashboard` by default.

See the [Mac Testing Guide](docs/Mac-Testing.md) for complete installation and
acceptance steps.  The [VS Code Setup Guide](docs/VS-Code-Setup-Mac.md) explains
how to work on the project without memorizing Terminal commands.

## Quick start on Windows

Install Python 3.11 or newer, then double-click `RunSpeedTest.bat`, or use
PowerShell:

```powershell
.\RunSpeedTest.ps1 -Interval 120 -Port 8501
```

Results are stored in `%USERPROFILE%\SpeedtestDashboard` by default.

## Command-line use

Install the application into the current Python environment:

```bash
python3 -m pip install -e .
```

Available commands:

```bash
speedtest-dashboard --interval 120 --port 8501
speedtest-collector --data-dir ~/SpeedtestDashboard
speedtest-dashboard-ui --server.port 8501
```

Set `SPEEDTEST_DASHBOARD_DATA_DIR` to change the data directory for all
commands.  The combined launcher also accepts `--data-dir`.

## Repository structure

```text
speedtest-dashboard/
├── src/speedtest_dashboard/  # Collector, dashboard, runner, and configuration
├── tests/                    # Offline automated tests
├── RunSpeedTest.command      # macOS launcher
├── RunSpeedTest.ps1          # Windows PowerShell launcher
├── RunSpeedTest.bat          # Windows batch launcher
├── docs/                     # Guides and project documentation
└── pyproject.toml            # Package and dependency configuration
```

## Development checks

```bash
python3 -m pip install -e ".[test]"
pytest -q
python3 -m build
```

CI verifies Python 3.11 and 3.12 on Linux, Python 3.12 on macOS, source
compilation, tests, the Mac launcher, wheel creation, isolated installation,
and installed command entry points.

## Documentation

- [Mac Testing Guide](docs/Mac-Testing.md)
- [VS Code Setup on Mac](docs/VS-Code-Setup-Mac.md)
- [Getting Started](docs/wiki/Getting-Started.md)
- [Configuration](docs/wiki/Configuration.md)
- [Running the Dashboard](docs/wiki/Running-the-Dashboard.md)
- [Troubleshooting](docs/wiki/Troubleshooting.md)
- [Roadmap](docs/wiki/Roadmap.md)

## License

Licensed under the MIT License.  Ookla's license applies when its Speedtest CLI
is used.

## Credits

- Concept and direction: Nilesh Ramrattan
- Development assistance: ChatGPT by OpenAI
- Stack: Ookla Speedtest CLI, Streamlit, pandas, NumPy, and Plotly
