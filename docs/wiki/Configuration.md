# Configuration

The collector and dashboard share one data directory and can be configured from
the combined launcher.

## Test interval

The default is 120 seconds.  Examples:

```bash
./RunSpeedTest.command --interval 300
speedtest-dashboard --interval 300
```

```powershell
.\RunSpeedTest.ps1 -Interval 300
```

The Windows batch launcher accepts interval and port as its first two values:

```bat
RunSpeedTest.bat 300 8600
```

## Dashboard port

The default port is 8501.  Use `--port` on macOS or `-Port` in PowerShell.

## Data directory

The default is a visible `SpeedtestDashboard` folder in the current user's home
folder.  It contains `speedtest_results.csv` and the `archive` folder.

Change it with one of these methods:

```bash
speedtest-dashboard --data-dir ~/Documents/SpeedtestData
export SPEEDTEST_DASHBOARD_DATA_DIR="$HOME/Documents/SpeedtestData"
```

```powershell
.\RunSpeedTest.ps1 -DataDir "$HOME\Documents\SpeedtestData"
```

An explicit `--data-dir` value has priority over the environment variable.

## Dashboard preferences

- Theme: Light, Dark, or automatic system detection.
- Timezone: `America/Chicago` by default, selectable in the dashboard.
- Download color: `#1976D2`.
- Upload color: `#8BDCCD`.
- Ping color: `#20B9D8`.

## Data retention

- Main CSV: approximately 30 days of samples.
- Archives: the latest 12 monthly CSV files.
