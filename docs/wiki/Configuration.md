# Configuration

The Speedtest Dashboard can be configured to suit your environment and needs.

## Collector Options
- `--interval <seconds>`  
  How often to run tests (default: 120).  
  Example: `python collector.py --daemon --interval 600`

- `--daemon`  
  Run continuously in the background.

- `--server <id>`  
  Specify one or more Speedtest servers by ID. Leave blank for auto-select.

## Dashboard Settings
Accessible at the top of the dashboard in the **Settings** section:

- **Timezone** – Adjusts all charts to your local timezone.
- **Theme** – Auto (match Windows), Light, or Dark.
- **Colors** – Choose base colors for:
  - Download (default: #1976D2)  
  - Upload (default: #8BDCCD)  
  - Ping (default: #20B9D8)

## CSV Storage
- Main file: `speedtest_results.csv` (rolling ~30 days).  
- Archives: stored monthly (up to 12 months).  
- Normalization tools available in `tools/`.
