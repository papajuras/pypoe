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

### 2. poe.ninja flipping monitoring (TODO)
### 3. PoE Trade flipping monitoring (TODO)

## Tech stack
- Python 3.13, uv for package management
- NiceGUI for UI (Quasar/Material Design)
- pyautogui / pynput / keyboard for automation
- JSON-backed config store (db/crafting.json)

## Project structure
- `main.py` — NiceGUI web UI entry point
- `crafting/` — core crafting module
  - `session.py` — CraftingSession orchestrator, Positions/Settings dataclasses
  - `actions.py` — low-level mouse/keyboard orb/item automation
  - `matching.py` — prefix/suffix matching utilities
- `db/` — data layer
  - `config.py` — JSON config store with per-profile settings (auto-save, migration)
  - `affixes.py` — RePoE affix data (mods.json + stat_translations.json, cached daily), item type filtering, builder search
  - `crafting.json` — persisted config (prefixes, suffixes, item_type, orb settings, metadata)
  - `cache/` — downloaded RePoE data (mods.json, stat_translations.json)
- `tmp/exalts/` — clipboard dumps from exalt orb results
- `test_life_block.py` — influenced mod matching tests

## Current state (save 2026-07-18)

### What works
- Main UI has affix browser with filterable multi-select dropdowns and item type per profile
- Influenced mods (Shaper/Elder/Crusader/Warlord/Hunter/Redeemer) detected and tagged via spawn weight analysis
- Game-exact display text from RePoE stat_translations.json, with values filled in
- Search text saved to profile uses game wording (text after last stat placeholder) for substring matching against item clipboard
- 1H/2H weapon distinction handled via `one_hand_weapon`/`two_hand_weapon` exclusion tags
- Creation modal: name + item type, then edit affixes in main UI
- Config auto-saves on every change to db/crafting.json
- Selected profile and screen mode persist across restarts
- Aug is always on (removed toggle)
- Regal/Exalt orb behaviour configurable
- CraftingSession orchestrates alt-spam with aug/regal/exalt flow
- Transmute after regal/exalt failure: sets `_needs_transmute` flag
- Exalt clipboard dumps saved to `tmp/exalts/`

### Removed
- `profiles.py` (seed data — JSON is the only source of truth)
- `use_aug` toggle (augmentation is always used)
- Old free-text prefix/suffix chip input (replaced by affix browser)
- `seed_from_profiles` function

### Known issues / TODOs
- Need to test full regal/exalt flow in-game
- Flipping monitoring (poe.ninja + PoE Trade) not started yet

### How to run
```
./run.sh    # or: uv run python main.py
```
Server starts on http://localhost:8080
