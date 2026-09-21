"""Native Windows pilot controller for the local Speedtest Monitor."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import urllib.request
import webbrowser

from speedtest_dashboard.app_config import DATA_DIR_ENV, get_data_dir


APP_NAME = "Speedtest Monitor"
APP_BUILD = "0.2.0-windows-pilot.4"
DESKTOP_MODE_ENV = "SPEEDTEST_DASHBOARD_DESKTOP"
DESKTOP_PLATFORM_ENV = "SPEEDTEST_DASHBOARD_DESKTOP_PLATFORM"
DEFAULT_INTERVAL = 300
DEFAULT_PORT = 8501
_SERVICE_LOG_HANDLE = None


def streamlit_options(port: int) -> dict[str, object]:
    """Return production-safe Streamlit settings for the packaged app."""
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


def service_command(port: int, interval: int, data_dir: Path) -> list[str]:
    """Build the hidden child-service command."""
    args = [
        "--service",
        "--port",
        str(port),
        "--interval",
        str(interval),
        "--data-dir",
        str(data_dir),
    ]
    if is_frozen():
        return [sys.executable, *args]
    return [sys.executable, "-m", "speedtest_dashboard.windows_app", *args]


def run_services(
    port: int,
    interval: int,
    data_dir: Path,
    *,
    start_collector: bool = True,
) -> None:
    """Run the collector and Streamlit server inside the hidden child process."""
    ensure_service_output_streams()
    print(f"[INFO] {APP_NAME} build {APP_BUILD} starting on port {port}", flush=True)
    os.environ[DATA_DIR_ENV] = str(data_dir)
    os.environ[DESKTOP_MODE_ENV] = "1"
    os.environ[DESKTOP_PLATFORM_ENV] = "windows"

    from streamlit.web import bootstrap

    if start_collector:
        from speedtest_dashboard import collector

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
    bootstrap.load_config_options(options)
    bootstrap.run(str(dashboard_script_path()), False, [], options)


def service_is_ready(url: str) -> bool:
    """Return whether the local Streamlit health endpoint is ready."""
    try:
        with urllib.request.urlopen(f"{url}/_stcore/health", timeout=0.5) as response:
            return response.status == 200
    except Exception:
        return False


def log_directory() -> Path:
    """Return the per-user Windows application log directory."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    root = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
    return root / "Ramrattan Speedtest Monitor" / "Logs"


def ensure_service_output_streams() -> None:
    """Give a windowed PyInstaller child writable stdout and stderr streams.

    PyInstaller deliberately sets these streams to ``None`` for a windowed
    executable.  The collector reports progress with ``print()``, so leaving
    them unset can stop its background thread before the first result while
    Streamlit continues serving an apparently healthy, empty dashboard.
    """
    global _SERVICE_LOG_HANDLE

    if sys.stdout is None:
        log_dir = log_directory()
        log_dir.mkdir(parents=True, exist_ok=True)
        _SERVICE_LOG_HANDLE = (log_dir / "monitor.log").open(
            "a", encoding="utf-8", buffering=1
        )
        sys.stdout = _SERVICE_LOG_HANDLE
    _configure_utf8_output(sys.stdout)
    if sys.stderr is None:
        sys.stderr = sys.stdout
    elif sys.stderr is not sys.stdout:
        _configure_utf8_output(sys.stderr)


def _configure_utf8_output(stream: object) -> None:
    """Use UTF-8 when a writable text stream supports reconfiguration."""
    reconfigure = getattr(stream, "reconfigure", None)
    if not callable(reconfigure):
        return
    try:
        reconfigure(encoding="utf-8", errors="backslashreplace")
    except (AttributeError, OSError, ValueError):
        # Some embedded or test streams cannot be reconfigured.  Collector
        # status text remains ASCII-safe as a second line of defence.
        return


def run_controller(interval: int, requested_port: int, data_dir: Path) -> None:
    """Show the Windows controller and supervise the hidden service process."""
    import tkinter as tk
    from tkinter import messagebox

    port = available_port(requested_port)
    url = f"http://127.0.0.1:{port}"
    data_dir.mkdir(parents=True, exist_ok=True)

    log_dir = log_directory()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_handle = (log_dir / "monitor.log").open("a", encoding="utf-8")

    child_env = os.environ.copy()
    child_env[DATA_DIR_ENV] = str(data_dir)
    child_env[DESKTOP_MODE_ENV] = "1"
    child_env[DESKTOP_PLATFORM_ENV] = "windows"
    popen_kwargs: dict[str, object] = {}
    if os.name == "nt":
        popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    child = subprocess.Popen(
        service_command(port, interval, data_dir),
        env=child_env,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        **popen_kwargs,
    )

    root = tk.Tk()
    root.title(APP_NAME)
    root.geometry("560x300")
    root.resizable(False, False)
    root.configure(background="#F3F7FA")

    tk.Label(
        root,
        text=APP_NAME,
        font=("Segoe UI", 24, "bold"),
        foreground="#173F63",
        background="#F3F7FA",
    ).pack(pady=(30, 6))
    tk.Label(
        root,
        text="Monitoring this PC's internet connection every five minutes.",
        font=("Segoe UI", 12),
        foreground="#425466",
        background="#F3F7FA",
    ).pack()

    status_text = tk.StringVar(value="Starting the local dashboard...")
    tk.Label(
        root,
        textvariable=status_text,
        font=("Segoe UI", 11),
        foreground="#2F78B8",
        background="#F3F7FA",
    ).pack(pady=(22, 16))

    button_frame = tk.Frame(root, background="#F3F7FA")
    button_frame.pack()
    open_button = tk.Button(
        button_frame,
        text="Open Dashboard",
        command=lambda: webbrowser.open(url),
        state="disabled",
        width=20,
        pady=8,
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

    tk.Button(
        button_frame,
        text="Quit Monitor",
        command=quit_app,
        width=20,
        pady=8,
    ).grid(row=0, column=1, padx=8)

    tk.Label(
        root,
        text=f"Windows Pilot 4  |  Results folder: {data_dir}",
        font=("Segoe UI", 9),
        foreground="#66788A",
        background="#F3F7FA",
        wraplength=520,
    ).pack(pady=(24, 0))

    browser_opened = False

    def poll_service() -> None:
        nonlocal browser_opened
        if child.poll() is not None:
            status_text.set("The monitor stopped unexpectedly.  Review monitor.log for details.")
            return
        if service_is_ready(url):
            status_text.set("The monitor is running.")
            open_button.configure(state="normal")
            if not browser_opened:
                browser_opened = True
                webbrowser.open(url)
        root.after(750, poll_service)

    root.protocol("WM_DELETE_WINDOW", quit_app)
    root.after(250, poll_service)
    root.mainloop()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog=APP_NAME)
    parser.add_argument("--service", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--dashboard-only", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--data-dir")
    args = parser.parse_args(argv)

    data_dir = get_data_dir(args.data_dir)
    if args.service:
        run_services(
            args.port,
            args.interval,
            data_dir,
            start_collector=not args.dashboard_only,
        )
    else:
        run_controller(args.interval, args.port, data_dir)


if __name__ == "__main__":
    main()
