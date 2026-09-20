# Configuration

## Desktop pilot defaults

Pilot 3 is designed for a simple double-click experience.  Its controller uses:

- Test interval: 300 seconds
- Preferred local port: 8501
- Data folder: `~/SpeedtestDashboard`
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

The data directory can also be set for all commands:

```bash
export SPEEDTEST_DASHBOARD_DATA_DIR="$HOME/Documents/SpeedtestData"
```

An explicit `--data-dir` value has priority over the environment variable.

## Dashboard preferences

- Theme: Light, Dark, or automatic system detection.
- Timezone: `America/Chicago` by default, selectable in the dashboard.
- Download colour: `#1976D2`.
- Upload colour: `#8BDCCD`.
- Ping colour: `#20B9D8`.

## Data retention

- Main CSV: approximately 30 days of samples.
- Archives: the latest 12 monthly CSV files.
