# macOS Desktop Packaging

Version 1.0.0 packages Speedtest Monitor as double-clickable Intel and Apple
silicon macOS applications.  Users do not need Python, Git, VS Code, Terminal,
or a repository copy for everyday operation.

## Current artifact

- Intel artifact: `Speedtest-Monitor-macOS-Intel-1.0.0`
- Intel disk image: `Speedtest-Monitor-macOS-Intel-1.0.0.dmg`
- Apple silicon artifact: `Speedtest-Monitor-macOS-Apple-Silicon-1.0.0`
- Apple silicon disk image: `Speedtest-Monitor-macOS-Apple-Silicon-1.0.0.dmg`
- Application version: `1.0.0`
- Architectures: Intel x86_64 and Apple silicon ARM64
- Signing status: unsigned and not notarized

The Intel build has been manually validated.  The Apple silicon release runs
its automated package and dashboard smoke tests on an ARM64 runner and still
awaits testing on a physical Apple silicon Mac.

## Build locally

Use a Mac of the target architecture with Python 3.11 or newer and Xcode
command-line tools:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test,macos-release]'
.venv/bin/python -m pytest -q
bash scripts/build_macos_release.sh
```

The build script detects `x86_64` or `arm64` and uses the matching package name.
The **Build macOS releases** workflow builds both architectures natively and
verifies each packaged dashboard route before uploading artifacts for 14 days.

## Install and update

1. Open the disk image.
2. Drag **Speedtest Monitor** to **Applications**.
3. Choose **Replace** when updating an existing installation.
4. Open the application.  If macOS blocks it, use **System Settings > Privacy &
   Security > Open Anyway**.
5. If the application is still blocked, double-click **Allow and Open Speedtest
   Monitor.command** in the disk image.  Review the explanation, enter the Mac
   administrator password when prompted, and allow the helper to open the app.

The helper runs only these commands against the installed Speedtest Monitor app:

```bash
sudo xattr -dr com.apple.quarantine "/Applications/Speedtest Monitor.app"
open "/Applications/Speedtest Monitor.app"
```

The same commands can be run manually in Terminal.  Only use the security
override for an artifact obtained from the project.

## Acceptance checks

- The controller footer reports version 1.0.0.
- **Open Dashboard** opens the controller-selected address.
- A completed test appears in `~/SpeedtestDashboard/speedtest_results.csv`.
- The dashboard displays the latest recorded result.
- **Refresh now** works with automatic refresh either on or off.
- **Quit Monitor** stops the local server.

## Logs and removal

Logs are stored in
`~/Library/Logs/Ramrattan Speedtest Monitor/monitor.log`.  To remove the
application, quit it and move `/Applications/Speedtest Monitor.app` to Trash.
Measurement history in `~/SpeedtestDashboard` is separate and is not removed
automatically.
