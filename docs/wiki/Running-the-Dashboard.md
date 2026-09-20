# Running the Dashboard

## macOS

```bash
./RunSpeedTest.command --interval 300
```

## Windows

```powershell
.\RunSpeedTest.ps1 -Interval 120 -Port 8501
```

or:

```bat
RunSpeedTest.bat 120 8501
```

## Installed command

```bash
speedtest-dashboard --interval 120 --port 8501
```

## Access and controls

Open <http://localhost:8501>.  The dashboard provides:

- Bar or line charts.
- Hour, day, week, month, and year windows.
- Previous-period comparison overlays.
- Server filtering.
- Custom colors.
- Automatic or manual refresh.
- Timezone and theme selectors.

Stop the macOS or command-line launcher with **Control-C**.  Windows launchers
open separate collector and dashboard windows, which can be closed normally.
