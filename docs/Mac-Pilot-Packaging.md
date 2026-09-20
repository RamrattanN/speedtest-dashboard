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
dist/Speedtest-Monitor-macOS-Intel-pilot.dmg
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
4. Download the `Speedtest-Monitor-macOS-Intel-pilot` artifact after the build
   completes.

The artifact expires after 14 days and is intended only for controlled pilot
testing.

## Install and first launch

1. Open the downloaded disk image.
2. Drag **Speedtest Monitor** to **Applications**.
3. Control-click the application and select **Open**.
4. Confirm **Open** when macOS displays the unsigned-application warning.
5. Keep the controller open while monitoring should continue.

## Pilot acceptance checks

- The application opens without Terminal.
- The controller changes from starting to running.
- The browser opens the dashboard automatically.
- **Open Dashboard** reopens a closed browser tab.
- A first result appears and is written to `~/SpeedtestDashboard`.
- The dashboard refreshes without manual browser refresh.
- **Quit Monitor** stops both the dashboard and collector.
- Existing CSV results remain available after reopening the application.

## Known pilot limitations

- The disk image is unsigned and not notarized.
- The first build supports Intel Macs only.
- The controller must remain open while collection continues.
- Automatic launch at login is not included.
- Automatic application updates are not included.

Code signing, notarization, Apple silicon support, launch-at-login, and a
menu-bar-only controller belong to the public-release phase.
