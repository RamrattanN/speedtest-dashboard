# Troubleshooting

Common problems and fixes.

## Dashboard not loading
- Ensure collector is running and writing to `speedtest_results.csv`.
- Check `streamlit` is installed: `pip install streamlit`.

## Collector errors
- `PermissionError: Access is denied`  
  → Make sure Dropbox/OneDrive isn’t locking the file. Try saving to a local folder.

- `HTTP Error 403: Forbidden`  
  → Switch from `speedtest-cli` to Ookla CLI (`speedtest.exe`) or vice versa.

## Port conflict
If `http://localhost:8501` is unavailable:
- Check for another Streamlit instance:  
  `netstat -ano | findstr :8501`
- Kill the process, or start on a new port:  
  `streamlit run dashboard.py --server.port 8502`
