# Configuration

## Desktop defaults

The macOS and Windows applications are designed for a simple double-click
experience.  Their controllers use:

- Test interval: 300 seconds
- Preferred local port: 8501
- Data folder: `~/SpeedtestDashboard` on macOS or
  `%USERPROFILE%\SpeedtestDashboard` on Windows
- Display refresh: 60 seconds
- Measurement engine: official Ookla CLI only

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

`SPEEDTEST_OOKLA_CLI` may contain the full path to an official Ookla CLI
executable.  A path saved in **Measurement engine** takes priority for normal
desktop operation.

## Measurement engine

Production mode requires the official Ookla CLI and pauses measurements when
it is unavailable.  The monitor checks a saved path, `SPEEDTEST_OOKLA_CLI`,
`PATH`, and common Windows and macOS installation locations.  It verifies the
binary's version output so the unrelated Python command named `speedtest` is
not mistaken for Ookla's application.

The application does not redistribute Ookla's executable.  Obtain it directly
from [Ookla](https://www.speedtest.net/apps/cli), then use **Connection
Overview > Measurement engine** to confirm detection.  Compatibility mode is
an explicit opt-in and may record materially different results.

## Dashboard preferences

- Theme: Light, Dark, or automatic system detection.
- Timezone: `America/Chicago` by default, selectable in the dashboard.
- Download colour: `#1976D2`.
- Upload colour: `#8BDCCD`.
- Ping colour: `#20B9D8`.

## Test server selection

New installations use **Automatic** selection.  This is intentionally
location-neutral and does not assume that every user is near the same city.
The speed-test provider estimates the location from the public IP address,
which can be inaccurate when an ISP, VPN, proxy, or security service routes
traffic through another region.

If automatic selection chooses a distant area:

1. Open **Test server selection** in Connection Overview.
2. Choose **Preferred city or region**.
3. Enter a city plus state, province, or country, such as `Austin, TX`.
4. Select **Save test server preference**.
5. Leave the monitor running for the next collection cycle.

The monitor searches the provider's server list, latency-ranks matching
candidates, and stores several server IDs for regional failover.  It stores
only the general area and server metadata in `settings.json` beside the CSV.
No street address is requested or stored.  Choose **Automatic** and save to
return to provider-selected servers.

If every calibrated regional candidate is temporarily unavailable, the cycle
may use unrestricted automatic selection.  That row is labeled **Automatic
fallback** so it can be distinguished from the preferred-area baseline.

## Data retention

- Main CSV: samples from the latest rolling 365 days.
- Archives: monthly files are pruned to the same rolling 365-day boundary.
- Use **Data management** below Window Summary to reset all measurements.  The
  two-step confirmation permanently clears both locations, preserves settings,
  and requests a fresh collection cycle.
