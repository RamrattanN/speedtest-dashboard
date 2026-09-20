# Troubleshooting

## macOS blocks the private pilot

Pilot 3 is unsigned and not notarized.  First try **System Settings > Privacy &
Security > Open Anyway**.  If the application remains blocked, run:

```bash
sudo xattr -dr com.apple.quarantine "/Applications/Speedtest Monitor.app"
```

Enter the Mac login password when prompted.  Terminal does not display the
password while it is typed.

## Dashboard does not open

- Keep the Speedtest Monitor controller open.
- Wait until it reports **The monitor is running**.
- Select **Open Dashboard** in the controller.
- Do not type `localhost:3000`.  Pilot 3 serves the dashboard on its selected
  local port.

If the browser reports **Not Found**, quit the controller, stop a stale pilot
process, and confirm that the preferred port is free:

```bash
pkill -f '/Applications/Speedtest Monitor.app/Contents/MacOS/Speedtest Monitor' || true
lsof -nP -iTCP:8501 -sTCP:LISTEN
```

Reopen Speedtest Monitor after the `lsof` command displays nothing.

On Windows, keep the controller open until it says **The monitor is running**,
then select **Open Dashboard**.  Do not browse to `localhost:3000`.

## Windows SmartScreen blocks the private pilot

Windows Pilot 1 is unsigned.  If the installer came from the controlled pilot
download, select **More info**, verify the Speedtest Monitor filename, then
select **Run anyway**.  Do not bypass SmartScreen for an installer received
from any other source.

## Controller remains on Starting

Review the application log:

```bash
tail -100 "$HOME/Library/Logs/Ramrattan Speedtest Monitor/monitor.log"
```

Pilot 3 should log `Speedtest Monitor build 0.2.0-pilot.3 starting`.

On Windows, review
`%LOCALAPPDATA%\Ramrattan Speedtest Monitor\Logs\monitor.log`.  The controller
footer should identify **Windows Pilot 1**.

## Collector does not write data

- Wait for the first speed test to complete.
- Confirm that `~/SpeedtestDashboard` is writable.
- Confirm that `speedtest_results.csv` is not locked by another application.
- An Ookla warning is not necessarily fatal because the monitor can use the
  Python speed-test fallback.

## Developer environment errors

On macOS, recreate the local environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[test]"
```

On Windows, run `setup_venv.bat` and then use the installed command documented
in [Getting Started](Getting-Started.md).

## Information to capture

Record the pilot number, operating system and processor type, the exact
symptom, and the last 100 lines of `monitor.log`.  State whether the problem
affected the controller, collector, dashboard, or all three.
