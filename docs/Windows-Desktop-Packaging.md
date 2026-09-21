# Windows x64 Desktop Packaging

Version 1.1.0 packages Speedtest Monitor as a normal per-user Windows installer.
Users do not need Python, Git, VS Code, a command line, or a repository copy for
everyday operation.

## Current artifact

- GitHub release installer: `Speedtest-Monitor-Windows-x64-1.1.0.exe`
- Application version: `1.1.0`
- Architecture: Windows x64
- Signing status: unsigned

## Build locally

Use Windows x64 with Python 3.11 or newer, PowerShell, and Inno Setup 6:

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install -e ".[test,windows-release]"
.venv\Scripts\python -m pytest -q
.\scripts\build_windows_release.ps1
```

The installer is written to `dist\Speedtest-Monitor-Windows-x64-1.1.0.exe`.
The **Build Windows x64 release** workflow builds, installs, repairs, uninstalls,
and smoke-tests the packaged application before uploading the artifact for 14
days.

## Install, repair, and uninstall

Run the installer as the current user.  If SmartScreen appears, select **More
info**, verify the download source, then select **Run anyway**.

Install the official Speedtest CLI directly from
`https://www.speedtest.net/apps/cli`.  Extracting it to
`C:\Tools\OoklaSpeedtest\speedtest.exe` allows automatic detection.  Another
location can be saved under **Connection Overview > Measurement engine**.

Running the installer again presents two maintenance choices:

- **Repair** reinstalls the current application files and shortcuts.
- **Uninstall completely** removes the application, shortcuts, and logs.

Measurement history in `%USERPROFILE%\SpeedtestDashboard` is preserved by
uninstall.  It can be removed separately only when the user no longer wants it.

## Acceptance checks

- The controller footer reports version 1.1.0.
- **Open Dashboard** opens the controller-selected address.
- At least two completed tests appear in
  `%USERPROFILE%\SpeedtestDashboard\speedtest_results.csv`.
- The Windows log shows each completed result promptly.
- A test that exceeds three minutes is terminated and a later cycle still runs.
- Quit Monitor stops the dashboard service and any active measurement child.
- Automatic server selection can be changed to a saved city-or-region
  preference without reinstalling.
- The header refresh icon immediately reloads dashboard data.
- The header **Run speed test** action requests and records one new
  timeout-protected measurement without overlapping an active test.
- A repeated application launch reports that the monitor is already running
  and does not create another service or collector.
- The chart-type selector appears directly below the chart.
- Repair preserves the application and measurement history.
- Uninstall removes the application but preserves measurement history.
- The controller reports setup required if the official Ookla CLI is absent.
- Compatibility mode must be selected explicitly before the Python engine can
  be used.

## Logs

The application log is stored at:

```text
%LOCALAPPDATA%\Ramrattan Speedtest Monitor\Logs\monitor.log
```

Version 1.1.0 uses UTF-8, line-buffered output.  A missing official CLI pauses
production collection without stopping the controller or dashboard.
Each measurement runs in a disposable child process.  Expected supervisor
messages include **Measurement cycle started**, **Measurement cycle completed**,
and **Next measurement cycle**.  A timeout message means that one frozen test
was terminated and does not mean the monitor itself stopped.
