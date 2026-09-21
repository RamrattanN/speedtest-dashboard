# Speedtest Monitor Wiki

Speedtest Monitor records ping, download, and upload measurements and presents
them in a local Streamlit dashboard.  Results stay on the computer in CSV files.

## Current release

Version 1.0.0 is available as unsigned **macOS Intel**, **macOS Apple silicon**,
and **Windows x64** desktop applications.  The Apple silicon release passes
automated ARM64 validation but still awaits physical-device testing.  The applications
include their own Python runtime and do not require the repository, VS Code, or
a command line for everyday use.

1. Install **Speedtest Monitor** in Applications on macOS or with the per-user
   Windows installer.
2. Open the application and keep its controller running.
3. Use **Open Dashboard** to return to the dashboard at any time.
4. Use **Quit Monitor** to stop both collection and the dashboard safely.

The collector normally records a measurement every five minutes.  The open
dashboard checks for new results every 60 seconds.  Turn off automatic refresh
to enable **Refresh now** for an immediate reload.

Source-based developer operation remains available through the macOS launcher
or the installed `speedtest-dashboard` command.  The legacy PowerShell and
Windows batch launchers have been retired.

## Documentation

- [Getting Started](Getting-Started.md)
- [Configuration](Configuration.md)
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
- Main CSV retention: approximately 30 days
- Monthly archives: up to 12 files
