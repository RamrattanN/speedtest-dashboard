# Troubleshooting

Common issues and fixes.

---

## ❌ Dashboard not opening
- Ensure dashboard window is running (`dashboard.py`)
- Open [http://localhost:8501](http://localhost:8501)

---

## ❌ Collector not writing data
- Check that `speedtest.exe` is installed and license accepted
- Ensure `speedtest_results.csv` is not locked by Dropbox sync

---

## ❌ Python not found
- Add Python 3.11+ to PATH
- Or pass full path using PowerShell `-Python` argument

---

## ❌ Dependency errors
Reinstall requirements:
```powershell
python -m pip install -r requirements.txt
```

---

## 📌 Tip
Always launch via `RunSpeedTest.bat` or `RunSpeedTest.ps1` instead of calling the scripts directly.
