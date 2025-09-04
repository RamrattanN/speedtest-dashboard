# Troubleshooting

## Collector won’t start
- Check Python 3.11+ is installed
- Confirm `speedtest.exe` (Ookla CLI) is installed and on PATH
- If unavailable, fallback is `speedtest-cli`

## Dashboard not loading
- Run: `python -m streamlit run dashboard.py`
- Ensure Streamlit is installed: `pip show streamlit`

## File access errors
- Dropbox sync can lock `speedtest_results.csv`
- Close other apps or pause sync temporarily

## GitHub sync problems
Use:
```powershell
git fetch origin
git pull --rebase origin main
git push origin main
```
