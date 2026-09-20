# macOS Intel Pilot Packaging

## Purpose

The private pilot packages Speedtest Monitor as a double-clickable macOS
application.  Pilot users do not need Python, VS Code, Terminal, or a copy of
the repository.

The application starts two local services:

- the collector, which normally performs a speed test every five minutes;
- the Streamlit dashboard, which is available only on the user's Mac.

Results remain in `~/SpeedtestDashboard`.  Closing the browser tab does not
stop collection.  Quitting the controller stops both local services.

## Build requirements

- An Intel Mac, or the GitHub Actions `macos-15-intel` runner.
- Python 3.12.
- The repository checked out at the intended pilot commit.

The current pilot is Intel-only because it is being validated on an Intel
MacBook Pro.  Apple silicon packaging is a later release task.

## Local build

From the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test,macos-pilot]'
.venv/bin/python -m pytest -q
.venv/bin/python -m PyInstaller --version
bash scripts/build_macos_pilot.sh
```

The resulting disk image is:

```text
dist/Speedtest-Monitor-macOS-Intel-pilot-3.dmg
```

## GitHub Actions build

The pilot workflow runs automatically when a pull request changes the packaging
or application files.  Download the artifact from that workflow run for branch
acceptance testing.

After the workflow is present on the repository's default branch, it can also
be run manually:

1. Open **Actions** in GitHub.
2. Select **Build macOS Intel pilot**.
3. Select **Run workflow**.
4. Download the `Speedtest-Monitor-macOS-Intel-pilot-3` artifact after the build
   completes.

The artifact expires after 14 days and is intended only for controlled pilot
testing.

## Install and first launch

1. Quit any running copy of **Speedtest Monitor**.
2. Open `Speedtest-Monitor-macOS-Intel-pilot-3.dmg`.
3. Drag **Speedtest Monitor** to **Applications** and choose **Replace** if an
   older pilot is installed.
4. Try opening the application.  If macOS blocks the unsigned pilot, open
   **System Settings > Privacy & Security** and use **Open Anyway** when that
   option is available.
5. If macOS still blocks it, remove the downloaded-file quarantine in Terminal:

   ```bash
   sudo xattr -dr com.apple.quarantine "/Applications/Speedtest Monitor.app"
   ```

   Enter the Mac login password when prompted.  Terminal does not display the
   password while it is typed.
6. Verify that the installed application is Pilot 3:

   ```bash
   /usr/libexec/PlistBuddy -c "Print :CFBundleShortVersionString" \
     "/Applications/Speedtest Monitor.app/Contents/Info.plist"
   ```

   The expected value is `0.2.0-pilot.3`.
7. Open **Speedtest Monitor** from Applications and keep its controller open
   while monitoring should continue.

## Pilot acceptance checks

- The application opens without Terminal.
- The controller changes from starting to running.
- The browser opens the dashboard automatically.
- **Open Dashboard** reopens a closed browser tab.
- A first result appears and is written to `~/SpeedtestDashboard`.
- The dashboard refreshes without manual browser refresh.
- **Quit Monitor** stops both the dashboard and collector.
- Existing CSV results remain available after reopening the application.
- The controller footer identifies the build as **Pilot 3**.

## Pilot troubleshooting

### Browser reports Not Found or cannot connect

Quit the controller, stop any remaining pilot process, and confirm that the
default port is free before reopening the application:

```bash
pkill -f '/Applications/Speedtest Monitor.app/Contents/MacOS/Speedtest Monitor' || true
lsof -nP -iTCP:8501 -sTCP:LISTEN
```

The `lsof` command should display nothing.  Pilot 3 serves the complete
Streamlit application on its selected local port and uses the controller's
**Open Dashboard** button to open the correct address.

### Controller remains on Starting

Review the last entries in the local application log:

```bash
tail -100 "$HOME/Library/Logs/Ramrattan Speedtest Monitor/monitor.log"
```

The log should contain `Speedtest Monitor build 0.2.0-pilot.3 starting` and a
local Streamlit server address.  Preserve the log output when reporting a
pilot defect.

## Known pilot limitations

- The disk image is unsigned and not notarized.
- GitHub's downloaded artifact receives macOS quarantine metadata.  Some pilot
  testers must use **Open Anyway** or the documented `xattr` command after
  copying the app.
- The first build supports Intel Macs only.
- The controller must remain open while collection continues.
- Automatic launch at login is not included.
- Automatic application updates are not included.

Code signing, notarization, Apple silicon support, launch-at-login, and a
menu-bar-only controller belong to the public-release phase.
