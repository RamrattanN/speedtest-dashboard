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

## Windows developer setup

Pilot 3 does not include a Windows desktop application.  Developers can use
Python 3.11 or newer and the installable command:

```bat
git clone https://github.com/RamrattanN/speedtest-dashboard.git
cd speedtest-dashboard
setup_venv.bat
.venv\Scripts\speedtest-dashboard.exe --interval 300 --port 8501
```

The former PowerShell and batch launchers are retired.
