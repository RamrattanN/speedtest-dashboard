# Changelog
All notable changes to this project are documented here.  

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)  
and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]
### Added
- macOS launcher and step-by-step Mac acceptance guide.
- Ready-made VS Code workspace, tasks, debugging profiles, and setup guide.
- Configurable cross-platform data directory with a visible home-folder default.
- Offline automated tests and GitHub Actions CI.
- Ramrattan-styled application header, latest-result cards, and compact content panels.
- Non-modal Rentals-style right sidebar Help for setup, controls, result interpretation, and troubleshooting.
- Packaged Ramrattan logo reused from the Rentals application.
- Unsigned macOS Intel pilot packaging with a native controller, bundled
  Python runtime, disk-image build script, and GitHub Actions artifact workflow.
- Pilot packaging and acceptance guide for controlled distribution.
- Unsigned Windows x64 Pilot 1 packaging with a native controller, per-user
  installer, Start menu shortcut, embedded version metadata, and GitHub Actions
  installed-app smoke test.
- Windows pilot packaging and acceptance guide.

### Changed
- Consolidated the collector and dashboard into the installable Python package.
- Dashboard controls, filters, chart, and summary now use a tighter card-based layout.
- Interactive controls now use the Ramrattan navy and blue palette instead of Streamlit red.
- Help now detects desktop packaging and replaces developer Terminal commands
  with Applications-folder, controller, browser, and safe-quit guidance.
- Packaged Help now covers pilot installation and replacement, unsigned-app
  security handling, local data privacy, and controller-based operation.
- README and wiki documentation now identify macOS Intel Pilot 3 as the current
  downloadable release and distinguish it from source-based developer use.
- Packaged Help now selects macOS or Windows installation, security, launch,
  and restart guidance at runtime.

### Removed
- Retired the legacy `RunSpeedTest.ps1` and `RunSpeedTest.bat` launchers.  The
  installable Python command remains available for Windows development.

### Fixed
- The windowed Windows service now restores writable output streams before
  starting the collector, preventing its background thread from stopping
  silently before the first measurement.
- Packaged macOS builds now force Streamlit production mode so the dashboard
  and its static frontend are both served on the selected local port instead
  of incorrectly expecting a development frontend on port 3000.
- The macOS packaging workflow now launches the finished application and
  verifies the dashboard root route before publishing its disk image.
- Pilot artifacts, disk images, application metadata, controller text, and
  startup logs now carry an explicit Pilot 3 identifier to prevent stale-build
  installation during acceptance testing.
- Installed console commands no longer depend on missing repository-root files.
- Removed the hardcoded personal Dropbox path from the application.
- Collector startup now creates the configured data directory without referencing
  the removed legacy `ROOT` variable.
- A detected but failing Ookla CLI now falls back to Python `speedtest-cli`
  unless `--require-ookla` is specified.
- Python collection now selects certifi's CA bundle when the interpreter has no
  usable default certificate file, while preserving explicit overrides.
- Replaced the third-party browser auto-refresh component with Streamlit's
  native timed fragment to prevent blank pages after the 60-second refresh.
- Updated chart and table width configuration for current Streamlit releases.
- The dashboard now redraws its data directly every 60 seconds without a browser refresh.
- Newly discovered speed-test servers remain visible during automatic redraws.

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
