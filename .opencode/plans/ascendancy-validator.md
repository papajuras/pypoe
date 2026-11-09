# Ascendancy Audit + Validator Extension — APPROVED PLAN (cap = 4 notables)

Status: user-approved (with amendment: ascendancy notable cap is **4**). Blocked by
plan-mode edit permissions at write time — execute as written below.
All audit evidence is verified (API calls + source reads, 2026-09-16).

## Part 1 — Audit evidence (report → `santa-maria/docs/experiments/phase7_ascendancy_audit/REPORT.md`)

- No dedicated node/edge type: ascendancies = `Passive` nodes by id convention
  (`Ascendancy*`, `AscendancyCustom*`, `AlternateAscendancy*`); 920 unique Ascendancy
  ids across RePoE trees; ≈455 excl. atlas/royale variants.
- Payload (extract_nodes.py:654 `shared: rec`) retains `ascendancy` (class name) +
  `kind_flags` (`is_keystone`, `is_notable`, `is_ascendancy_starting_node`).
  644/920 have a class; 276 are ascendancy=None (Atlas/Alternate smalls — unclassifiable).
  Kind split: 415 is_notable=true (big), 505 neither (small), 0 keystones.
  Per class e.g. Berserker(alt)=9 notables+10 smalls, Necromancer(Default)=8+9.
- `phase6_api.py` NEVER surfaces kind_flags/ascendancy (grep-verified). get_start_seed
  returns id/type/name only.
- Reachability: yes, via `passive_grants_stat` both directions
  (passive:AscendancyNecromancer9 → 3 stats → mechanic:minion). No passive↔passive or
  class-grouping edges exist (EDGE_TYPES).
- Random selection: `type=Passive` pool ≈2699, ascendancy ≈17% — hit but unlabeled.
  No type-filtered random "ascendancy" pick; `id_contains='Ascendancy'` is the only handle.
- Validator: `BuildState` = items+gem_groups only; passive candidate CRASHES
  (`slot_check → _resolve_unique → ValueError('unique node not found')` — verified).
- **Part 3 conclusion:** primarily state-model gap; secondarily API surface gap; graph
  coverage tertiary (only real gap = no class-grouping edges). KB fact: no ascendancy
  keystones exist (0/920; keystones are regular-tree nodes without ascendancy class),
  so "≤N keystones from that ascendancy" is undeterminable — user approved counting
  **is_notable ascendancy nodes** instead, cap **4**.

## Part 2 — Validator changes (`santa-maria/tools/phase7_build_validity.py`)

1. Constants: `ASCENDANCY_NOTABLE_CAP = 4`; extend VALID_WRT (+ascendancy composition);
   append LIMITATIONS entry (payload classification, None→unknown, no ascendancy
   keystones, smalls uncounted).
2. `BuildState`: add `passives: list = field(default_factory=list)`; `add_passive()`
   returning new instance; thread `passives` through existing `add()`/`add_gem_group()`;
   `_as_state` reads `state.get('passives', [])`.
3. `_resolve_passive(candidate, nodes)`: exact `passive:<x>` key, else unique name match
   among Passive nodes; unresolvable/ambiguous → ValueError (fail-fast, consistent with
   items).
4. `_classify_passive(payload)` → `(ascendancy, is_notable, class_status)`:
   - base = payload['shared']; kind_flags top-level (None ⇒ per-variant disagreement).
   - `kind_flags is None` or ascendancy missing-but-variants-disagree → class_status='unknown'.
   - ascendancy=None regular-tree keystones are classless components (legal, uncounted).
5. `_passive_checks(passives, g, final)` → block mirroring gem_checks:
   - resolved entries: {passive, name, ascendancy, class_status, is_notable, is_keystone};
   - `class_mix`: distinct known classes ≥2 → INVALID 'mixed Ascendancies: X, Y';
   - `notable_cap`: count is_notable & class_status='known' nodes > 4 → INVALID; ==4 valid;
   - `single_ascendancy` (final only): zero known classes → INVALID 'no Ascendancy';
   - any class_status='unknown' → contributes UNKNOWN (never valid).
6. `validate_build(state, graph=None, final=True)`: run item slot_check as today +
   passive_checks when state.passives; INVALID > UNKNOWN > VALID ordering unchanged;
   `checked` += ['ascendancy_composition'] when passives present.
   `validate_addition(state, candidate, graph=None)`: for passive candidates route via
   `merged = state.add_passive(candidate)` and call validate_build(..., final=False)
   (in-progress states are not penalized for missing ascendancy; mixing/cap still apply);
   conflict attribution extended to passive_checks (candidate involved → per-item reason).
7. CLI: `--passive NAME` (append, repeatable) on both `add` and `build` subcommands;
   `build` = final=True; `add` = validate_addition (final=False internally).
8. demo(): add one ascendancy line (optional, 3 lines max).

## Tests — `santa-maria/tools/tests/test_build_validity_ascendancy.py`

Assert-style like existing tests. Cases:
1. valid single ascendancy: 2 Necromancer notables → VALID;
2. no ascendancy at final: state with 0 ascendancy-class passives → INVALID 'no Ascendancy'
   (final=True); same state via validate_addition (final=False) → not penalized;
3. two different ascendancies (Necromancer + Juggernaut notable) → INVALID 'mixed';
4. exactly 4 notables of one class → VALID; 5th → INVALID (cap);
5. validate_addition of second-class ascendancy onto single-class state → INVALID,
   attributed to candidate;
6. ascendancy=None / kind_flags-None candidate → UNKNOWN (never valid);
7. immutability: add_passive does not mutate (regression guard).
Real node ids for tests: Necromancer class passives from Default tree
(passive:AscendancyNecromancer9 has ascendancy='Necromancer', is_notable — verify notability
at test-authoring time via payload; pick 5 notable ids of one class + 1 of another class
from data/repoe/passive_skill_trees/Default.json).

## Run

```
cd santa-maria
uv run python -m tools.tests.test_build_validity_ascendancy
uv run python -m tools.tests.test_build_validity     # regression
uv run python -m tools.tests.test_build_feasibility  # regression
uv run python -m tools.tests.test_consumer_projection # regression
```

## Out of scope (proposed follow-up, do NOT implement now)

Expose `kind_flags`+`ascendancy` in get_start_seed/get_neighbour output (few lines, no
schema change) so discovery can label/commit ascendancies it stumbles onto. Also no
class-grouping edges (coverage fix), no new discovery run.
