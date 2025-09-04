# Configuration

The dashboard and collector can be customized for your needs.

---

## ⏱ Interval
- Default: 120 seconds (2 minutes)  
- Change via:
  - **Batch**: edit `RunSpeedTest.bat`
  - **PowerShell**: use `-Interval` argument

---

## 🌐 Dashboard Port
- Default: 8501  
- Change via `-Port` argument in PowerShell

---

## 🎨 Theme
- Options: Light / Dark / Auto (system-based)  
- Set in dashboard settings

---

## 🌍 Timezone
- Default: America/Chicago  
- Change via dropdown in dashboard

---

## 🎨 Colors
Default colors:
- Upload: `#8BDCCD`
- Download: `#1976D2`
- Ping: `#20B9D8`

Overlays use related but muted shades for clarity.

---

## 💾 Data Retention
- Main CSV: ~30 days of samples
- Archives: monthly CSVs up to 12 months
