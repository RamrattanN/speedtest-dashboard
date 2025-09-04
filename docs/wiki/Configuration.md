# Configuration

## Collector
- Interval: configurable (default: 120 seconds)
- Run manually:
  ```powershell
  python collector.py --daemon --interval 600
  ```
- Results saved in `speedtest_results.csv`
- Main CSV keeps 30 days, archives maintain up to 12 months

## Dashboard
- Run the dashboard:
  ```powershell
  python -m streamlit run dashboard.py
  ```
- Or use the packaged launcher:
  ```powershell
  speedtest-dashboard --interval 120 --port 8501
  ```

## UI Settings
- **Theme:** Auto / Light / Dark
- **Timezone selector:** supports all IANA timezones
- **Color selection:** Upload / Download / Ping
- **Trend overlays:** Compare with previous day, week, month, or year
