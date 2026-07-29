# pypoe — Path of Exile personal sidecar

Personal utility for Path of Exile crafting and economy monitoring.

## Features

### 1. Alt/Aug/Regal/Exalt crafting spammer
Automates orb usage with configurable stop criteria.
- Alt-spams items, augments when hitting desired mods, regals/exalts based on match count
- Profiles define which prefix/suffix mods to look for (saved to db/crafting.json)
- Influenced mods detected automatically from spawn weight tags
- Game-accurate display text from RePoE stat_translations.json
- Hotkeys: Ctrl+J to start spam, ESC to stop
- Debug button shows current prefix/suffix match arrays

### 2. PoE Trade flipping (flipper/)
Flipping opportunity monitor with automated price fetching.
- Flips defined by source (buy) + target (sell) trade queries, multiplier, cost
- TradeClient with strict rate limiting (stagger + buffer, parses X-Rate-Limit-* headers)
- PriceFetcher scans DB every 120s for oldest-unpriced flips (3h min age), fetches live prices via worker thread
- Source: average of 5 cheapest divine listings. Target: cheapest single divine listing.
- Liquid/illiquid split, sortable by cost/profit/profit%, auto-refresh every 3s
- poe.ninja integration: items priced via ninja API (DivinationCard, Currency) with ETag cache
- SQLite store with schema migrations, price history table, 60-day auto-prune
- Native window mode (pywebview + PySide6)

## Tech stack
- Python 3.13, uv for package management
- NiceGUI for UI (Quasar/Material Design)
- pyautogui / pynput / keyboard for automation
- JSON-backed config store (db/crafting.json)
- SQLite via stdlib, requests, websockets for PoE Trade API

## Project structure
- `main.py` — NiceGUI web UI entry point (split layout: crafting left, flipper right)
- `crafting/` — core crafting module
  - `session.py` — CraftingSession orchestrator, Positions/Settings dataclasses
  - `actions.py` — low-level mouse/keyboard orb/item automation
  - `matching.py` — prefix/suffix matching utilities
- `flipper/` — flipping module
  - `client.py` — TradeClient with rate limiting, search/fetch/live API
  - `store.py` — Flip dataclass, Store (SQLite), price/history, migrations
  - `pricer.py` — PriceFetcher with scanner + worker threads
  - `ninja.py` — NinjaClient with ETag cache for poe.ninja API
  - `ui.py` — FlipperPanel: sortable tables, profit calc, form, auto-refresh
  - `test_throttle.py` — 17 tests for rate limiting logic
  - `test_pricer.py` — 10 tests for sequential queue processing
- `db/` — data layer
  - `config.py` — JSON config store with per-profile settings (auto-save, migration)
  - `affixes.py` — RePoE affix data (mods.json + stat_translations.json, cached daily)
  - `schema.py` — versioned SQLite schema migrations
  - `tool.py` — CLI to inspect/manipulate flips.db
  - `crafting.json` — persisted crafting config
  - `cache/` — downloaded RePoE data
  - `flips.db` — flips, prices, price_history
- `bin/` — scripts
  - `cleanup-vpn.sh` — undo VPN namespace, veth, iptables (run after crash/SIGKILL)
- `tmp/` — clipboard dumps, test output
- `test_life_block.py` — influenced mod matching tests

## Current state (save 2026-07-28)

### What works
- Full crafting macro with affix browser, influence detection, 2/3 screen modes
- TradeClient with proactive rate limiting (stagger, 1s min gap before headers, multi-tier, 429 exits immediately)
- Flip CRUD with name, source/target type (query or ninja), multiplier (4-digit), cost
- PriceFetcher: scanner every 120s queues 10 oldest-unpriced flips, 3-hour minimum age (manual refresh overrides)
- Source: average of 5 cheapest divine listings. Target: cheapest single divine listing.
- poe.ninja: NinjaClient with ETag + stale-while-revalidate cache, Currency/DivinationCard types
- Liquid/illiquid split tables, sortable columns (cost/profit/profit%), green/red coloring
- Auto-refresh every 3s (pauses during form editing)
- Native window via pywebview + PySide6
- Schema migrations (V1: flips, V2: prices + history + indexes)
- 60-day price history auto-prune
- 17 throttle tests, 10 pricer tests passing (1 pre-existing mock path error in throttle)
- VPN netns isolation verified: host traffic uses normal gateway, only pypoe PID goes through WireGuard tunnel — separate IP, separate rate limit bucket
- `bin/cleanup-vpn.sh`: sudo-friendly script to undo all VPN artifacts after crash/SIGKILL
- db/tool.py: list, search, dump flips from CLI

### Removed
- `profiles.py` (seed data — JSON is the only source of truth)
- `use_aug` toggle (augmentation is always used)
- Old free-text prefix/suffix chip input (replaced by affix browser)
- `seed_from_profiles` function

### ⚠️ Hard rules
- **NEVER delete or clear db/flips.db** — contains real data
- **NEVER delete or clear db/crafting.json** — contains real crafting profiles
- **NEVER clear data just because schema changed** — use schema.py migrations instead

### Known issues / TODOs
- Need to test full regal/exalt flow in-game
- Live trade WebSocket not wired
- 40 flips from generator (10 bases × 4 qualities), no split variants (split beasts removed in new league), multiplier 0.5 for all, cost 1
- poe.ninja item_options could add more categories (BaseType, Unique, etc.)
- 1 pre-existing throttle test error: `patch('flipper.client.time', ...)` path doesn't resolve with `src/` layout

### How to run
```
./run.sh    # or: uv run python main.py
```
Server starts on http://localhost:8080 (native window with pywebview)

`run.sh` creates a **WireGuard VPN network namespace** (`pypoe-vpn`, veth pair, NAT masquerade) and launches `main.py --tray-only` inside it. This forces all PoE Trade API traffic through the VPN to avoid rate-limit bans. Runs as root via sudo; cleanup trap handles crash recovery (iptables, netns, ip_forward).

### Run tests
```
PYTHONPATH=src uv run python -m pypoe.flipper.test_throttle
PYTHONPATH=src uv run python -m pypoe.flipper.test_pricer
```
