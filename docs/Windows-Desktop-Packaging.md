# Windows x64 Desktop Packaging

Version 1.0.0 packages Speedtest Monitor as a normal per-user Windows installer.
Users do not need Python, Git, VS Code, a command line, or a repository copy for
everyday operation.

## Current artifact

- GitHub Actions artifact: `Speedtest-Monitor-Windows-x64-1.0.0`
- Installer: `Speedtest-Monitor-Windows-x64-1.0.0.exe`
- Application version: `1.0.0`
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

The installer is written to `dist\Speedtest-Monitor-Windows-x64-1.0.0.exe`.
The **Build Windows x64 release** workflow builds, installs, repairs, uninstalls,
and smoke-tests the packaged application before uploading the artifact for 14
days.

## Install, repair, and uninstall

Run the installer as the current user.  If SmartScreen appears, select **More
info**, verify the download source, then select **Run anyway**.

Running the installer again presents two maintenance choices:

- **Repair** reinstalls the current application files and shortcuts.
- **Uninstall completely** removes the application, shortcuts, and logs.

Measurement history in `%USERPROFILE%\SpeedtestDashboard` is preserved by
uninstall.  It can be removed separately only when the user no longer wants it.

## Acceptance checks

- The controller footer reports version 1.0.0.
- **Open Dashboard** opens the controller-selected address.
- At least two completed tests appear in
  `%USERPROFILE%\SpeedtestDashboard\speedtest_results.csv`.
- The Windows log shows each completed result promptly.
- **Refresh now** becomes available after automatic refresh is turned off.
- Repair preserves the application and measurement history.
- Uninstall removes the application but preserves measurement history.

## Logs

The application log is stored at:

```text
%LOCALAPPDATA%\Ramrattan Speedtest Monitor\Logs\monitor.log
```

Version 1.0.0 uses UTF-8, line-buffered output.  An Ookla CLI warning is not
necessarily fatal because the Python speed-test fallback can record results.
