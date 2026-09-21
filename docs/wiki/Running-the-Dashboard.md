# Running the Dashboard

## Installed desktop application

Open **Speedtest Monitor** from Applications on macOS or the Start menu on
Windows.  The controller starts the collector and local dashboard together,
then opens the dashboard in the default browser.

- Keep the controller open while results should continue to be collected.
- Closing the browser tab does not stop collection.
- Select **Open Dashboard** to reopen the browser page.
- Select **Quit Monitor** to stop the collector and dashboard safely.

## Developer launchers

On macOS:

```bash
./RunSpeedTest.command --interval 300
```

Stop the launcher with **Control-C**.  With an installed Python package on any
supported system:

```bash
speedtest-dashboard --interval 300 --port 8501
```

## Dashboard controls

The dashboard provides:

- Latest download, upload, ping, and recorded-time cards.
- Minimum, average, and peak rows directly under Latest Result, calculated
  from the selected reporting window and server filters.
- Bar or line charts.
- Time-axis-only chart zooming, which protects the speed and ping scales from
  accidental vertical zoom changes.
- Hour, day, week, month, and year windows.
- Previous-period comparison overlays.
- Server filtering, custom colours, timezone, and theme controls.
- Automatic display refresh every 60 seconds.
- **Refresh now** for an immediate data reload after automatic refresh is
  turned off.
- **Test server selection** to keep measurements in a preferred city or region
  when public-IP geolocation selects a distant server.
