# Roadmap

## Version 1.1.0 QA candidate

- Cross-platform Python collector and local CSV retention.
- Ramrattan-branded dashboard with latest-result cards, trends, summaries, and
  header Help.
- Unsigned macOS Intel and Apple silicon disk images, plus a Windows x64
  per-user installer.
- Automated Apple silicon ARM64 release.
- Windows Repair and Uninstall maintenance choices.
- Location-neutral automatic server selection with optional regional
  calibration and failover candidates.
- Timeout-protected Windows measurements with process-tree cleanup and
  automatic recovery.
- Automated package builds and installed-application smoke tests.
- Automatic 60-second display refresh with an always-available manual reload.
- Safe on-demand measurement requests that coalesce and never launch
  overlapping collectors.
- Cross-platform singleton protection for controllers and collectors sharing a
  results folder.
- Plain-text macOS Gatekeeper instructions covering both the application and
  the optional approval helper.
- Official-only production measurements with verified native CLI discovery,
  explicit compatibility mode, and visible collector health.

## Next

- Complete pre-release soak testing on representative macOS Intel and Windows
  x64 systems.
- Validate the ARM64 build on a physical Apple silicon Mac.
- Publish version 1.1.0 installers with checksums and release notes after QA
  approval.

## Later releases

- Optional code signing and Apple notarization when paid signing is justified.
- Windows code signing when paid signing is justified.
- Launch-at-login option.
- Automatic application updates.
- Persisted dashboard preferences.
- Multiple-host visualisation.
