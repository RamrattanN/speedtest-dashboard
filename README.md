# Speedtest Dashboard

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B)
[![CI](https://github.com/RamrattanN/speedtest-dashboard/actions/workflows/ci.yml/badge.svg)](https://github.com/RamrattanN/speedtest-dashboard/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/RamrattanN/speedtest-dashboard?sort=semver)](https://github.com/RamrattanN/speedtest-dashboard/releases)

A local internet speed monitor with packaged macOS and Windows desktop
applications, plus a portable Python developer mode.  It periodically
collects ping, download, and upload results using the separately installed
official Ookla Speedtest CLI.  The Python `speedtest-cli` library remains
available only through an explicit compatibility-mode choice.
Results are stored locally in CSV files and displayed in a Streamlit dashboard.

![Speedtest Dashboard Screenshot](assets/dashboard_preview.png?v=2025-09-04-1)

## Features

- Configurable test interval, dashboard port, and data folder.
- Approximately 30 days of results in the main CSV.
- Up to 12 monthly archive files.
- Bar and line charts with previous-period comparison.
- Automatic 60-second display refresh plus an independent manual refresh.
- Timezone, theme, color, server, and date-window controls.
- Location-neutral server selection: automatic by default, with an optional
  saved city-or-region preference and regional failover candidates.
- Official-only production engine policy that prevents silent mixing of Ookla
  and Python measurements, plus visible collector health and setup guidance.
- Windows measurement isolation with a hard timeout, automatic recovery, and
  process-tree cleanup if a speed-test backend freezes.
- Unsigned macOS Intel and Apple silicon applications for
  users who do not use Terminal in everyday use.
- Unsigned Windows x64 installer with a native controller and Start menu entry.
- macOS developer launcher using an isolated local Python environment.
- Installable command-line package.
- Automated tests that do not perform real internet speed tests.

## Quick start on macOS

### Desktop application

The unsigned macOS Intel 1.1.0 application is distributed as
[Speedtest-Monitor-macOS-Intel-1.1.0.dmg](https://github.com/RamrattanN/speedtest-dashboard/releases/download/v1.1.0/Speedtest-Monitor-macOS-Intel-1.1.0.dmg).
Open the disk image, drag
**Speedtest Monitor** to **Applications**, then open the application.  It
includes Python and the required dependencies and does not require the
repository or VS Code.

Because the application is unsigned, macOS may block the first launch.  Select
**Done**, then use **System Settings > Privacy & Security > Open Anyway**.  The
disk image includes **Read Me First - macOS Security.txt** and the optional
**Allow and Open Speedtest Monitor.command** helper.  macOS may also block the
unsigned helper itself.  If that happens, select **Done**, approve the helper
with **Open Anyway** in Privacy & Security, and run it again.  The plain-text
instructions include the manual Terminal fallback.  This is a one-time
installation step.  Everyday operation uses the small controller window to
reopen the dashboard or quit the monitor safely.

See [macOS Desktop Packaging](docs/Mac-Desktop-Packaging.md) for build, test, and
distribution instructions.

An unsigned Apple silicon release is also produced as
[Speedtest-Monitor-macOS-Apple-Silicon-1.1.0.dmg](https://github.com/RamrattanN/speedtest-dashboard/releases/download/v1.1.0/Speedtest-Monitor-macOS-Apple-Silicon-1.1.0.dmg).
Its automated package and
dashboard smoke tests run on an ARM64 GitHub Actions runner, but it remains
unvalidated on a physical Apple silicon Mac.

### Developer launcher

Install Python 3.11 or newer, then clone the repository and run:

```bash
chmod +x RunSpeedTest.command
./RunSpeedTest.command
```

The dashboard opens at <http://localhost:8501>.  Results are stored in
`~/SpeedtestDashboard` by default.

Production measurements require the official Ookla Speedtest CLI, obtained
directly from [Ookla](https://www.speedtest.net/apps/cli).  The application
does not redistribute Ookla's executable.  After installing it, open
**Connection Overview > Measurement engine** to confirm detection or save its
full executable path.  Compatibility mode must be selected explicitly if the
Python engine is required temporarily.

See the [Mac Testing Guide](docs/Mac-Testing.md) for complete installation and
acceptance steps.  The [VS Code Setup Guide](docs/VS-Code-Setup-Mac.md) explains
how to work on the project without memorizing Terminal commands.

## Quick start on Windows

### Desktop application

Download
[Speedtest-Monitor-Windows-x64-1.1.0.exe](https://github.com/RamrattanN/speedtest-dashboard/releases/download/v1.1.0/Speedtest-Monitor-Windows-x64-1.1.0.exe),
then run it.  The per-user
installer adds **Speedtest Monitor** to the Start menu and does not require
Python or the repository.

Running the installer again offers **Repair** and **Uninstall completely**.
Uninstall removes the application, shortcuts, and logs while preserving the
measurement history in `%USERPROFILE%\SpeedtestDashboard`.

The application is unsigned.  If Microsoft Defender SmartScreen appears,
select **More info**, confirm that the file came from the project download,
then select **Run anyway**.  See
[Windows Desktop Packaging](docs/Windows-Desktop-Packaging.md) for installation,
testing, logs, and removal.

### Developer setup

Developers can install Python 3.11 or newer, clone the repository, run
`setup_venv.bat`, and start the installed command:

```bat
setup_venv.bat
.venv\Scripts\speedtest-dashboard.exe --interval 300 --port 8501
```

Results are stored in `%USERPROFILE%\SpeedtestDashboard` by default.

Install the official CLI directly from
[Ookla](https://www.speedtest.net/apps/cli).  If it is not on `PATH`, extract
it to `C:\Tools\OoklaSpeedtest\speedtest.exe` or save its full path under
**Connection Overview > Measurement engine**.  Production collection remains
paused until the official engine is detected.

Server selection remains automatic for every new installation.  If the
provider places your public IP in the wrong region, open **Test server
selection**, choose **Preferred city or region**, enter a city plus state,
province, or country, and save.  The next cycle calibrates matching servers.
Only that general area is stored locally.

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
├── setup_venv.bat            # Optional Windows developer setup helper
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

Separate release workflows build and smoke-test the unsigned macOS Intel and
Apple silicon disk images and the Windows x64 installer.  Each packaged
application is built on its target operating system and architecture because
PyInstaller builds for the system on which it runs.

## Documentation

- [Mac Testing Guide](docs/Mac-Testing.md)
- [macOS Desktop Packaging](docs/Mac-Desktop-Packaging.md)
- [Windows Desktop Packaging](docs/Windows-Desktop-Packaging.md)
- [VS Code Setup on Mac](docs/VS-Code-Setup-Mac.md)
- [Getting Started](docs/wiki/Getting-Started.md)
- [Configuration](docs/wiki/Configuration.md)
- [Measurement Engine](docs/wiki/Measurement-Engine.md)
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
