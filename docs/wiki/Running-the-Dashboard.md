# Running the Dashboard

There are multiple ways to run the system:

## 1. Combined (Collector + Dashboard)
```powershell
speedtest-dashboard --interval 120 --port 8501
```

## 2. Collector only
```powershell
speedtest-collector --daemon --interval 120
```

## 3. Dashboard only
```powershell
speedtest-dashboard-ui --server.port 8501
```

📍 Once running, open your browser at:  
[http://localhost:8501](http://localhost:8501)
