# Troubleshooting

## Dashboard does not open

- Confirm the launcher is still running.
- Open <http://localhost:8501> manually.
- Check whether another application is using port 8501.
- In VS Code, run the **Dashboard only** debug configuration and review the
  integrated Terminal.

## Collector does not write data

- Review the collector output for `403`, `Forbidden`, license, or connection
  errors.
- Install the official Ookla Speedtest CLI if the Python fallback is blocked.
- Confirm the data directory is writable.
- Confirm `speedtest_results.csv` is not open in an application that locks it.

## Python is not found

Install Python 3.11 or newer, restart Terminal or VS Code, and run setup again.

## Dependency or environment errors

On macOS, recreate the local environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[test]"
```

On Windows, run:

```bat
setup_venv.bat
```

## Mac launcher is blocked

From the project folder, run:

```bash
chmod +x RunSpeedTest.command
./RunSpeedTest.command
```

## Information to capture

Copy the complete error and provide your Python version, Mac processor type or
Windows version, current Git commit, and whether the failure affected the
collector, dashboard, or both.
