# Getting Started

## macOS application

Intel users need `Speedtest-Monitor-macOS-Intel-0.2.0.dmg`.  Apple silicon
users can use the `Speedtest-Monitor-macOS-Apple-Silicon-0.2.0.dmg` candidate
after confirming that it came from the project workflow.  The ARM64 candidate
still requires validation on a physical Apple silicon Mac.  Python, Git, VS
Code, and a repository checkout are not required.

1. Quit any older copy of Speedtest Monitor.
2. Open the disk image and drag **Speedtest Monitor** to **Applications**.
3. Choose **Replace** if an older copy is installed.
4. Complete the unsigned-application security step in the
   [macOS Desktop Packaging guide](../Mac-Desktop-Packaging.md).
5. Open **Speedtest Monitor** and keep the controller open.

The dashboard opens automatically when the service is ready.  Results are
stored in `~/SpeedtestDashboard`.

## Windows x64 application

Users need `Speedtest-Monitor-Windows-x64-0.2.0.exe`.  Python, Git, VS Code,
and a repository checkout are not required.

1. Download and unzip the GitHub Actions artifact.
2. Run the installer.
3. If SmartScreen appears, select **More info**, verify the download source,
   then select **Run anyway**.
4. Open **Speedtest Monitor** from the Start menu and keep the controller open.

Running the installer again offers **Repair** and **Uninstall completely**.
Uninstall removes the application, shortcuts, and logs but preserves measurement
history in `%USERPROFILE%\SpeedtestDashboard`.  See the
[Windows Desktop Packaging guide](../Windows-Desktop-Packaging.md) for details.

## Developer setup

Developers need Python 3.11 or newer and Git.  On macOS:

```bash
git clone https://github.com/RamrattanN/speedtest-dashboard.git
cd speedtest-dashboard
chmod +x RunSpeedTest.command
./RunSpeedTest.command --interval 300
```

On Windows:

```bat
git clone https://github.com/RamrattanN/speedtest-dashboard.git
cd speedtest-dashboard
setup_venv.bat
.venv\Scripts\speedtest-dashboard.exe --interval 300 --port 8501
```

The former PowerShell and batch application launchers are retired.
