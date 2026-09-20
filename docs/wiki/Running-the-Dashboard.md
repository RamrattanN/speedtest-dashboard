# Running the Dashboard

## Installed macOS pilot

Open **Speedtest Monitor** from Applications.  The controller starts the
collector and local dashboard together, then opens the dashboard in the default
browser.

- Keep the controller open while results should continue to be collected.
- Closing the browser tab does not stop collection.
- Select **Open Dashboard** to reopen the browser page.
- Select **Quit Monitor** to stop the collector and dashboard safely.

## macOS developer launcher

```bash
./RunSpeedTest.command --interval 300
```

Stop the developer launcher with **Control-C**.

## Installed Windows pilot

Open **Speedtest Monitor** from the Start menu.  Its controller has the same
**Open Dashboard** and **Quit Monitor** behavior as the macOS pilot.  Closing
the browser tab does not stop collection.

## Installed Python command

```bash
speedtest-dashboard --interval 300 --port 8501
```

On Windows after `setup_venv.bat`, use:

```bat
.venv\Scripts\speedtest-dashboard.exe --interval 300 --port 8501
```

## Dashboard controls

The dashboard provides:

- Latest download, upload, ping, and recorded-time cards.
- Bar or line charts.
- Hour, day, week, month, and year windows.
- Previous-period comparison overlays.
- Server filtering.
- Custom colours.
- Automatic or manual display refresh.
- Timezone and theme selectors.
