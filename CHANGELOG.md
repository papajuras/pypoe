# Changelog

## [0.1.0] - 2026-07-23

### Added

- **Crafting macro** — Alt/Aug/Regal/Exalt automator with affix browser,
  influence detection, profile management, and 2/3 screen position modes
- **Flip monitor** — Trade price fetcher with proactive rate limiting,
  poe.ninja integration (Currency, DivinationCard), liquid/illiquid split,
  sortable profit table with 3-second auto-refresh
- **Freshness indicator** — Refresh buttons show data age via green-to-red
  hue gradient (hover for exact hours), click pushes flip to front of queue
- **Rate limiting** — Multi-tier backoff, jitter, 429 Cloudflare detection,
  12 unit tests verifying correct behavior against live API patterns
- **SQLite store** — Versioned schema migrations, price history table,
  60-day automatic prune, CLI tool for inspection
- **Native window + system tray** — PySide6 tray icon (Fedora KDE compatible),
  subprocess-based window reopen, tooltip with queue state
- **Base-type flip generator** — Body armour, helmet, gloves, boots with
  quality filters (Q27–Q30), high-ilvl trade queries
- **Unit tests** — 30 tests covering throttle logic, pricer queue processing,
  store queries, and front-of-queue ordering
