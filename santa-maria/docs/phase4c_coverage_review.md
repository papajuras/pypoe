# Phase 4C — Coverage & Edge-Readiness Review

Review of the Phase 4B taxonomy for data retention / coverage sufficiency
before edge generation and mechanical (conversion) analysis.

## 1. Approved taxonomy (from `phase4b_taxonomy.md`, unchanged here)

Nodes (all `origin = source`, schema `node_id | type | origin | payload`):
**Stat, Modifier, ModifierGroup (candidate, 4C-pending), UniqueItem, Passive,
Gem, Tag, ItemClass, Buff (provisional)**.
Lookup/evidence (not nodes): ModItemExclusive, QueryMods, TradeSiteStats,
ModCache, stat_translations, stat_value_handlers, PoB Uniques text, tree
scaffolding, stats_by_file, data-formats.

### Non-node record classes → retention classification

| class | classification |
|---|---|
| TradeSiteStats entries | retained only in raw snapshot (role 5) + used as query-time lookup/index (role 4) |
| QueryMods slot maps | retained only in raw snapshot (role 5) + query-time lookup (role 4) |
| ModCache entries | retained only in raw snapshot (role 5) + query-time lookup (role 4) |
| ModItemExclusive records | retained in raw snapshot (role 5); **evidence for UniqueItem resolution method 2** (role 3) via `tradeHashes` text |
| PoB `Uniques/*.json` text blocks | retained in raw snapshot (role 5); **evidence for resolution method 2** (role 3) |
| `stat_translations.json` (+ dir) | retained in raw snapshot (role 5); **must be retained as lookup/evidence for T3 + the keystone↔conversion bridge** (role 3/4) |
| `stat_value_handlers.json` | retained in raw snapshot (role 5); **must be retained as lookup for T3 magnitude** (role 4) |
| `stats_by_file.json` | retained in raw snapshot (role 5); provenance index (role 4) |
| tree scaffolding (`art/groups/roots/title`) | retained in raw snapshot (role 5); provenance (role 3) |
| `data-formats/*` schemas | safely discardable after extraction (documentation, kept in repo) |
| `gems.json per_level` lines | retained in **Gem payload** (role 2) |
| `gems.json stat_conversions` | retained in **Gem payload** (role 2) + T1 alias lookup |
| `spawn_weights[].tag/weight` | retained in **Modifier payload** (role 2); Tag is the node |
| `old_do_not_use_*` / dummy stats | retained in **Stat payload** as flags (role 2) |
| unlisted candidate sources (Mod* family, buffs, tags, item_classes, base_items…) | retained only in raw snapshot (role 5); 4C decides load-bearing |

No new nodes are warranted by any of the above — resolution/evidence data
stays lookup/evidence/raw.

## 2. Information that MUST survive extraction

- Raw **stat id strings** in every payload (T1 join atoms; T3 carriers).
- `Modifier.stats[].id` + `min`/`max` + `text` (magnitude + display) — T3 source of truth.
- **Conversion-suffix stat ids** (`_at_<N>%_value`, `_applies_to_`,
  `_gained_as_` — 19/26/4 confirmed in mods.json) as raw ids in Modifier payload.
- `Passive.stats` (stat_id→value) incl. keystone markers (`strong_casting`).
- `Gem.stat_conversions` (alias map) + `Gem` per_level stat ids.
- `UniqueItem.resolved_targets` + `resolution_status` + `resolution_evidence`
  (method, matched text, candidate keys) — for re-resolution.
- `stat_translations` + `stat_value_handlers` (T3 display + magnitude chain) — as lookup/evidence.
- `Modifier.groups[]`, tags, `domain`, `generation_type` (T2).

## 3. Genuine coverage gaps

1. **Keystone ↔ conversion-stat bridge (the real one).**
   `Passive(iron_will) → Stat(strong_casting)` and
   `Modifier(Crown of Eyes) → Stat(additive_spell_damage_modifiers_apply_to_attack_damage_at_150%_value)`
   are both retained, but **no structural link connects `strong_casting` to
   the `additive_spell_damage…` conversion family**. Verified:
   `strong_casting` has one stat_translations entry ("Iron Will"); the
   conversion family has 2 separate entries; **0 entries group them**; the
   display strings differ ("Iron Will" vs "Attacks have 100/150% Arcane
   Might"). The equivalence is only inferable via translation text
   comparison or a curated alias.
2. **T3 magnitude/completeness chain not in any payload.**
   `stat_value_handlers` is keyed by handler name; the stat→handler link
   lives in `stat_translations` `index_handlers`. This chain is entirely
   outside node payloads (safe in the raw snapshot, but not in payload).
3. **Method-2 resolution matches unvalidated.** The 880 are candidate
   associations; re-resolution needs the retained evidence (kept) — noted,
   not a data gap.

## 4. Gap fixes (type required)

1. Keystone↔conversion bridge → **lookup/evidence retention**
   (`stat_translations` retained as role-4 lookup; optionally a derived
   stat-alias/equivalence map in 4C/5). **No new node.** This is the only
   case where Phase 5 needs data beyond node payloads.
2. T3 magnitude chain → **lookup/evidence retention** (`stat_translations`
   + `stat_value_handlers` retained; elevate from "candidate" to required
   for the T3 claim). No new node.
3. Everything else → already in payload or raw snapshot; no fix.

## 5. Iron Will Test — sufficient retained information?

**Yes — retained data (node payloads + the lossless raw snapshot) contains
everything required**, with one explicitly documented dependency:

- T3 conversion detection:
  `additive_spell_damage_modifiers_apply_to_attack_damage_at_150%_value` is
  retained as a raw Modifier stat id, with magnitude **150 encoded in the
  id** and `min/max` in the payload — sufficient for the full/partial
  question at the modifier level.
- Keystone side: `Passive(iron_will) → strong_casting` retained (T1).
- Magnitude scaling (permyriad etc.): `stat_value_handlers` retained in the
  raw snapshot; reachable via `stat_translations.index_handlers` — must be
  kept as lookup/evidence (it is).
- **Dependency:** equating `strong_casting` with the Arcane Might
  conversion stat is **not structural** — it requires the
  `stat_translations` (or a derived alias) bridge (gap 1). The raw snapshot
  retains it, so the test is answerable; it just cannot be answered from
  node payloads alone.

**Verdict: READY for Phase 5 data-wise, with one required retention
guarantee** — `stat_translations` + `stat_value_handlers` must be retained
as lookup/evidence (they are, in `raw_records.db`), and Phase 5 must consume
them (or a derived stat-alias map) for the keystone↔conversion bridge. No
new nodes, no payload changes strictly required.
