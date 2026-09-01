# Phase 6 — Graph API Implementation Report

Implementation of the frozen design in `docs/phase6_api_design.md`. Two calls only.

## 1. Implementation

- **`tools/phase6_api.py`** — `GraphDB` class with `get_start_seed(filters)` and
  `get_neighbour(depth, filters)`; module-level `get_start_seed` / `get_neighbour`
  convenience wrappers; `__main__` discovery-example self-check (`demo()`).
- **`tools/tests/test_phase6.py`** — assert-based tests (8 cases), run via
  `python3 tools/tests/test_phase6.py`.
- Reads only `cache/nodes.db` (node identity/name) and `cache/edges.db`
  (confirmed-eligible edges). No candidate-only resolution is ever read or exposed;
  the API surfaces the frozen factual graph only.

## 2. API surface (exactly as designed)

- `get_start_seed(filters)`: filters `type` (8 node types), `id_contains`,
  `name_contains`, `count [1..20]` (default 5), `seed` (default 0). Deterministic
  PRNG sampling over the sorted matching id list (reproducible per seed; varied
  across seeds). At least one of type/id_contains/name_contains required.
- `get_neighbour(depth, filters)`: `depth [1..4]` (positional), `start` (required),
  `direction` (out|in|both, default both), `edge_types` (subset of the 9 approved
  classes, default all), `max_nodes_per_level [1..200]` (default 50),
  `include_provenance` (bool). BFS, undirected by default (reverse reachability is
  traversal, not a reverse edge); visited-set dedup (shortest path wins); per-level
  node cap -> `truncated: true`.
- **Closed-schema validation**: unknown filter names, invalid enum values,
  out-of-range integers, wrong-type values, missing `start`, non-existent `start`,
  empty `edge_types`, and empty seed filter sets are all rejected with `ValueError`.
  Cross-operation filters (e.g. `depth`/`seed` misuse) are rejected.
- Response formats match the design: `{"seeds":[{node_id,type,name}]}` and
  `{"start", "depth_requested", "truncated", "levels":[{depth, edges:[{from,to,type,direction,provenance?}]}]}`.
  Compact provenance = `source_file` + `field` (+ `method` for uma edges).

## 3. Discovery examples (verified against the live graph)

1. **Strength → Fire scaling → modifiers**: `stat:strength` → `stat_scales_with` →
   `stat:attack_min/max_added_fire_damage_per_10_strength` → `modifier_grants_stat`
   → `mod:AddedFireDamagePerStrengthInfluence1` (depth 2). PASS.
2. **Unique → Modifier → shared Stat → rare Modifier**: `unique:183` →
   `unique_modifier_association` → `mod:IncreasedAccuracyUniqueAmulet17_` →
   `stat:accuracy_rating` → (reverse) `mod:AbyssAccuracyRatingJewel1`. No direct
   Unique→rare shortcut is present. PASS.
3. **Whispers**: `unique:1461` exposes its 4 confirmed mods (chaos-per-mana,
   reduced-mana, ES-recharge, skills-cost-ES); **no hop to `stat:intelligence`**
   exists — the confirmed gap is exposed, not invented. `stat:intelligence` →
   `stat_scales_with` → per-10-intelligence lightning stats. PASS.
4. **Unholy Trinity → Lightning/Physical/Chaos**: `gem:SupportUnholyTrinity` →
   `gem_has_tag` → `tag:lightning/physical/chaos`. PASS.

## 4. Determinism

- `get_start_seed(seed=k)` reproducible (same seed → identical; seed 0 vs 1 → different
  sample).
- `get_neighbour` returns byte-identical JSON across calls.
- BFS expansion sorts the frontier, dedupes by visited-set, and orders edges by
  `(type, from, to)`; the per-level cap is applied to the sorted set. No iteration
  order, dictionary order, or filesystem order affects output.

## 5. Tests

`python3 tools/tests/test_phase6.py` — 8 tests, ALL PASSED:
seed sampling/determinism, seed closed-schema rejection, the four discovery examples,
neighbour direction/edge_types/provenance + closed-schema rejection, neighbour
determinism.

## 6. Minimality

Exactly the two designed calls; no ranking, scoring, semantic reasoning, candidate
exposure, or schema changes. No blocker encountered — the approved two-call API is
sufficient for all real discovery requirements tested.

PHASE 6 API IMPLEMENTED — READY FOR INTEGRATION TESTING
