# macOS Desktop Packaging

Version 1.1.0 packages Speedtest Monitor as double-clickable Intel and Apple
silicon macOS applications.  Users do not need Python, Git, VS Code, Terminal,
or a repository copy for everyday operation.

## Current artifact

- Intel artifact: `Speedtest-Monitor-macOS-Intel-1.1.0`
- Intel disk image: `Speedtest-Monitor-macOS-Intel-1.1.0.dmg`
- Apple silicon artifact: `Speedtest-Monitor-macOS-Apple-Silicon-1.1.0`
- Apple silicon disk image: `Speedtest-Monitor-macOS-Apple-Silicon-1.1.0.dmg`
- Application version: `1.1.0`
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
4. Open the application.  If macOS blocks it, select **Done**, open **System
   Settings > Privacy & Security**, scroll to **Security**, and select **Open
   Anyway** beside the Speedtest Monitor message.  Authenticate and confirm
   **Open**.
5. If needed, open **Read Me First - macOS Security.txt** in the disk image and
   use the optional **Allow and Open Speedtest Monitor.command** helper.
6. If macOS blocks the helper itself, select **Done**, return to **System
   Settings > Privacy & Security > Security**, select **Open Anyway** beside the
   helper message, authenticate, and run the helper again.
7. Install the official Speedtest CLI directly from
   `https://www.speedtest.net/apps/cli`.  Confirm it under **Connection
   Overview > Measurement engine**, or save its full executable path there.

The helper runs only these commands against the installed Speedtest Monitor app:

```bash
sudo xattr -dr com.apple.quarantine "/Applications/Speedtest Monitor.app"
open "/Applications/Speedtest Monitor.app"
```

The same commands can be run manually in Terminal.  The helper cannot approve
itself before macOS allows it to run, which is why the disk image includes a
plain-text instruction file.  Only use the security override for an artifact
obtained from the official project release.

## Acceptance checks

- The controller footer reports version 1.1.0.
- **Open Dashboard** opens the controller-selected address.
- A completed test appears in `~/SpeedtestDashboard/speedtest_results.csv`.
- The dashboard displays the latest recorded result.
- The header refresh icon immediately reloads dashboard data.
- The header **Run speed test** action requests and records one new
  measurement without overlapping an active test.
- The chart-type selector appears directly below the chart.
- **Quit Monitor** stops the local server.
- Automatic server selection remains the default.  A preferred city or region
  can be saved from Test server selection and is applied on the next cycle.
- The controller reports setup required when the official Ookla CLI is absent.
- Compatibility mode uses the Python engine only after an explicit opt-in.

## Logs and removal

Logs are stored in
`~/Library/Logs/Ramrattan Speedtest Monitor/monitor.log`.  To remove the
application, quit it and move `/Applications/Speedtest Monitor.app` to Trash.
Measurement history in `~/SpeedtestDashboard` is separate and is not removed
automatically.
