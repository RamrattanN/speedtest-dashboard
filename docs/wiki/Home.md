# Speedtest Monitor Wiki

Speedtest Monitor records ping, download, and upload measurements and presents
them in a local Streamlit dashboard.  Results stay on the computer in CSV files.

![Current Speedtest Monitor dashboard](https://raw.githubusercontent.com/RamrattanN/speedtest-dashboard/main/assets/dashboard_preview.png)

## Current release

Version 1.0.0 is the current published production release.  Unsigned **macOS
Intel**, **macOS Apple silicon**, and **Windows x64** installers are available
from the stable latest-release page.  The applications include their own
Python runtime and do not require the repository, VS Code, or a command line
for everyday use.

Download the installers from the
[latest Speedtest Monitor release](https://github.com/RamrattanN/speedtest-dashboard/releases/latest).

Version 1.1.0 is the current QA candidate on `main`.  It adds atomic one-shot
measurements, upgrade-safe duplicate-instance protection, one-year rolling
retention, measurement-history controls, improved chart behavior, and expanded
engine and server configuration.  It will replace 1.0.0 on the release page only after
hands-on production approval.  The Apple silicon package passes automated ARM64
validation but still awaits testing on a physical Apple silicon Mac.

Unless a page explicitly says otherwise, this wiki documents the version 1.1.0
QA candidate currently on `main`.  Temporary QA artifacts are shared directly
with testers and are not presented as production downloads.

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

Each **Run speed test** request is consumed once by the existing collector.  It
does not create another timer, service, or recurring schedule.

Server selection is automatic by default on every computer.  If public-IP
geolocation chooses a distant region, use **Test server selection** to save a
preferred city or region.  The monitor calibrates several matching servers and
retains automatic fallback without storing a street address.

Source-based developer operation remains available through the macOS launcher
or the installed `speedtest-dashboard` command.  The legacy PowerShell and
Windows batch launchers have been retired.

## Documentation

- [Getting Started](https://github.com/RamrattanN/speedtest-dashboard/wiki/Getting-Started)
- [Configuration](https://github.com/RamrattanN/speedtest-dashboard/wiki/Configuration)
- [Measurement Engine](https://github.com/RamrattanN/speedtest-dashboard/wiki/Measurement-Engine)
- [Running the Dashboard](https://github.com/RamrattanN/speedtest-dashboard/wiki/Running-the-Dashboard)
- [Customization](https://github.com/RamrattanN/speedtest-dashboard/wiki/Customization)
- [Troubleshooting](https://github.com/RamrattanN/speedtest-dashboard/wiki/Troubleshooting)
- [Roadmap](https://github.com/RamrattanN/speedtest-dashboard/wiki/Roadmap)
- [Credits](https://github.com/RamrattanN/speedtest-dashboard/wiki/Credits)

## Defaults

- Collection interval: five minutes
- Display refresh: 60 seconds
- Data folder: `~/SpeedtestDashboard` on macOS or
  `%USERPROFILE%\SpeedtestDashboard` on Windows
- Dashboard address: selected and opened by the controller
- Measurement retention: rolling 365 days in the main CSV and monthly archives
