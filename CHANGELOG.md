# Changelog
All notable changes to this project are documented here.  

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)  
and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]
### Planned
- Additional overlay controls
- Multi-host visualization
- GitHub Actions for automated checks
- Windows Task Scheduler helper

---

## [0.1.1] - 2025-09-04
### Changed
- **Batch launcher**: `RunSpeedTest.bat` made fully independent (not a wrapper).
- **Docs**: Updated README and links to wiki pages.

### Added
- Enhanced PowerShell launcher (`RunSpeedTest.ps1`) with clearer args and defaults.
- Regenerated `.github` issue and PR templates.
- Wiki pages re-synced and added Home.md.

---

## [0.1.0] - 2025-08-14
### Added
- Collector (`collector.py`) — runs speedtests at configurable intervals, stores results in CSV.
- Dashboard (`dashboard.py`) — Streamlit UI:
  - Bar/Line toggle
  - Timezone selection
  - Auto/manual refresh
  - Light/Dark/Auto theme
  - Color selection
  - Historical overlays
- Launchers:
  - `RunSpeedTest.ps1` (PowerShell, preferred)
  - `RunSpeedTest.bat` (initial batch version)
- Docs:
  - `README.md`, `LICENSE`, preview screenshot
- Repo hygiene: `.gitignore` for results, tools, binaries, venv, OS cruft

---

## [0.0.1] - 2025-08-13
### Added
- Initial proof-of-concept (collector, dashboard, simple batch launcher).
- Early requirements management and Streamlit UI.

---

[Unreleased]: https://github.com/RamrattanN/speedtest-dashboard/compare/v0.1.1...HEAD  
[0.1.1]: https://github.com/RamrattanN/speedtest-dashboard/compare/v0.1.0...v0.1.1  
[0.1.0]: https://github.com/RamrattanN/speedtest-dashboard/releases/tag/v0.1.0  
[0.0.1]: https://github.com/RamrattanN/speedtest-dashboard/releases/tag/v0.0.1  
