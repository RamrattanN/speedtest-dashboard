# Changelog
All notable changes to this project are documented here.  

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)  
and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- A header **Run speed test** action that requests one immediate measurement
  without launching overlapping collectors.  Repeated requests coalesce while
  one request is pending.
- A sortable table of the latest 150 measurements in the selected dashboard
  window.
- A two-step data reset that clears the main CSV and monthly archives, preserves
  application settings, and requests a fresh measurement cycle.

### Changed
- Ping now uses a dashed line and diamond markers, while download and upload
  use distinct marker shapes.  Both Y-axes include zero so independently
  scaled two-sample series do not completely conceal one another.
- Measurement retention now uses a rolling 365-day boundary across the main
  CSV and monthly archives.
- Chart zoom gestures are limited to the time axis so speed and ping scales
  cannot be changed accidentally.
- The chart-type selector now sits directly below the chart it controls.
- The visible refresh-schedule toggle has been removed.  The dashboard still
  checks for new data every 60 seconds, while an always-available refresh icon
  in the header provides an immediate reload.
- Implausible or corrupt latency values are rejected before collection and
  excluded from existing dashboard history so they cannot distort the chart.

## [1.1.0] - 2026-09-21
### Added
- Production engine controls and official Ookla CLI discovery for Windows x64,
  macOS Intel, and macOS Apple silicon.
- Verified executable detection that rejects the unrelated Python command with
  the same `speedtest` filename.
- Visible collector states for setup required, testing, healthy, and failed
  measurement cycles.
- A dedicated Measurement Engine Wiki page and aligned installation guidance.

### Changed
- The official Ookla CLI is now required by default for production
  measurements.  Python fallback requires an explicit Compatibility mode
  selection.
- Packaged GUI applications search saved settings, an environment override,
  `PATH`, and standard platform locations for the official executable.
- Missing-engine conditions pause new measurements without stopping the
  controller or local dashboard.
- All Windows x64, macOS Intel, and macOS Apple silicon artifacts now use
  version 1.1.0.

### Security
- Ookla's executable is not redistributed because an explicit redistribution
  grant was not confirmed.  Users obtain it directly from Ookla and its terms
  continue to apply.

## [1.0.1] - 2026-09-21
### Added
- Both macOS disk images now include a plain-text first-launch security guide
  that remains readable when Gatekeeper blocks executable files.
- All platforms now provide optional preferred city-or-region server
  calibration while retaining automatic selection as the universal default.
- Regional calibration stores multiple local candidates so collection can
  fail over without hardcoding a city for every user.
- Windows runs each measurement in a disposable child process with a
  three-minute safety timeout and automatic continuation on the next cycle.

### Changed
- macOS installation guidance now explains that the optional unsigned approval
  helper may require its own **Open Anyway** approval before it can run.
- README, packaged Help, packaging guides, and Wiki pages now use the same
  macOS Gatekeeper sequence and identify version 1.0.1 as the current release.
- Windows and both macOS packages now share patch version 1.0.1.
- Preferred server settings are stored locally in the existing results folder.
- Windows schedules measurement starts at the configured interval instead of
  adding the full interval after test completion.
- Latest Result now includes minimum, average, and peak rows for the active
  time window and server filters.
- Latest Result now identifies the measurement engine so official Ookla CLI
  samples can be distinguished from Python fallback samples.

### Fixed
- Corrected first-launch instructions that previously implied the unsigned
  macOS approval helper could always execute before Gatekeeper approval.
- macOS release builds now rerun when installer guidance files change.
- A frozen Windows speed-test backend can no longer indefinitely block later
  measurements or require Task Manager to release its descendant processes.
- Windows Quit Monitor now terminates the complete packaged service process
  tree, including any active measurement child.
- Python fallback requests now use bounded network timeouts on every platform.

## [1.0.0] - 2026-09-21
### Added
- macOS launcher and step-by-step Mac acceptance guide.
- Ready-made VS Code workspace, tasks, debugging profiles, and setup guide.
- Configurable cross-platform data directory with a visible home-folder default.
- Offline automated tests and GitHub Actions CI.
- Ramrattan-styled application header, latest-result cards, and compact content panels.
- Non-modal Rentals-style right sidebar Help for setup, controls, result interpretation, and troubleshooting.
- Packaged Ramrattan logo reused from the Rentals application.
- Unsigned macOS Intel 1.0.0 packaging with a native controller, bundled
  Python runtime, disk-image build script, and GitHub Actions artifact workflow.
- Native Apple silicon ARM64 release with architecture-specific disk
  image naming and a packaged dashboard smoke test.
- Unsigned Windows x64 1.0.0 packaging with a native controller, per-user
  installer, Start menu shortcut, embedded version metadata, and GitHub Actions
  installed-app smoke test.
- Windows installer maintenance choices for Repair and Uninstall completely.
- Production packaging, acceptance, troubleshooting, and Wiki documentation.

### Changed
- Consolidated the collector and dashboard into the installable Python package.
- Dashboard controls, filters, chart, and summary now use a tighter card-based layout.
- Interactive controls now use the Ramrattan navy and blue palette instead of Streamlit red.
- Help now detects desktop packaging and replaces developer Terminal commands
  with Applications-folder, controller, browser, and safe-quit guidance.
- Packaged Help now covers installation and replacement, unsigned-app
  security handling, local data privacy, and controller-based operation.
- README and Wiki documentation identify unsigned macOS Intel, macOS Apple
  silicon, and Windows x64 1.0.0 as the current downloadable applications and distinguish them from
  source-based developer use.
- Packaged Help now selects macOS or Windows installation, security, launch,
  and restart guidance at runtime.
- Connection Overview now follows Latest Result on every platform.
- All desktop packages, controllers, artifacts, and user documentation use the
  same production version number, 1.0.0.
- macOS disk images include an optional, confirmation-gated approval helper
  that removes quarantine only from the installed application and opens it.

### Removed
- Retired the legacy `RunSpeedTest.ps1` and `RunSpeedTest.bat` launchers.  The
  installable Python command remains available for Windows development.

### Fixed
- Chart-type changes now force a full dashboard redraw so Bar and Line / Curve
  selections apply reliably in packaged desktop applications.
- **Refresh now** is disabled while automatic 60-second refresh is enabled and
  becomes available when automatic refresh is turned off.
- Windows service logging now forces UTF-8 before the collector starts, avoiding
  a CP1252 encoding failure that stopped collection when status text contained
  Unicode characters.
- Windows service logging is line-buffered so completed measurements appear in
  `monitor.log` immediately during soak testing.
- The windowed Windows service now restores writable output streams before
  starting the collector, preventing its background thread from stopping
  silently before the first measurement.
- The browser tab now uses the Ramrattan logo, Help is an icon in the branded
  header, and the manual refresh action uses a navy primary-button treatment.
- The header Help control now renders as a compact, visible icon button across
  packaged macOS and Windows apps.
- Latest Result now appears between Performance Trend and Window Summary.
- Packaged Help now renders installation steps as a proper ordered list instead
  of exposing raw HTML list tags.
- Packaged macOS builds now force Streamlit production mode so the dashboard
  and its static frontend are both served on the selected local port instead
  of incorrectly expecting a development frontend on port 3000.
- The macOS packaging workflow now launches the finished application and
  verifies the dashboard root route before publishing its disk image.
- Production artifacts, application metadata, controller text, and startup
  logs now carry version 1.0.0 consistently.
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

[Unreleased]: https://github.com/RamrattanN/speedtest-dashboard/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/RamrattanN/speedtest-dashboard/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/RamrattanN/speedtest-dashboard/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/RamrattanN/speedtest-dashboard/compare/v0.1.1...v1.0.0
[0.1.1]: https://github.com/RamrattanN/speedtest-dashboard/compare/v0.1.0...v0.1.1  
[0.1.0]: https://github.com/RamrattanN/speedtest-dashboard/releases/tag/v0.1.0  
[0.0.1]: https://github.com/RamrattanN/speedtest-dashboard/releases/tag/v0.0.1  
