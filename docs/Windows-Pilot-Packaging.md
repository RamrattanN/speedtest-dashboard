# Windows x64 Pilot Packaging

## Purpose

Windows Pilot 1 packages Speedtest Monitor as a normal per-user installer.
Pilot users do not need Python, Git, VS Code, Terminal, or a repository copy.
The installer adds **Speedtest Monitor** to the Windows Start menu and can be
removed from **Settings > Apps > Installed apps**.

The application stores results in `%USERPROFILE%\SpeedtestDashboard` and makes
the dashboard available only on the user's PC.  Closing the browser tab does
not stop collection.  Selecting **Quit Monitor** in the controller stops both
the collector and dashboard.

## Build requirements

- 64-bit Windows 10 or Windows 11.
- Python 3.12.
- Inno Setup 6.
- The repository checked out at the intended pilot commit.

## Local build

From PowerShell in the repository root:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -e ".[test,windows-pilot]"
.venv\Scripts\python -m pytest -q
.\scripts\build_windows_pilot.ps1
```

The resulting installer is:

```text
dist\Speedtest-Monitor-Windows-x64-pilot-1.exe
```

## GitHub Actions build

The **Build Windows x64 pilot** workflow builds the app on Windows, installs
the finished installer into a temporary user folder, checks its embedded Pilot
1 version, starts the installed application, and verifies the dashboard route.
Download the `Speedtest-Monitor-Windows-x64-pilot-1` artifact from a successful
workflow run.  The artifact expires after 14 days and is intended for
controlled testing.

## Install and first launch

1. Download and unzip the GitHub Actions artifact.
2. Run `Speedtest-Monitor-Windows-x64-pilot-1.exe`.
3. Because the private pilot is unsigned, Microsoft Defender SmartScreen may
   appear.  Select **More info**, verify that the application is **Speedtest
   Monitor**, then select **Run anyway** only when the installer came from the
   controlled pilot link.
4. Complete the installer and open **Speedtest Monitor** from the Start menu.
5. Keep the controller open while monitoring should continue.

## Pilot acceptance checks

- Installation completes without Python or developer tools.
- The Start menu contains **Speedtest Monitor**.
- The controller identifies the application as **Windows Pilot 1**.
- The controller changes from starting to running.
- The browser opens the dashboard automatically.
- **Open Dashboard** reopens a closed browser tab.
- A first result appears in `%USERPROFILE%\SpeedtestDashboard`.
- The dashboard refreshes without manual browser refresh.
- **Quit Monitor** stops the collector and dashboard.
- Uninstalling from Installed apps removes the application.
- Existing CSV results remain after uninstalling or upgrading.

## Troubleshooting

If the controller reports that the monitor stopped unexpectedly, inspect:

```text
%LOCALAPPDATA%\Ramrattan Speedtest Monitor\Logs\monitor.log
```

If the browser cannot connect, keep the controller open and wait until it says
**The monitor is running**, then select **Open Dashboard**.  Do not use
`localhost:3000`; the controller opens the correct local port.

## Known pilot limitations

- The installer and application are unsigned.  SmartScreen may require manual
  approval on first installation.
- The first Windows package supports x64 PCs only.
- The controller must remain open while collection continues.
- Automatic launch at sign-in and automatic updates are not included.

Code signing can be added later without publishing through Microsoft Store.
