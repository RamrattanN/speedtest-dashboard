# macOS Intel Desktop Packaging

Version 0.2.0 packages Speedtest Monitor as a double-clickable Intel macOS
application.  Users do not need Python, Git, VS Code, Terminal, or a repository
copy for everyday operation.

## Current artifact

- GitHub Actions artifact: `Speedtest-Monitor-macOS-Intel-0.2.0`
- Disk image: `Speedtest-Monitor-macOS-Intel-0.2.0.dmg`
- Application version: `0.2.0`
- Architecture: Intel x86_64
- Signing status: unsigned and not notarized

## Build locally

Use an Intel Mac with Python 3.11 or newer and Xcode command-line tools:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test,macos-release]'
.venv/bin/python -m pytest -q
bash scripts/build_macos_release.sh
```

The disk image is written to `dist/Speedtest-Monitor-macOS-Intel-0.2.0.dmg`.
The **Build macOS Intel release** workflow performs the same build and verifies
the packaged dashboard route before uploading the artifact for 14 days.

## Install and update

1. Open the disk image.
2. Drag **Speedtest Monitor** to **Applications**.
3. Choose **Replace** when updating an existing installation.
4. Open the application.  If macOS blocks it, use **System Settings > Privacy &
   Security > Open Anyway**.
5. If the application is still blocked, run:

```bash
sudo xattr -dr com.apple.quarantine "/Applications/Speedtest Monitor.app"
```

Only use the security override for an artifact obtained from the project.

## Acceptance checks

- The controller footer reports version 0.2.0.
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
