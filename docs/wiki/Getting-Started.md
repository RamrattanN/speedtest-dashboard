# Getting Started

## Prerequisites

- macOS or Windows 10/11.
- Python 3.11 or newer.
- Git for cloning the repository.
- Official Ookla Speedtest CLI recommended, but not required for initial setup.

## macOS

```bash
git clone https://github.com/RamrattanN/speedtest-dashboard.git
cd speedtest-dashboard
chmod +x RunSpeedTest.command
./RunSpeedTest.command
```

See the [Mac Testing Guide](../Mac-Testing.md) and
[VS Code Setup Guide](../VS-Code-Setup-Mac.md) for guided instructions.

## Windows

```powershell
git clone https://github.com/RamrattanN/speedtest-dashboard.git
cd speedtest-dashboard
.\setup_venv.bat
.\RunSpeedTest.ps1 -Interval 120 -Port 8501
```

`RunSpeedTest.bat` is also available for a double-click start.

## Dashboard access

Open <http://localhost:8501> after the launcher starts.  Results are stored in
the `SpeedtestDashboard` folder inside your home folder by default.
