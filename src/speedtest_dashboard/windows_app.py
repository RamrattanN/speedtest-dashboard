"""Native Windows controller for the local Speedtest Monitor."""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path
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
    wait_for_collection_restart,
)


APP_NAME = "Speedtest Monitor"
APP_BUILD = __version__
DESKTOP_MODE_ENV = "SPEEDTEST_DASHBOARD_DESKTOP"
DESKTOP_PLATFORM_ENV = "SPEEDTEST_DASHBOARD_DESKTOP_PLATFORM"
DEFAULT_INTERVAL = 300
DEFAULT_PORT = 8501
COLLECTOR_TIMEOUT_SECONDS = 180
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


def service_command(
    port: int,
    interval: int,
    data_dir: Path,
    controller_pid: int | None = None,
) -> list[str]:
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
    if controller_pid:
        args.extend(["--controller-pid", str(controller_pid)])
    if is_frozen():
        return [sys.executable, *args]
    return [sys.executable, "-m", "speedtest_dashboard.windows_app", *args]


def collector_command(data_dir: Path) -> list[str]:
    """Build a one-measurement child command for source or packaged execution."""

    args = ["--collect-once", "--data-dir", str(data_dir)]
    if is_frozen():
        return [sys.executable, *args]
    return [sys.executable, "-m", "speedtest_dashboard.windows_app", *args]


def terminate_process_tree(process: subprocess.Popen) -> None:
    """Terminate a child and descendants without leaving a frozen speed test behind."""

    if process.poll() is not None:
        return
    if os.name == "nt":
        try:
            result = subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if result.returncode != 0 and process.poll() is None:
                process.kill()
        except (OSError, subprocess.SubprocessError):
            process.kill()
    else:
        process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


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


def run_collector_cycle(
    data_dir: Path,
    *,
    timeout: int = COLLECTOR_TIMEOUT_SECONDS,
) -> bool:
    """Run one speed test in an expendable child process."""

    print(f"[INFO] Measurement cycle started with a {timeout}-second safety timeout.", flush=True)
    popen_kwargs: dict[str, object] = {
        "stdout": sys.stdout,
        "stderr": sys.stderr,
    }
    if os.name == "nt":
        popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
    try:
        child = subprocess.Popen(collector_command(data_dir), **popen_kwargs)
    except OSError as exc:
        print(f"[ERROR] Could not start measurement child: {exc}", flush=True)
        return False
    try:
        return_code = child.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        print(
            f"[ERROR] Measurement exceeded {timeout} seconds.  Terminating it and continuing on schedule.",
            flush=True,
        )
        terminate_process_tree(child)
        return False

    if return_code != 0:
        print(f"[WARN] Measurement child exited with code {return_code}.  The supervisor will retry next cycle.", flush=True)
        return False
    print("[INFO] Measurement cycle completed.", flush=True)
    return True


def _supervise_collector(
    interval: int,
    data_dir: Path,
    *,
    timeout: int = COLLECTOR_TIMEOUT_SECONDS,
    stop_event: threading.Event | None = None,
) -> None:
    """Keep measurements on schedule even when a backend call freezes."""

    stop_event = stop_event or threading.Event()
    while not stop_event.is_set():
        started = time.monotonic()
        try:
            run_collector_cycle(data_dir, timeout=timeout)
        except Exception as exc:
            print(
                f"[ERROR] Measurement supervisor recovered from an unexpected error: {exc}",
                flush=True,
            )
        elapsed = time.monotonic() - started
        wait_seconds = max(5.0, float(interval) - elapsed)
        print(f"[INFO] Next measurement cycle in {int(round(wait_seconds))} seconds.", flush=True)
        if wait_for_collection_restart(
            wait_seconds,
            data_dir,
            stop_event=stop_event,
        ):
            print(
                "[INFO] One-shot measurement request acknowledged.  "
                "Starting one measurement cycle.",
                flush=True,
            )


def supervise_collector(
    interval: int,
    data_dir: Path,
    *,
    timeout: int = COLLECTOR_TIMEOUT_SECONDS,
    stop_event: threading.Event | None = None,
) -> None:
    """Run one Windows collector supervisor per results folder."""

    try:
        with instance_lock("collector", data_dir):
            _supervise_collector(
                interval,
                data_dir,
                timeout=timeout,
                stop_event=stop_event,
            )
    except InstanceAlreadyRunningError as exc:
        print(f"[INFO] {exc}  This collector will not start.", flush=True)


def run_services(
    port: int,
    interval: int,
    data_dir: Path,
    *,
    start_collector: bool = True,
    controller_pid: int = 0,
) -> None:
    """Run the collector and Streamlit server inside the hidden child process."""
    ensure_service_output_streams()
    print(f"[INFO] {APP_NAME} build {APP_BUILD} starting on port {port}", flush=True)
    os.environ[DATA_DIR_ENV] = str(data_dir)
    os.environ[DESKTOP_MODE_ENV] = "1"
    os.environ[DESKTOP_PLATFORM_ENV] = "windows"

    from streamlit.web import bootstrap

    if os.name == "nt" and hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    if controller_pid:
        threading.Thread(
            target=_exit_when_controller_stops,
            args=(controller_pid,),
            name="controller-lifecycle-monitor",
            daemon=True,
        ).start()

    if start_collector:
        threading.Thread(
            target=supervise_collector,
            args=(interval, data_dir),
            name="speedtest-collector-supervisor",
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
        reconfigure(
            encoding="utf-8",
            errors="backslashreplace",
            line_buffering=True,
            write_through=True,
        )
    except (AttributeError, OSError, ValueError):
        # Some embedded or test streams cannot be reconfigured.  Collector
        # status text remains ASCII-safe as a second line of defence.
        return


def _run_controller(interval: int, requested_port: int, data_dir: Path) -> None:
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
        service_command(port, interval, data_dir, os.getpid()),
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
        wraplength=520,
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
        terminate_process_tree(child)
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
        text=f"Version {APP_BUILD}  |  Results folder: {data_dir}",
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
    parser.add_argument("--collect-once", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--dashboard-only", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--controller-pid", type=int, default=0, help=argparse.SUPPRESS)
    parser.add_argument("--data-dir")
    args = parser.parse_args(argv)

    data_dir = get_data_dir(args.data_dir)
    if args.collect_once:
        ensure_service_output_streams()
        from speedtest_dashboard import collector

        if not collector.main(["--data-dir", str(data_dir)]):
            raise SystemExit(1)
    elif args.service:
        run_services(
            args.port,
            args.interval,
            data_dir,
            start_collector=not args.dashboard_only,
            controller_pid=args.controller_pid,
        )
    else:
        run_controller(args.interval, args.port, data_dir)


if __name__ == "__main__":
    main()
