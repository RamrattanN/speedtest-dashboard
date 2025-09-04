# Getting Started

This guide helps you set up and run the Speedtest Dashboard.

---

## ✅ Prerequisites
- Windows 10/11  
- Python 3.11+  
- [Ookla Speedtest CLI](https://www.speedtest.net/apps/cli) (recommended)  
- Git (to clone the repository)

---

## 📥 Installation

1. **Clone the repository**
   ```powershell
   git clone https://github.com/RamrattanN/speedtest-dashboard.git
   cd speedtest-dashboard
   ```

2. **Install dependencies** (first time only)
   ```powershell
   setup_venv.bat
   ```

---

## ▶️ Launching

### Option A — Batch (simple / independent)
```bat
RunSpeedTest.bat
```
Starts collector and dashboard with default interval (120 seconds).

### Option B — PowerShell (preferred)
```powershell
.\RunSpeedTest.ps1 -Interval 120 -Port 8501
```
Supports options for Python path, headless mode, and custom ports.

---

## 🌐 Dashboard Access
Once running, open: [http://localhost:8501](http://localhost:8501)
