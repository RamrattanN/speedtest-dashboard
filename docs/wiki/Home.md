# Speedtest Dashboard Wiki

Welcome to the **Speedtest Dashboard** documentation.  

This project continuously monitors internet performance (ping, download, upload) using **Ookla’s Speedtest CLI** (preferred) or **Python’s speedtest-cli** fallback.  
Results are stored in CSV files (30-day rolling main file plus optional monthly archives) and displayed via a Streamlit dashboard.

---

## 🚀 Quick Start
The easiest way to launch the system is from the project root:

- **Batch (independent):**
  ```bat
  RunSpeedTest.bat
  ```
  Runs both collector and dashboard with a default interval of 120 seconds.

- **PowerShell (preferred, configurable):**
  ```powershell
  .\RunSpeedTest.ps1 -Interval 120 -Port 8501
  ```
  Supports extra options like custom Python path, headless mode, and port selection.

Once launched, open: [http://localhost:8501](http://localhost:8501)

---

## 📚 Documentation

- [Getting Started](Getting-Started.md)  
- [Configuration](Configuration.md)  
- [Running the Dashboard](Running-the-Dashboard.md)  
- [Customization](Customization.md)  
- [Troubleshooting](Troubleshooting.md)  
- [Roadmap](Roadmap.md)  
- [Credits](Credits.md)  

---

## 📝 Notes
- Default colors: Upload `#8BDCCD`, Download `#1976D2`, Ping `#20B9D8`
- Default timezone: America/Chicago (changeable via dropdown in dashboard)
- Supports Light / Dark / Auto themes
- Data retention: ~30 days in main CSV; rollover to monthly archives up to 12 months
