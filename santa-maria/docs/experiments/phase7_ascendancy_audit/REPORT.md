# Phase 7 Audit — Ascendancy Representation & Build Validity (2026-09-16)

Question: why do generated builds contain no Ascendancy, and does the KB/API expose
enough for discovery to use Ascendancies naturally?

## Part 1 — Representation (API + source evidence)

**Node/edge types.** `phase6_api.NODE_TYPES` has no Ascendancy type. Ascendancies are
`Passive` nodes identified only by id convention — three coexisting conventions:
`Ascendancy*` (PoE1 Default tree), `AscendancyCustom*` (DefaultAltAscendancies / PoE2-era
alt tree), `AlternateAscendancy*` (warden-type smalls). 920 unique Ascendancy-id passive
records across RePoE trees; ~455 after excluding atlas/royale variants.

**Payload vs API surface.** `extract_nodes.py:654` stores the FULL source record in
`payload['shared']`, so the graph contains:
- `ascendancy` — class name (e.g. "Necromancer"): present on 644/920; 276 are
  `ascendancy=None` (Atlas nodes, `AlternateAscendancy*` smalls) — unclassifiable from
  the field;
- `kind_flags` = {is_keystone, is_notable, is_jewel_socket, is_ascendancy_starting_node,
  is_multiple_choice}.

Kind split of Ascendancy-id nodes: **415 `is_notable=true` (big nodes), 505 small
(neither), 0 keystones**. Per class: Berserker (alt tree) 9 notables + 10 smalls;
Necromancer (Default) 8 + 9. Small/big distinction IS in the representation (`is_notable`),
and smalls are real (e.g. "Strength and Armour" flat-stat smalls).

**But `phase6_api.py` never surfaces any of this** (grep: no `kind_flags`, no `ascendancy`
in the API module). `get_start_seed`/`get_neighbour` expose id/type/name/edges only.

**Edges.** Ascendancy nodes connect only via `passive_grants_stat` (verified both
directions: `passive:AscendancyNecromancer9 → 3 stats`, and stats → other ascendancy nodes).
Depth-2 transit reaches mechanics (`...minion_maximum_life_%_to_add_as... → mechanic:minion`).
There are NO passive↔passive edges and no class-grouping edges — EDGE_TYPES has none —
so class membership is recoverable only from the payload field (or id string).

**Random selection.** `get_start_seed({'type':'Passive'})` draws from ≈2699 passives;
Ascendancy ids ≈17% of the pool — raw random Passive seeds hit them occasionally but
unlabeled. There is no type-filtered random pick for "an Ascendancy"; the only handle is
`id_contains='Ascendancy'` (works today, verified).

**Reachability.** Yes: get_neighbour returns them (both directions of
`passive_grants_stat`), and run-1's attempt A13 surfaced
`AscendancyCustomHeirophant18` naturally through a random Passive start.

## Part 1 verdict — why builds lack Ascendancies

**Primary: state-model gap (3/4).** `BuildState` = items + gem_groups only. A passive
candidate CRASHES the validator: `slot_check → _resolve_unique →
ValueError('unique node not found: ...')` (reproduced). Discovery literally cannot commit
an ascendancy even if it finds one — check-then-commit fails hard, and reports list builds
as item-only.

**Secondary: API surface gap (2/4).** The classification data (`ascendancy` class,
`is_notable`) exists in the graph payloads but nothing in the API result exposes it;
an LLM explorer cannot see what it found. Also no class-grouped random selection.

**Tertiary: graph coverage (1/4).** Missing class-grouping edges are real but minor —
membership is recoverable from payload. NOT the root cause.

**Discovery behaviour (4/4) is least to blame:** A13 shows ascendancies appear naturally;
they were never committable.

**KB fact:** 0/920 Ascendancy nodes are keystones; keystones (Iron Reflexes, Vaal Pact…,
80 ids incl. atlas) are regular-tree nodes with no ascendancy class. "Keystones from that
Ascendancy" is therefore undeterminable from the KB — per user decision, the cap applies
to **`is_notable` ascendancy nodes** (cap = 4), smalls uncounted.

## Part 2 — Validator extension (implemented this run)

- `BuildState.passives` + `add_passive()` (immutable, same check-then-commit convention).
- Classification via payload internals (`_classify_passive`): `ascendancy` field +
  `kind_flags`; `ascendancy=None`/conflicting variants → `unknown`, never guessed.
- New checks (reported in `passive_checks` block, `checked` += ascendancy_composition):
  1. exactly-one at final validation (`final=True`): zero classes → invalid "no Ascendancy";
  2. no-mixing: ≥2 distinct classes → invalid "mixed Ascendancies: ...";
     `validate_addition` of a second-class ascendancy → invalid, attributed to candidate
     (incremental validation runs `final=False` so in-progress states aren't penalized);
  3. ≤4 notables: count of `is_notable` ascendancy nodes > 4 → invalid; ==4 valid;
  4. unclassifiable passives → status unknown (never valid).
- CLI: `--passive NAME` repeatable on `add`/`build`.
- Tests: `tools/tests/test_build_validity_ascendancy.py` (7 cases; see file).

## Part 3 — Smallest justified next step (implemented same day)

`phase6_api` now surfaces Passive classification: `get_start_seed` entries add
`passive_info {ascendancy, kind_flags}` for Passive seeds; `get_neighbour` levels add a
`passive_nodes` block (id, name, passive_info) for discovered Passives (edge targets +
carrier-group members; absent when a level has none). Conflict/unclassifiable payloads
surface as nulls — never guessed. No DB/schema change; graph bit-identical.
Tests: `tools/tests/test_phase6_passive_info.py` (5); regressions test_phase6,
test_variants, test_consumer_projection, test_build_validity, test_build_validity_ascendancy
all pass. Not done: class-grouping edges (coverage), nameless stat/mod nodes (readability).
