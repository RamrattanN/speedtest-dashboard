# Speedtest Dashboard  

![License](https://img.shields.io/badge/License-MIT-blue.svg)  
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)  
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B)  
![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-lightgrey)  
[![Docs](https://img.shields.io/badge/Docs-Wiki-blue)](docs/wiki/SUMMARY.md)  
[![Release](https://img.shields.io/github/v/release/RamrattanN/speedtest-dashboard?sort=semver)](https://github.com/RamrattanN/speedtest-dashboard/releases)  
[![Changelog](https://img.shields.io/badge/Changelog-md-blue)](CHANGELOG.md)

A self-hosted internet speed monitoring tool.  
It collects ping, download, and upload speeds periodically using **Ookla’s Speedtest CLI** (preferred) or the **Python speedtest-cli library** (fallback).  
Results are stored in CSV format and visualized via a Streamlit dashboard.

---

## ✨ Features
- Configurable test interval (default: 2 minutes).
- Retains ~30 days of data in the main CSV; archives up to 12 months.
- Dashboard options:
  - Bar / Line chart toggle
  - Timezone selector
  - Auto-refresh or manual refresh
  - Historical overlays (hourly, daily, weekly, monthly, yearly)
  - Customizable colors (Download, Upload, Ping)
  - Light/Dark/Auto theme
- Multi-server support.
- Launchers:
  - `RunSpeedTest.ps1` (PowerShell, preferred)
  - `RunSpeedTest.bat` (independent batch script)

---

## 📸 Preview
![Speedtest Dashboard Screenshot](assets/dashboard_preview.png?v=2025-09-04-1)

---

## 📂 Repository Structure
```
speedtest-dashboard/
├── collector.py         # Collector script (runs tests, writes results)
├── dashboard.py         # Streamlit UI
├── RunSpeedTest.ps1     # PowerShell launcher (preferred)
├── RunSpeedTest.bat     # Batch launcher (independent)
├── requirements.txt     # Python dependencies
├── setup_venv.bat       # Local venv + deps
├── assets/              # Images/screenshots
├── docs/wiki/           # Project Wiki
├── .github/             # Issue/PR templates
├── LICENSE
└── README.md
```

---

## ⚡ Quick Start (Windows)

1. **Clone this repository**
   ```powershell
   git clone https://github.com/RamrattanN/speedtest-dashboard.git
   cd speedtest-dashboard
   ```

2. **Install dependencies** (one-time)
   ```powershell
   setup_venv.bat
   ```

3. **Run the system**

   **PowerShell (preferred):**
   ```powershell
   .\RunSpeedTest.ps1 -Interval 120 -Port 8501
   ```
   Opens two windows:
   - Collector (tests every 2 minutes)
   - Dashboard (http://localhost:8501)

   **Batch (independent):**
   ```bat
   RunSpeedTest.bat
   ```

---

## ⚙️ Configuration

- **Interval**: `-Interval` in PowerShell, or edit `.bat`  
- **Dashboard port**: `-Port` in PowerShell  
- **Headless mode**: `.\RunSpeedTest.ps1 -Headless`  
- **Python exe**: `-Python` in PowerShell  
- **Theme**: Light / Dark / Auto  
- **Timezone**: user-selectable dropdown  
- **Default colors**:
  - Upload: `#8BDCCD`
  - Download: `#1976D2`
  - Ping: `#20B9D8`

---

## 📚 Documentation
See the [Wiki](docs/wiki/SUMMARY.md) for full guides:

- [Getting Started](docs/wiki/Getting-Started.md)  
- [Configuration](docs/wiki/Configuration.md)  
- [Running the Dashboard](docs/wiki/Running-the-Dashboard.md)  
- [Customization](docs/wiki/Customization.md)  
- [Troubleshooting](docs/wiki/Troubleshooting.md)  
- [Roadmap](docs/wiki/Roadmap.md)  
- [Credits](docs/wiki/Credits.md)  

---

## 🔧 Requirements
- Windows 10/11  
- Python 3.11+  
- [Ookla Speedtest CLI](https://www.speedtest.net/apps/cli) (recommended)  
- Dependencies from `requirements.txt`

---

## 📝 License
Licensed under MIT (see [LICENSE](LICENSE)).  
Ookla’s license applies for Speedtest data usage.

---

## 🙌 Credits
- **Concept & Direction** — Nilesh Ramrattan  
- **Development** — assisted by ChatGPT (OpenAI)  
- **Stack** — Ookla Speedtest CLI, Streamlit, pandas, numpy, plotly
