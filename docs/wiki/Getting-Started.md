# Getting Started

## macOS application

Open the
[latest production release](https://github.com/RamrattanN/speedtest-dashboard/releases/latest)
and download the disk image matching the Mac processor: **macOS Intel** for an
Intel Mac or **macOS Apple Silicon** for an M-series Mac.  The ARM64 package
passes automated validation but still awaits testing on a physical Apple
silicon Mac.  Python, Git, VS Code, and a repository checkout are not required.

1. Quit any older copy of Speedtest Monitor.
2. Open the disk image and drag **Speedtest Monitor** to **Applications**.
3. Choose **Replace** if an older copy is installed.
4. If macOS blocks the application, select **Done**, open **System Settings >
   Privacy & Security**, scroll to **Security**, and select **Open Anyway**.
5. If needed, open **Read Me First - macOS Security.txt** and use the optional
   **Allow and Open Speedtest Monitor.command** helper in the disk image.  If
   macOS blocks the helper itself, select **Done**, approve the helper with
   **Open Anyway** in Privacy & Security, and run it again.
6. See the [macOS Desktop Packaging guide](https://github.com/RamrattanN/speedtest-dashboard/blob/main/docs/Mac-Desktop-Packaging.md) for the
   Terminal fallback and complete security explanation.
7. Open **Speedtest Monitor** and keep the controller open.
8. Download the official Speedtest CLI directly from
   [Ookla](https://www.speedtest.net/apps/cli), then open **Connection Overview
   > Measurement engine** to confirm detection or save its executable path.

The dashboard opens automatically when the service is ready.  Results are
stored in `~/SpeedtestDashboard`.

The manual Terminal fallback is:

```bash
sudo xattr -dr com.apple.quarantine "/Applications/Speedtest Monitor.app"
open "/Applications/Speedtest Monitor.app"
```

The first command may request the Mac administrator password.  Terminal does
not display password characters while they are typed.

## Windows x64 application

Open the
[latest production release](https://github.com/RamrattanN/speedtest-dashboard/releases/latest)
and download the **Windows x64** installer.  Python, Git, VS Code, and a
repository checkout are not required.

1. Download the installer from the project Releases page.
2. Run the installer.
3. If SmartScreen appears, select **More info**, verify the download source,
   then select **Run anyway**.
4. Open **Speedtest Monitor** from the Start menu and keep the controller open.
5. Download the official Speedtest CLI directly from
   [Ookla](https://www.speedtest.net/apps/cli).  Extract it to
   `C:\Tools\OoklaSpeedtest\speedtest.exe`, or save its full location under
   **Connection Overview > Measurement engine**.

Running the installer again offers **Repair** and **Uninstall completely**.
Uninstall removes the application, shortcuts, and logs but preserves measurement
history in `%USERPROFILE%\SpeedtestDashboard`.  See the
[Windows Desktop Packaging guide](https://github.com/RamrattanN/speedtest-dashboard/blob/main/docs/Windows-Desktop-Packaging.md) for details.

Every installation starts with location-neutral **Automatic** server
selection.  If the first results use an unexpectedly distant region, open
**Test server selection**, choose **Preferred city or region**, enter a city
plus state, province, or country, and save.  The next measurement calibrates
regional candidates.  This control works the same way on macOS and Windows.

Production collection does not silently substitute the Python engine when the
official CLI is unavailable.  The controller and dashboard report that setup
is required.  Python compatibility mode is available as an explicit temporary
choice, but those samples should not be treated as directly comparable to
official Ookla measurements.

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
