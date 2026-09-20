# Speedtest Monitor Wiki

Speedtest Monitor records ping, download, and upload measurements and presents
them in a local Streamlit dashboard.  Results stay on the computer in CSV files.

## Current release path

The current downloadable release is the unsigned **macOS Intel Pilot 3**.  It
includes its own Python runtime and does not require the repository, VS Code, or
Terminal for everyday use.

1. Install **Speedtest Monitor** in Applications.
2. Open the application and keep its controller running.
3. Use **Open Dashboard** to return to the dashboard at any time.
4. Use **Quit Monitor** to stop both collection and the dashboard safely.

The collector normally records a measurement every five minutes.  The open
dashboard checks for new results every 60 seconds.

Source-based developer operation remains available through the macOS launcher
or the installed `speedtest-dashboard` command.  The legacy PowerShell and
Windows batch launchers have been retired.  A Windows desktop package is not
part of Pilot 3.

## Documentation

- [Getting Started](Getting-Started.md)
- [Configuration](Configuration.md)
- [Running the Dashboard](Running-the-Dashboard.md)
- [Customization](Customization.md)
- [Troubleshooting](Troubleshooting.md)
- [Roadmap](Roadmap.md)
- [Credits](Credits.md)

## Defaults

- Collection interval: five minutes in the desktop pilot
- Display refresh: 60 seconds
- Data folder: `~/SpeedtestDashboard`
- Dashboard address: selected and opened by the controller
- Main CSV retention: approximately 30 days
- Monthly archives: up to 12 files
