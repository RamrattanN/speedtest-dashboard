# Mac Testing Guide

This guide assumes you are using a Mac that does not already have the project
configured.  The test does not change anything outside the downloaded project,
its local `.venv` folder, and `~/SpeedtestDashboard`.

## 1. Confirm Python

Open Terminal from **Applications > Utilities > Terminal**, then run:

```bash
python3 --version
```

The version must be Python 3.11 or newer.  If the command is missing or the
version is older, install a current Python 3 release from
<https://www.python.org/downloads/macos/> and reopen Terminal.

## 2. Download the current source

In Terminal, run:

```bash
cd ~/Desktop
git clone https://github.com/RamrattanN/speedtest-dashboard.git
cd speedtest-dashboard
```

If macOS asks to install its command-line developer tools, approve the prompt,
allow it to finish, and repeat the commands.

## 3. Start the application

Run:

```bash
chmod +x RunSpeedTest.command
./RunSpeedTest.command --interval 300
```

The first start creates `.venv` and installs the required Python packages.  It
may take several minutes.  Later starts are faster.

Expected results:

1. Terminal reports that the collector and dashboard are starting.
2. Your browser opens <http://localhost:8501>.
3. The dashboard initially says it is waiting for data.
4. After a successful speed test, the dashboard displays the recorded result.
5. Finder shows `speedtest_results.csv` inside your home folder under
   `SpeedtestDashboard`.

The collector may report that the official Ookla CLI is unavailable.  In
production mode this pauses new measurements while leaving the dashboard
available.  Install the CLI from `https://www.speedtest.net/apps/cli`, then
confirm its path under **Connection Overview > Measurement engine**.  Select
Compatibility mode only when intentionally testing the Python engine.

## 4. Complete the acceptance checklist

- The dashboard opens without a Python traceback.
- The **Display settings** section expands.
- **Bar** and **Line / Curve** views both render.
- **Light** and **Dark** themes both remain readable.
- The timezone list includes `America/Chicago`.
- Automatic refresh checks for new data every 60 seconds.
- The header refresh icon immediately reloads dashboard data.
- The header **Run speed test** action requests one new measurement without
  launching an overlapping collector.
- Opening Speedtest Monitor a second time reports that it is already running
  and does not start another service or collector.
- The chart-type selector appears directly below the chart.
- `~/SpeedtestDashboard/speedtest_results.csv` exists after collection.
- Stopping the launcher with **Control-C** ends both processes.

## 5. Collect diagnostic information if something fails

Do not close Terminal immediately.  Copy the last error shown, then run these
commands from the project folder:

```bash
python3 --version
uname -m
git rev-parse HEAD
ls -la ~/SpeedtestDashboard
```

Send the copied error and command output with your test result.  Do not send the
contents of the CSV unless you specifically want its measurements reviewed.

## Restart later

Return to the project folder and run the same launcher:

```bash
cd ~/Desktop/speedtest-dashboard
./RunSpeedTest.command --interval 300
```
