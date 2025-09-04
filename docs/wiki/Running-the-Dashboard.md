# Running the Dashboard

The dashboard is powered by [Streamlit](https://streamlit.io/).

## Start the Collector
First, run the collector in a PowerShell window:

```powershell
python collector.py --daemon --interval 120
```

This writes results into `speedtest_results.csv`.

## Start the Dashboard
In another window, run:

```powershell
python -m streamlit run dashboard.py
```

By default the dashboard is available at:  
👉 [http://localhost:8501](http://localhost:8501)

## Batch/PowerShell Launchers
- **RunSpeedTest.bat**  
  Starts both collector and dashboard in separate windows.  
- **RunSpeedTest.ps1**  
  PowerShell launcher (with logging and easier scripting).
