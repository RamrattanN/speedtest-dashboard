# Speedtest Monitor Wiki

Speedtest Monitor records ping, download, and upload measurements and presents
them in a local Streamlit dashboard.  Results stay on the computer in CSV files.

## Current release

Version 1.1.0 is available as unsigned **macOS Intel**, **macOS Apple silicon**,
and **Windows x64** desktop applications.  The Apple silicon release passes
automated ARM64 validation but still awaits physical-device testing.  The applications
include their own Python runtime and do not require the repository, VS Code, or
a command line for everyday use.

Download the installers from the
[Speedtest Monitor 1.1.0 release](https://github.com/RamrattanN/speedtest-dashboard/releases/tag/v1.1.0).

1. Install **Speedtest Monitor** in Applications on macOS or with the per-user
   Windows installer.
2. On macOS, follow **Read Me First - macOS Security.txt** if Gatekeeper blocks
   the unsigned app or its optional approval helper.
3. Open the application and keep its controller running.
4. Install the official CLI directly from
   [Ookla](https://www.speedtest.net/apps/cli), then confirm it under
   **Connection Overview > Measurement engine**.
5. Use **Open Dashboard** to return to the dashboard at any time.
6. Use **Quit Monitor** to stop both collection and the dashboard safely.

The collector normally records a measurement every five minutes.  The open
dashboard checks for new results every 60 seconds.  Select **Run speed test**
to request a new measurement, or **Refresh dashboard** to reload results that
have already been recorded.

Server selection is automatic by default on every computer.  If public-IP
geolocation chooses a distant region, use **Test server selection** to save a
preferred city or region.  The monitor calibrates several matching servers and
retains automatic fallback without storing a street address.

Source-based developer operation remains available through the macOS launcher
or the installed `speedtest-dashboard` command.  The legacy PowerShell and
Windows batch launchers have been retired.

## Documentation

- [Getting Started](Getting-Started.md)
- [Configuration](Configuration.md)
- [Measurement Engine](Measurement-Engine.md)
- [Running the Dashboard](Running-the-Dashboard.md)
- [Customization](Customization.md)
- [Troubleshooting](Troubleshooting.md)
- [Roadmap](Roadmap.md)
- [Credits](Credits.md)

## Defaults

- Collection interval: five minutes
- Display refresh: 60 seconds
- Data folder: `~/SpeedtestDashboard` on macOS or
  `%USERPROFILE%\SpeedtestDashboard` on Windows
- Dashboard address: selected and opened by the controller
- Measurement retention: rolling 365 days in the main CSV and monthly archives
