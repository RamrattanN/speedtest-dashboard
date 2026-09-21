# Troubleshooting

## macOS blocks the application

Version 1.1.0 is unsigned and not notarized.  When macOS blocks Speedtest
Monitor, select **Done**, open **System Settings > Privacy & Security**, scroll
to **Security**, and select **Open Anyway** beside the Speedtest Monitor
message.  Authenticate and confirm **Open**.

The disk image includes **Read Me First - macOS Security.txt** and the optional
**Allow and Open Speedtest Monitor.command** helper.  The helper requests
confirmation and the Mac administrator password, removes quarantine only from
the installed Speedtest Monitor application, and opens it.

The helper is also unsigned, so macOS may block it before it can run.  If that
happens, select **Done**, return to **System Settings > Privacy & Security >
Security**, select **Open Anyway** beside the helper message, authenticate, and
run the helper again.  An unsigned helper cannot approve itself before macOS
allows it to execute.

The same steps can be completed manually in Terminal:

```bash
sudo xattr -dr com.apple.quarantine "/Applications/Speedtest Monitor.app"
open "/Applications/Speedtest Monitor.app"
```

Enter the Mac login password when prompted.  Terminal does not display the
password while it is typed.

## Windows SmartScreen blocks the installer

Version 1.1.0 is unsigned.  If the installer came from the project download,
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
2. Turn off **Refresh display every 60s**, then select **Refresh now**.
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

Version 1.1.0 configures Windows log output as UTF-8 and line-buffered so each
completed result is visible promptly.  Repeated browser connection-reset lines
do not by themselves indicate a collector failure.

Version 1.1.0 also runs each Windows measurement in a separate child process.
The log records the cycle start, completion, failure, timeout, and next retry.
If a backend call exceeds three minutes, the monitor terminates that process
tree and continues on schedule instead of leaving the controller locked.

## Collector does not write data

- Wait for the first speed test to complete.
- Confirm that the data folder is writable.
- Confirm that `speedtest_results.csv` is not locked by another application.
- Open **Measurement engine** and confirm that the official Ookla CLI is
  detected.  Production collection intentionally pauses when it is missing.
- Download the CLI only from [Ookla](https://www.speedtest.net/apps/cli), or
  save the full executable path in the dashboard.
- Use Compatibility mode only as an explicit temporary exception.  It permits
  the Python engine and creates results that may not be directly comparable to
  official Ookla samples.

## Tests use a distant server

Automatic selection uses public-IP geolocation.  ISP records, carrier-grade
NAT, VPNs, proxies, and security routing can make that location differ from the
computer's physical location.

Open **Test server selection**, choose **Preferred city or region**, enter a
city plus state, province, or country, and save.  The next cycle calibrates
matching regional servers.  If calibration fails, the dashboard shows the
reason and the collector uses automatic selection for that cycle.  Save the
preference again to retry, or return to **Automatic**.

Do not select a remote server merely because it reports a higher peak speed.
Use a stable nearby region so ping and throughput remain comparable over time.

## Information to capture

Record the application version, operating system and processor type, the exact
symptom, the last ten CSV rows, and the last 100 log lines.  State whether the
problem affected the controller, collector, dashboard, or all three.
