# Changelog
All notable changes to this project will be documented in this file.  

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),  
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Placeholder section for upcoming features (historical overlays, multiple host support, etc.).

---

## [0.1.0] - 2025-08-14
### Added
- **Collector (`collector.py`)**: runs speedtests at configurable intervals, stores results in CSV.
- **Dashboard (`dashboard.py`)**: Streamlit web interface with:
  - Bar/Line chart toggle
  - Timezone selection
  - Auto-refresh/manual refresh
  - Light/Dark/Auto theme
  - Color selection for Upload/Download/Ping
  - Historical overlays (daily/weekly/monthly/yearly)
- **Launchers**:
  - `RunSpeedTest.ps1`: PowerShell launcher (preferred).
  - `RunSpeedTest.bat`: Batch launcher (legacy).
- **Documentation**:
  - `README.md` with badges, setup instructions, configuration options, and credits.
  - `LICENSE` (MIT).
  - `assets/dashboard_preview.png` preview screenshot.
- **Repository hygiene**:
  - `.gitignore` excluding CSVs, archives, tools, binaries, venv, and OS cruft.

### Changed
- Updated repo structure in documentation to reflect PowerShell launcher.
- Improved README with preview section and GitHub badges.

### Removed
- Legacy reference files (`speedtest.md`, `Baseline/`) excluded from repo.

---

## [0.0.1] - 2025-08-13
### Added
- Initial proof-of-concept with collector, dashboard, and simple batch launcher.
- Early iterations of requirements management and Streamlit UI.

---

[Unreleased]: https://github.com/RamrattanN/speedtest-dashboard/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/RamrattanN/speedtest-dashboard/releases/tag/v0.1.0
[0.0.1]: https://github.com/RamrattanN/speedtest-dashboard/releases/tag/v0.0.1
