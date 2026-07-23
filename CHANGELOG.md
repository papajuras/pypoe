# Changelog

## [0.2.0] - 2026-07-23

### Added

- **Stale section** — Flips with no price data or data older than 4 hours
  are grouped in a muted "Stale" section at the bottom of the flip panel
- **Rate limit persistence** — Rate limit labels persist across API calls
  keyed by tier (e.g. `ip/10s`, `ip/60s`, `ip/300s`), never flicker or grow
- **Last sleep indicator** — Most recent enforced API cooldown shown in
  the rate limit header row
- **Actions column cleanup** — Header label no longer wraps to next line

### Changed

- **Project structure** — Source code moved to `src/pypoe/` layout with
  `main.py` as the root entry point; `crafting/`, `db/`, `flipper/`,
  `config.py`, `tray.py`, `window.py` live under `src/pypoe/`
- **Api jitter halved** — Rate limiting jitter reduced from 2–5s to 1.0–2.5s
  for faster throughput

### Fixed

- **White screen on startup** — Native window now renders correctly with
  the restructured project layout

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
