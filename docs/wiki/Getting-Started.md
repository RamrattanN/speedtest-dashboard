# Getting Started

The Speedtest Dashboard is a **self-hosted internet monitoring tool**.  
It periodically runs speedtests, logs results into CSV, and visualizes them in a Streamlit dashboard.

## Requirements
- Windows 10/11 (PowerShell or CMD)
- Python 3.11+
- Git (for cloning the repo)
- [Ookla Speedtest CLI](https://www.speedtest.net/apps/cli) (preferred)
- Optional fallback: `speedtest-cli` Python package

## Installation
1. Clone the repo:
   ```powershell
   git clone https://github.com/RamrattanN/speedtest-dashboard.git
   cd speedtest-dashboard
   ```

2. Install dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```

3. (Optional) Create a virtual environment:
   ```powershell
   .\\setup_venv.bat
   ```

✅ You’re ready to run your first collector and dashboard!
