# Configuration

## Desktop defaults

The macOS and Windows applications are designed for a simple double-click
experience.  Their controllers use:

- Test interval: 300 seconds
- Preferred local port: 8501
- Data folder: `~/SpeedtestDashboard` on macOS or
  `%USERPROFILE%\SpeedtestDashboard` on Windows
- Display refresh: 60 seconds

If port 8501 is already in use, the controller selects another local port and
opens the correct address.  Use **Open Dashboard** rather than typing a port.

## Developer configuration

The source launcher and installed command support overrides:

```bash
./RunSpeedTest.command --interval 300
speedtest-dashboard --interval 300 --port 8501
speedtest-dashboard --data-dir ~/Documents/SpeedtestData
```

The `SPEEDTEST_DASHBOARD_DATA_DIR` environment variable changes the data
directory for all commands.  An explicit `--data-dir` value has priority.

## Dashboard preferences

- Theme: Light, Dark, or automatic system detection.
- Timezone: `America/Chicago` by default, selectable in the dashboard.
- Download colour: `#1976D2`.
- Upload colour: `#8BDCCD`.
- Ping colour: `#20B9D8`.

## Data retention

- Main CSV: approximately 30 days of samples.
- Archives: the latest 12 monthly CSV files.
