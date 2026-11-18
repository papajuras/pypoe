# santa-maria data tools — RePoE + PoB inventory pipeline

Repeatable, **exhaustive** pipeline that mirrors the RePoE poe1 export and
PoB data export, analyzes every file in full, and renders the inventory
report.

## Data flow

```
santa-maria/data/   (gitignored mirror, as-is files)
   ▲  phase1_download.py   (fetches git trees from GitHub API itself — no /tmp dumps)
santa-maria/cache/  (gitignored intermediates)
   ▲  phase1_vocab.py      → cache/stat_vocab.json, cache/conversion_hits.json
   ▲  phase1_analyze.py    → cache/analysis.json   (EXHAUSTIVE per-file scan)
   ▲  phase1_investigate.py → cache/investigations.json  (traces + resolution rates)
santa-maria/docs/data_inventory.md   (generated, gitignored)
   ▲  phase1_report.py     (renders from cache/ + data/ for JSON-Schemas)
   ▲  phase1_audit.py      (PHASE 1 SELF-AUDIT; non-zero exit on FAIL)
```

## Opaque-marker semantic extraction (Phase 4M)

Runs between node extraction and edge extraction (`run_pipeline.sh` step 5/6).

```
tools/annotations/phase4_semantic_annotations.json   (committed curated ground truth,
                                                     202 core opaque markers)
cache/nodes.db + cache/raw_records.db                (deterministic corpus regen)
   ▲  phase4_markers_extract.py
cache/semantic_markers.json   (semantic intermediate; textual labels only, no edges)
docs/phase4_semantic_extraction.md   (generated summary)
```

Contract: seven operators (REDIRECT / SUBSTITUTE / CONVERT / DERIVE / EQUAL /
COUNT_AS / SUPPRESS), frozen. The regenerated marker set MUST equal the
committed annotation key set; drift fails the run. Labels ("Mana", "Energy
Shield", "Strength") are textual semantic labels, never KB node ids; no graph
edges or candidate pairs are emitted here.


## Semantic binding extraction (Phase 5S)

Runs immediately after edge extraction (`run_pipeline.sh` step 7/7).

```
cache/semantic_markers.json + cache/nodes.db + data/repoe/stat_translations/
   ▲  phase5s_semantic_bind.py
cache/edges.db            (adds ONE relationship class: sem_relation_binds)
cache/sem_binding_coverage.json   (every participant resolution outcome)
```

Contract: `docs/phase5s_semantic_binding_contract.json` (v5S.1, frozen). A
binding means ONLY: the Phase 4M participant explicitly refers to this KB
concept — never an interaction claim. M1_tag (phrase → existing Tag node,
`confirmed`), **M2b_stat** (contract 5S.2: phrase tokens must head an existing
Stat ID with only an approved magnitude-tail remainder — `+%`/`%`/`+`/
`per_minute`/`per_second` — singleton required, leading `all ` quantifier
stripped; `resolved_not_validated`) and M2_label (exact-unique English label →
Stat node, `resolved_not_validated`); ambiguous/unresolved participants emit
nothing and are itemized in the coverage report; multi-participant relations
bind all-or-nothing; `classification_uncertainty` caps at
`resolved_not_validated`.
Discovery = reverse traversal of existing edge classes from bound concepts
(candidates are query-time, never persisted). Also ensures the
`edges(target_node_id)` index used by all reverse lookups.


## Semantic candidate discovery (Phase 5D)

Runs immediately after Phase 5S (`run_pipeline.sh` step 8/8). **Read-only**
over `nodes.db`/`edges.db`.

```
cache/semantic_markers.json + sem_relation_binds edges + structural edges
   ▲  phase5d_candidates.py
cache/sem_candidates.json   (regenerable intermediate, content-hashed, NOT graph data)
```

Contract: `5D.1`. A candidate means ONLY: this node is reachable from a
Phase 5S-bound concept through an explicitly allowed discovery path — never a
relationship claim. Fixed templates only: P2 (tag ← `modifier_has_tag`), P2g
(tag ← `gem_has_tag`), P3 (tag ← mod ← `unique_modifier_association`, status
preserved). Carriers are NOT duplicated (they live as `*_grants_stat` edges).
Per-record: full ordered path with per-hop edge type/direction/status, anchor
role (explicit Phase 4M participant → role map), verbatim frozen
`relation_fields`, 4M uncertainty. Dedup by
`(sid, relation_index, operator, candidate_node_id)` — all valid paths merged.
Silent operators (EQUAL in Round B) are reported, not errors. Per-(relation,
anchor) cap 5000 with explicit truncation metadata. Consumed later by a
validation phase; no validation happens here.

Contract `5D.2` adds the Stat-anchored templates: **P1a** (bound Stat anchor ←
`*_grants_stat` carrier) and **P1b** (marker Stat ← `*_grants_stat` carrier,
Stat-anchored relations only). Tag-anchored relations keep the carrier
exclusion; no carrier-carrier paths; `tag:damage`-scale anchors hit the 5000
cap and are truncated with explicit metadata.


## Semantic candidate validation (Phase 5V)

Runs immediately after Phase 5D (`run_pipeline.sh` step 9/9). **Read-only**
over `nodes.db`/`edges.db`.

```
cache/sem_candidates.json + nodes.db payloads + *_grants_stat / uma edges
   ▲  phase5v_validate.py
cache/sem_validation_results.json   (content-hashed; full records for
                                     validated tiers only, insufficient
                                     summarized)
```

Contract: `5V.1`, three tiers: `validated` (E1: candidate's `payload.stats[]`
grants the relation's own marker stat), `validated_family` (E2: granted stat
ids exhibit the audited+frozen operator morphology — SUBSTITUTE
`instead_of|in_place_of` with verified `<to>…<from>` direction; CONVERT
`to_convert_to|added_as` with pool order; SUPPRESS/REDIRECT/DERIVE/EQUAL/
COUNT_AS are **V1-only**), `insufficient_evidence` (summarized, not
materialized; the expected outcome for the overwhelming majority).
`contradicted` reserved. No LLM/fuzzy/text evidence; evidence is always
cited granted stat ids. Uniques compose through associated modifiers and
carry `status_cap: resolved_not_validated`. 4M uncertainty relations produce
no validated claims. Result records copy the 5D path, 5S binding and 4M
`relation_fields` verbatim (full traceability). v1 measured: 70 validated +
84 family of 86,402 candidates; the rest is `insufficient_evidence` — the
honest result, itemizing exactly which payload fact is missing.


## Run

```sh
santa-maria/tools/phase1_run.sh            # all steps
santa-maria/tools/phase1_run.sh report     # any single step: download|vocab|analyze|investigate|report|audit
```

Re-runnable: `phase1_download.py` skips already-downloaded (non-empty) files and
rebuilds `data/manifest.json` (path → [size, sha1]).

## Pinned external-source mechanic artifacts (Rounds A–C)

`tools/sources/` holds audited, pinned extractions from the Path of Building
Community Fork calculation code (`provenance_class: audited_pinned_external_source`,
each pinned to a PoB commit; snapshots, never auto-regenerated mirrors):

```
pob_attribute_mechanics.json   (contract 5.6: attribute_grants_stat — inherent
                                attribute bonuses, e.g. Strength → Melee Physical Damage)
pob_stat_mechanics.json        (contract 5.7: stat_mechanic_variant — the Arcane Might /
                                SpellDamageAppliesToAttacks family; stat_mechanic_operand —
                                family ↔ operand (Spell Damage) / product (Attack Damage))
```

Both are consumed by `phase5_extract_edges.py` (structural, source-backed
classes; no 5S/5D/5V impact). Product gaps (e.g. retaliation attack damage has
no KB Stat) are preserved in the artifact, never invented.

## Phase 6G — opt-in carrier grouping

`get_neighbour` accepts `carrier_grouping: true` (default false — existing
behavior unchanged). When enabled, carrier-class edges originating from **Stat
nodes** (the 8 carrier edge classes) are aggregated into virtual terminal
groups keyed by actual carrier entity type (Modifier/Passive/Gem/UniqueItem):
`levels[].carrier_groups = [{carrier_type, count, members}]`. Groups emit no
edges, never enter the frontier, and retain every member in-memory (carrier
lookup preserved). Semantic/mechanic edges expand individually as before.
`MAX_DEPTH` is 6 (raised from 4 — the verified 5-hop semantic chains require
it; per-query `depth` remains configurable).

## Snapshot integrity

- The download scope is **enforced in code** (`phase1_download.py` `scope_filter`):
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
  (`phase1_investigate.py`).

## Tests

```sh
python3 santa-maria/tools/tests/test_phase1.py
```

## Scope (filters in phase1_download.py)

- English only — the 9 language dirs are excluded
- `Metadata/Terrain/` (procedural tile graphs) excluded
- `.min.json` variants excluded
- Both the `repoe/` and `pob-data/poe1/` exports are mirrored

## Notes

- `common.py` holds `CONVERSION_PATTERNS` (order matters for the stat-id
  bucketing in `phase1_vocab.py`/the appendix) and `SCAN_PATTERNS` (exhaustive
  per-file scan), `REF_CLASSES`/`KEY_CLASSES` (cross-reference taxonomy), and
  the keyed-map heuristic constants.
- `docs/data_inventory.md` is regenerated idempotently and **gitignored**.
- The report and audit must agree: `phase1_audit.py` exits 1 if any checklist item
  FAILs.
