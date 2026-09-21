"""Native macOS controller for the local Speedtest Monitor."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser

from speedtest_dashboard import __version__
from speedtest_dashboard.app_config import (
    DATA_DIR_ENV,
    InstanceAlreadyRunningError,
    get_data_dir,
    instance_lock,
    load_collector_status,
)


APP_NAME = "Speedtest Monitor"
APP_BUILD = __version__
DESKTOP_MODE_ENV = "SPEEDTEST_DASHBOARD_DESKTOP"
DESKTOP_PLATFORM_ENV = "SPEEDTEST_DASHBOARD_DESKTOP_PLATFORM"
DEFAULT_INTERVAL = 300
DEFAULT_PORT = 8501


def streamlit_options(port: int) -> dict[str, object]:
    """Return production-safe Streamlit settings for the packaged app.

    PyInstaller relocates Streamlit outside a conventional ``site-packages``
    directory.  Streamlit otherwise mistakes the frozen bundle for a source
    checkout, enables development mode, and expects a separate Vite frontend
    on port 3000.
    """
    return {
        "global.developmentMode": False,
        "server.address": "127.0.0.1",
        "server.port": port,
        "browser.serverAddress": "127.0.0.1",
        "browser.serverPort": port,
        "server.headless": True,
        "browser.gatherUsageStats": False,
        "theme.base": "light",
        "theme.primaryColor": "#173F63",
        "theme.backgroundColor": "#F3F7FA",
        "theme.secondaryBackgroundColor": "#FFFFFF",
        "theme.textColor": "#17232E",
    }


def is_frozen() -> bool:
    """Return whether the process is running from a PyInstaller bundle."""
    return bool(getattr(sys, "frozen", False))


def dashboard_script_path() -> Path:
    """Locate the Streamlit script in source and frozen application layouts."""
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        return Path(bundle_root) / "speedtest_dashboard" / "dashboard.py"
    return Path(__file__).with_name("dashboard.py")


def available_port(preferred: int = DEFAULT_PORT) -> int:
    """Return the preferred local port when available, otherwise a free port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(("127.0.0.1", preferred))
            return preferred
        except OSError:
            probe.bind(("127.0.0.1", 0))
            return int(probe.getsockname()[1])


def service_command(
    port: int,
    interval: int,
    data_dir: Path,
    controller_pid: int | None = None,
) -> list[str]:
    """Build the child command for source or packaged execution."""
    args = [
        "--service",
        "--port",
        str(port),
        "--interval",
        str(interval),
        "--data-dir",
        str(data_dir),
    ]
    if controller_pid:
        args.extend(["--controller-pid", str(controller_pid)])
    if is_frozen():
        return [sys.executable, *args]
    return [sys.executable, "-m", "speedtest_dashboard.macos_app", *args]


def _pid_is_running(pid: int) -> bool:
    """Return whether a process still exists without changing it."""

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _exit_when_controller_stops(controller_pid: int, poll_seconds: float = 2.0) -> None:
    """Prevent a hidden service from surviving its owning controller."""

    if controller_pid <= 0:
        return
    while os.getppid() == controller_pid and _pid_is_running(controller_pid):
        time.sleep(poll_seconds)
    os._exit(0)


def legacy_orphan_service_pids(
    data_dir: Path,
    process_table: str | None = None,
) -> list[int]:
    """Find reparented Speedtest Monitor services for this results folder."""

    if process_table is None:
        try:
            process_table = subprocess.run(
                ["ps", "-axo", "pid=,ppid=,command="],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            ).stdout
        except (OSError, subprocess.SubprocessError):
            return []

    data_argument = re.compile(
        rf"--data-dir(?:=|\s+)[\"']?{re.escape(str(data_dir.resolve()))}[\"']?(?:\s|$)"
    )
    matches: list[int] = []
    for line in process_table.splitlines():
        fields = line.strip().split(maxsplit=2)
        if len(fields) != 3:
            continue
        raw_pid, raw_parent, command = fields
        if raw_parent != "1" or "--service" not in command:
            continue
        if not (
            "Speedtest Monitor.app/Contents/MacOS/Speedtest Monitor" in command
            or "speedtest_dashboard.macos_app" in command
        ):
            continue
        if not data_argument.search(command):
            continue
        try:
            pid = int(raw_pid)
        except ValueError:
            continue
        if pid != os.getpid():
            matches.append(pid)
    return matches


def stop_legacy_orphan_services(data_dir: Path) -> list[int]:
    """Stop legacy orphan services before starting the owned replacement."""

    stopped: list[int] = []
    for pid in legacy_orphan_service_pids(data_dir):
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            continue
        except PermissionError:
            continue

        deadline = time.monotonic() + 5.0
        while _pid_is_running(pid) and time.monotonic() < deadline:
            time.sleep(0.1)
        if _pid_is_running(pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        stopped.append(pid)
    return stopped


def run_services(
    port: int,
    interval: int,
    data_dir: Path,
    controller_pid: int = 0,
) -> None:
    """Run the collector and Streamlit server inside the hidden child process."""
    print(f"[INFO] {APP_NAME} build {APP_BUILD} starting on port {port}", flush=True)
    os.environ[DATA_DIR_ENV] = str(data_dir)
    os.environ[DESKTOP_MODE_ENV] = "1"
    os.environ[DESKTOP_PLATFORM_ENV] = "macos"

    from speedtest_dashboard import collector
    from streamlit.web import bootstrap

    if controller_pid:
        threading.Thread(
            target=_exit_when_controller_stops,
            args=(controller_pid,),
            name="controller-lifecycle-monitor",
            daemon=True,
        ).start()

    collector_args = [
        "--daemon",
        "--interval",
        str(interval),
        "--data-dir",
        str(data_dir),
    ]
    threading.Thread(
        target=collector.main,
        args=(collector_args,),
        name="speedtest-collector",
        daemon=True,
    ).start()

    options = streamlit_options(port)
    # ``bootstrap.run`` assumes the CLI has already loaded flag options.  The
    # desktop launcher calls it directly, so load them before Server creation.
    bootstrap.load_config_options(options)
    bootstrap.run(
        str(dashboard_script_path()),
        False,
        [],
        options,
    )


def service_is_ready(url: str) -> bool:
    """Return whether the local Streamlit health endpoint is ready."""
    try:
        with urllib.request.urlopen(f"{url}/_stcore/health", timeout=0.5) as response:
            return response.status == 200
    except Exception:
        return False


def _run_controller(interval: int, requested_port: int, data_dir: Path) -> None:
    """Show the macOS controller and supervise the hidden service process."""
    import tkinter as tk
    from tkinter import messagebox

    data_dir.mkdir(parents=True, exist_ok=True)
    port = available_port(requested_port)
    url = f"http://127.0.0.1:{port}"

    log_dir = Path.home() / "Library" / "Logs" / "Ramrattan Speedtest Monitor"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_handle = (log_dir / "monitor.log").open("a", encoding="utf-8")
    stopped_orphans = stop_legacy_orphan_services(data_dir)
    for pid in stopped_orphans:
        log_handle.write(
            f"[INFO] Stopped orphaned Speedtest Monitor service PID {pid}.\n"
        )
    log_handle.flush()

    child_env = os.environ.copy()
    child_env[DATA_DIR_ENV] = str(data_dir)
    child_env[DESKTOP_MODE_ENV] = "1"
    child_env[DESKTOP_PLATFORM_ENV] = "macos"
    child = subprocess.Popen(
        service_command(port, interval, data_dir, os.getpid()),
        env=child_env,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
    )

    root = tk.Tk()
    root.title(APP_NAME)
    root.geometry("520x285")
    root.resizable(False, False)
    root.configure(background="#F3F7FA")

    heading = tk.Label(
        root,
        text="Speedtest Monitor",
        font=("Helvetica Neue", 24, "bold"),
        foreground="#173F63",
        background="#F3F7FA",
    )
    heading.pack(pady=(28, 6))

    explanation = tk.Label(
        root,
        text="Monitoring this Mac's internet connection every five minutes.",
        font=("Helvetica Neue", 13),
        foreground="#425466",
        background="#F3F7FA",
    )
    explanation.pack()

    status_text = tk.StringVar(value="Starting the local dashboard...")
    status = tk.Label(
        root,
        textvariable=status_text,
        font=("Helvetica Neue", 12),
        foreground="#2F78B8",
        background="#F3F7FA",
        wraplength=470,
    )
    status.pack(pady=(20, 16))

    button_frame = tk.Frame(root, background="#F3F7FA")
    button_frame.pack()

    open_button = tk.Button(
        button_frame,
        text="Open Dashboard",
        command=lambda: webbrowser.open(url),
        state="disabled",
        width=18,
        pady=7,
    )
    open_button.grid(row=0, column=0, padx=8)

    def stop_child() -> None:
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
        log_handle.close()

    def quit_app() -> None:
        if messagebox.askokcancel(
            "Quit Speedtest Monitor",
            "Stop collecting speed-test results and quit?",
        ):
            stop_child()
            root.destroy()

    quit_button = tk.Button(
        button_frame,
        text="Quit Monitor",
        command=quit_app,
        width=18,
        pady=7,
    )
    quit_button.grid(row=0, column=1, padx=8)

    data_label = tk.Label(
        root,
        text=f"Version {APP_BUILD}  |  Results folder: {data_dir}",
        font=("Helvetica Neue", 10),
        foreground="#66788A",
        background="#F3F7FA",
        wraplength=470,
    )
    data_label.pack(pady=(22, 0))

    browser_opened = False

    def poll_service() -> None:
        nonlocal browser_opened
        if child.poll() is not None:
            status_text.set("The monitor stopped unexpectedly.  Review monitor.log for details.")
            return
        if service_is_ready(url):
            collector_status = load_collector_status(data_dir)
            status_text.set(collector_status["message"])
            open_button.configure(state="normal")
            if not browser_opened:
                browser_opened = True
                webbrowser.open(url)
        root.after(750, poll_service)

    root.protocol("WM_DELETE_WINDOW", quit_app)
    root.after(250, poll_service)
    root.mainloop()


def run_controller(interval: int, requested_port: int, data_dir: Path) -> None:
    """Run one controller per results folder and reject duplicate launches."""

    try:
        with instance_lock("controller", data_dir):
            _run_controller(interval, requested_port, data_dir)
    except InstanceAlreadyRunningError:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(
            APP_NAME,
            "Speedtest Monitor is already running.  Use the existing controller "
            "window to open the dashboard or quit the monitor.",
        )
        root.destroy()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog=APP_NAME)
    parser.add_argument("--service", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--controller-pid", type=int, default=0, help=argparse.SUPPRESS)
    parser.add_argument("--data-dir")
    args = parser.parse_args(argv)

    data_dir = get_data_dir(args.data_dir)
    if args.service:
        run_services(args.port, args.interval, data_dir, args.controller_pid)
    else:
        run_controller(args.interval, args.port, data_dir)


if __name__ == "__main__":
    main()
