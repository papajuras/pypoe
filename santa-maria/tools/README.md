# santa-maria data tools — RePoE + PoB inventory pipeline

Repeatable, **exhaustive** pipeline that mirrors the RePoE poe1 export and
PoB data export, analyzes every file in full, and renders the inventory
report.

## Data flow

```
santa-maria/data/   (gitignored mirror, as-is files)
   ▲  download.py   (fetches git trees from GitHub API itself — no /tmp dumps)
santa-maria/cache/  (gitignored intermediates)
   ▲  vocab.py      → cache/stat_vocab.json, cache/conversion_hits.json
   ▲  analyze.py    → cache/analysis.json   (EXHAUSTIVE per-file scan)
   ▲  investigate.py → cache/investigations.json  (traces + resolution rates)
santa-maria/docs/data_inventory.md   (generated, gitignored)
   ▲  report.py     (renders from cache/ + data/ for JSON-Schemas)
   ▲  audit.py      (PHASE 1 SELF-AUDIT; non-zero exit on FAIL)
```

## Run

```sh
santa-maria/tools/run.sh            # all steps
santa-maria/tools/run.sh report     # any single step: download|vocab|analyze|investigate|report|audit
```

Re-runnable: `download.py` skips already-downloaded (non-empty) files and
rebuilds `data/manifest.json` (path → [size, sha1]).

## Snapshot integrity

- The download scope is **enforced in code** (`download.py` `scope_filter`):
  `.json` only, no `.min.json`, RePoE `data/` additionally excludes the 9
  language dirs and `Metadata/Terrain/`. The RePoE git `data/` tree at the
  recorded commit is taken as the authoritative equivalent of the published
  RePoE export (documented in `manifest.json._meta.scope`).
- The manifest is built from the **current download scope** (the planned file
  list), not from whatever exists on disk. `_meta` records upstream
  provenance (commit SHA + date per source) and the planned / downloaded-ok /
  missing / stale counts so the snapshot is auditable.
- Stale/out-of-scope files on disk are detected, reported, and excluded from
  the manifest (never silently part of the valid snapshot; not deleted).

## Exhaustiveness contract (Phase 1)

- **Schema**: every record, every field, every nested object, every array
  element, to full nesting depth. No `[:N]` sampling. The report renders
  keyed maps (`passives{}`, `per_level{}`, stat-id maps) **structurally
  compacted** to `{}`; the machine-readable cache (`analysis.json` →
  `keyed_maps`) is **lossless with respect to the observed schema** — for
  every keyed map it keeps the exact concrete key set, value types, per-shape
  child schemas and the number of distinct child shapes.
- **Cross-references**: every string value in every record is classified
  (stat-vocabulary membership, `stat_\d+` hashes, `Metadata/`/`Art/` paths,
  trade hashes, `id`/`*_id`/`*_key`/`*_hash` keys, `Unique`-embedded keys);
  **integer values ≥ 4 digits are detected as numeric reference candidates**
  (`numeric_id`/`trade_hash`), kept separate from resolution. Counts
  exhaustive; samples capped for display.
- **Conversion/scaling**: every key and string value scanned against the
  `common.SCAN_PATTERNS` vocabulary (broad, unfiltered). Each value is
  recorded under EVERY matching pattern; per-file contexts preserve path +
  key/value kind + counts, and `cache/stat_conversion_context.json` makes
  every stat-id match's source context recoverable without re-scanning raw
  files.
- **Examples**: first 5 records, serialized from parsed JSON and truncated —
  explicitly SAMPLED and NOT verbatim.
- **Validation**: manifest ↔ disk ↔ analyzed parity, parse errors, mismatch
  reporting, explicit Downloaded/Excluded scope statement, stale-file
  detection, snapshot provenance, `planned == downloaded_ok + missing`.
- **Special investigations**: Crown of Eyes (traced through mods.json,
  ModItemExclusive, ModCache, QueryMods, TradeSiteStats, Uniques text —
  per-candidate chain with explicit-vs-heuristic labels), Iron Will, Avatar
  of Fire, the exhaustive unique visual-id → mods linkage rate, and the PoB
  unique-mod pipeline, each reconstructed from the actual data
  (`investigate.py`).

## Tests

```sh
python3 santa-maria/tools/tests/test_tools.py
```

## Scope (filters in download.py)

- English only — the 9 language dirs are excluded
- `Metadata/Terrain/` (procedural tile graphs) excluded
- `.min.json` variants excluded
- Both the `repoe/` and `pob-data/poe1/` exports are mirrored

## Notes

- `common.py` holds `CONVERSION_PATTERNS` (order matters for the stat-id
  bucketing in `vocab.py`/the appendix) and `SCAN_PATTERNS` (exhaustive
  per-file scan), `REF_CLASSES`/`KEY_CLASSES` (cross-reference taxonomy), and
  the keyed-map heuristic constants.
- `docs/data_inventory.md` is regenerated idempotently and **gitignored**.
- The report and audit must agree: `audit.py` exits 1 if any checklist item
  FAILs.
