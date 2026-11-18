# Seed corpus v1 — frozen discovery starting points

Frozen, reusable set of 81 starting points for standardized PoE discovery
experiments. Built exclusively through the public Research API
(`phase8_research.resolve`, `phase6_api.get_start_seed`); no KB/database
internals were touched (sha256 proof below).

Rebuild (must reproduce the same entries): `uv run python build_corpus.py`
from this directory. Determinism was verified: two consecutive builds produce
byte-identical `entries` (sha256 of the canonicalized array).

## Changelog

- v1.1 (2026-09-16): ascendancy coverage restricted to **base ascendancies**.
  Phrecia alternates (id namespace `passive:AscendancyCustom<Asc><n>`) and
  alternate-ascendancy trees (`passive:AlternateAscendancy*`) are excluded by
  id-namespace criterion, observable purely through public `resolve` substring
  search. Coverage grew 19 → 20 (Luminary and Reliquarian live in the base
  namespace; Reliquarian included, Luminary excluded per spec); corpus
  80 → 81 entries. The earlier v1 claim "no Luminary exists in the KB" was
  **wrong** — Luminary exists in the base namespace (18 nodes, 6 notables);
  it was absent only from the Phrecia block v1 enumerated. Corrected here.
- v1 (2026-09-16): initial freeze (80 entries, Phrecia-namespace coverage).

## Seed scheme

- `selection_seed = 20260916` (global).
- Mandatory entries: `seed = null` (pinned by requirement, not drawn).
- `ascendancy_coverage`: single `random.Random(20260916)` instance consumed in
  sorted-ascendancy order over sorted base-namespace notable ids → one notable
  per base ascendancy (Luminary explicitly skipped-and-counted, builder-asserted).
- `random_draw`: one `get_start_seed({'seed': S, 'type': T, 'count': 2})` call
  per draw round, seeds consumed monotonically 20260917+, recorded per entry.
  Drawn Passives linked to non-base ascendancy material (`AscendancyCustom*`
  ids, `AlternateAscendancy*` ids, non-null `passive_info.ascendancy`) are
  rejected — ascendancy coverage lives only in its dedicated block.

## Mandatory concepts (verified, not substituted)

| index | node_id | type | name | verification |
|---|---|---|---|---|
| 0 | `unique:1198` | UniqueItem | Replica Alberon's Warpath | resolve hit, `available` |
| 1 | `unique:1461` | UniqueItem | Whispers of Infinity | resolve hit, `available` |
| 2 | `item_class:Boots` | ItemClass | — (KB has no display name) | resolve hit; **rare-base boots anchor, deliberately NOT a UniqueItem** |

Entry 2 records the actual rare-base starting concept: the boots **ItemClass**
node (id-anchored, display name `None` in the KB). No accuracy-related Unique
was substituted.

## Mandatory base-ascendancy coverage (exactly one notable per base ascendancy)

Enumerated exhaustively via `resolve("Ascendancy", type="Passive")`
(920 nodes across three namespaces, `truncated: false`); base namespace =
21 ascendancies, 161 notables; minus Luminary (excluded) → 20 coverage
entries, deterministic rng picks below.

| ascendancy | notable node_id | display name |
|---|---|---|
| Ascendant | `passive:AscendancyAscendant5` | Path of the Shadow |
| Assassin | `passive:AscendancyAssassin10` | Toxic Delivery |
| Berserker | `passive:AscendancyBerserker8` | Rite of Ruin |
| Champion | `passive:AscendancyChampion14` | Master of Metal |
| Chieftain | `passive:AscendancyChieftan11` | Tukohama, War's Herald |
| Deadeye | `passive:AscendancyDeadeye14` | Gathering Winds |
| Elementalist | `passive:AscendancyElementalist19` | Shaper of Storms |
| Gladiator | `passive:AscendancyGladiator7` | Gratuitous Violence |
| Guardian | `passive:AscendancyGuardian16` | Unwavering Crusade |
| Hierophant | `passive:AscendancyHeirophant9` | Pursuit of Faith |
| Inquisitor | `passive:AscendancyInquisitor14` | Instruments of Zeal |
| Juggernaut | `passive:AscendancyJuggernaut11` | Unflinching |
| Necromancer | `passive:AscendancyNecromancer12` | Commander of Darkness |
| Occultist | `passive:AscendancyOccultist8` | Unholy Authority |
| Pathfinder | `passive:AscendancyPathfinder14` | Master Toxicist |
| Reliquarian | `passive:AscendancyReliquarian9` | Caster Weapon Display |
| Saboteur | `passive:AscendancySaboteur4` | Born in the Shadows |
| Slayer | `passive:AscendancySlayer8` | Overwhelm |
| Trickster | `passive:AscendancyTrickster2` | Swift Killer |
| Warden | `passive:AscendancyRaider8` | Lesson of the Seasons |

**Verification**: every eligible base ascendancy appears exactly once in this
block (20 groups, asserted 1-per-asc in the builder). Luminary is present in
the base namespace and explicitly skipped (6 notables, builder-asserted
skip-count > 0). No ascendancy notable appears anywhere else in the corpus:
draws rejecting all asc-linked Passives are builder-enforced.

## Composition and type distribution

81 entries: 3 mandatory + 20 ascendancy coverage + 58 recorded-seed draws
(34 `get_start_seed` calls; all quotas filled).

| type | count | notes |
|---|---|---|
| UniqueItem | 14 | 12 draws + 2 mandatory |
| Passive | 28 | 8 draws + 20 ascendancy coverage |
| Gem | 8 | incl. awakened/alternate-quality variants |
| Stat | 8 | incl. conditional-shaped stats |
| Modifier | 6 | incl. enchant/unique/heist families |
| Mechanic | 5 | minion, ignite, suppression, attribute, frenzy_charge |
| Tag | 4 | weapon, dagger, lightning, curse |
| ItemClass | 8 | 7 draws + 1 mandatory (Boots) |

## Sanity check (all enforced by builder asserts + manual review)

- All 81 entries re-resolve through the public API (resolve by exact id).
- No duplicate `node_id`; no near-duplicate family (normalized-name
  collision check: `Replica `/awakened-quality prefixes, trailing numeric
  suffixes, `AltX` variants stripped). Farrul's Chase + Farrul's Bite were
  kept deliberately: distinct items sharing an aspect-of-the-cat family,
  not name near-duplicates.
- Mandatory concepts present as specified (see table above).
- No placeholder-style display names (`<<…>>`) anywhere in the corpus
  (builder-asserted) — the v1 Phrecia `<<HRB32>>` artifact is gone.
- Type distribution: see table; 8 of 8 seedable entity types represented.
- No mechanic-family overrepresentation observed (≤2 per item family;
  mechanics block covers 5 distinct mechanics).

## Observations / API limitations recorded (not worked around)

1. **Luminary**: exists as a base-namespace ascendancy (18 nodes, 6 notables);
   excluded from coverage per corpus spec (explicit skip, not silent absence).
2. **Base vs Phrecia criterion**: id namespace only (`Ascendancy<Asc>` vs
   `AscendancyCustom<Asc>`); the API exposes no explicit "alternate version"
   flag on `passive_info` — the namespace split is the only public signal.
3. Warden coverage entry: id namespace says `AscendancyRaider8` while
   `passive_info.ascendancy` says `Warden` (id/metadata mismatch in the KB;
   API-authoritative metadata was used for grouping).
4. `Buff` and `BaseItem` are not seedable: `get_start_seed` returns
   `unknown_filter` with **empty candidates** (the known Phase 8
   did-you-mean weakness); fail-closed, corpus adjusted by using the 8
   valid seedable types.

## Read-only proof

KB sha256 identical before and after all corpus API calls:

```
289b29aea530a15f9a8664fc91d46f2064ed2d04a5790c25437525dcfe1c9e1d  cache/nodes.db
5eb3059b82633bfaa2e86df7bf928d7b1899042c5840300da13af746ffae024a  cache/edges.db
a8b725e9f27db1e123cb092b150cea5873c27f5bd4e692b14974ecf7ecad11fe  cache/raw_records.db
```
