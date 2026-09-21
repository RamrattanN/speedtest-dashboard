# Troubleshooting

## macOS blocks the application

Version 0.2.0 is unsigned and not notarized.  First try **System Settings >
Privacy & Security > Open Anyway**.  If the application remains blocked, run:

```bash
sudo xattr -dr com.apple.quarantine "/Applications/Speedtest Monitor.app"
```

Enter the Mac login password when prompted.  Terminal does not display the
password while it is typed.

## Windows SmartScreen blocks the installer

Version 0.2.0 is unsigned.  If the installer came from the project download,
select **More info**, verify the filename, then select **Run anyway**.  Do not
bypass SmartScreen for an installer received from another source.

## Dashboard does not open

- Keep the controller open and wait for **The monitor is running**.
- Select **Open Dashboard** in the controller.
- Do not type `localhost:3000`.  The controller opens the correct local port.

On macOS, if the browser reports **Not Found**, quit the controller and check
for a stale process:

```bash
pkill -f '/Applications/Speedtest Monitor.app/Contents/MacOS/Speedtest Monitor' || true
lsof -nP -iTCP:8501 -sTCP:LISTEN
```

Reopen the application after `lsof` displays nothing.

## Dashboard data appears stale

The collector and dashboard use separate schedules.  A speed test normally
finishes about every five minutes, while the open dashboard checks the CSV every
60 seconds.

1. Compare the **Recorded** card with the last CSV row.
2. Select **Refresh now**.  It remains available when automatic refresh is on.
3. If needed, press **F5** once to confirm that the browser still has a live
   connection to the local dashboard.

On Windows, inspect recent rows with PowerShell:

```powershell
Import-Csv "$env:USERPROFILE\SpeedtestDashboard\speedtest_results.csv" |
  Select-Object -Last 10 timestamp, download_mbps, upload_mbps, ping_ms, server_name |
  Format-Table -AutoSize
```

If the CSV has new rows but the page does not, the collector is healthy and the
problem is limited to display refresh.

## Review application logs

On macOS:

```bash
tail -100 "$HOME/Library/Logs/Ramrattan Speedtest Monitor/monitor.log"
```

On Windows:

```powershell
Get-Content "$env:LOCALAPPDATA\Ramrattan Speedtest Monitor\Logs\monitor.log" -Tail 100
```

Version 0.2.0 configures Windows log output as UTF-8 and line-buffered so each
completed result is visible promptly.  Repeated browser connection-reset lines
do not by themselves indicate a collector failure.

## Collector does not write data

- Wait for the first speed test to complete.
- Confirm that the data folder is writable.
- Confirm that `speedtest_results.csv` is not locked by another application.
- An Ookla warning is not necessarily fatal because the monitor can use the
  Python speed-test fallback.

## Information to capture

Record the application version, operating system and processor type, the exact
symptom, the last ten CSV rows, and the last 100 log lines.  State whether the
problem affected the controller, collector, dashboard, or all three.
