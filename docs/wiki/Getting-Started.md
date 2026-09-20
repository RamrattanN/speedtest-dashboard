# Getting Started

## macOS Intel private pilot

Pilot users need an Intel Mac and the current Pilot 3 disk image.  Python, Git,
VS Code, and a repository checkout are not required.

1. Quit any older copy of Speedtest Monitor.
2. Open `Speedtest-Monitor-macOS-Intel-pilot-3.dmg`.
3. Drag **Speedtest Monitor** to **Applications**.
4. Complete the unsigned-pilot security step described in the
   [macOS Pilot Packaging guide](../Mac-Pilot-Packaging.md).
5. Open **Speedtest Monitor** and keep the controller open.

The dashboard opens automatically when the service is ready.  Results are
stored in `~/SpeedtestDashboard`.

## macOS developer setup

Developers need Python 3.11 or newer and Git:

```bash
git clone https://github.com/RamrattanN/speedtest-dashboard.git
cd speedtest-dashboard
chmod +x RunSpeedTest.command
./RunSpeedTest.command --interval 300
```

See the [Mac Testing Guide](../Mac-Testing.md) and
[VS Code Setup Guide](../VS-Code-Setup-Mac.md) for guided development steps.

## Windows x64 private pilot

Windows pilot users need the current Windows Pilot 1 installer.  Python, Git,
VS Code, and a repository checkout are not required.

1. Download and unzip the controlled pilot artifact.
2. Run `Speedtest-Monitor-Windows-x64-pilot-1.exe`.
3. If SmartScreen appears, select **More info**, then **Run anyway**.
4. Open **Speedtest Monitor** from the Start menu and keep the controller open.

Results are stored in `%USERPROFILE%\SpeedtestDashboard`.  See the
[Windows Pilot Packaging guide](../Windows-Pilot-Packaging.md) for complete
acceptance and troubleshooting steps.

## Windows developer setup

Developers can use Python 3.11 or newer and the installable command:

```bat
git clone https://github.com/RamrattanN/speedtest-dashboard.git
cd speedtest-dashboard
setup_venv.bat
.venv\Scripts\speedtest-dashboard.exe --interval 300 --port 8501
```

The former PowerShell and batch launchers are retired.
