# Phase 6 — Graph API Design

Smallest API that lets an LLM explore the factual graph. Planning document only —
the API is not implemented.

Initial API surface is fixed:

```
get_start_seed(filters)
get_neighbour(depth, filters)
```

## 1. API semantics

Two calls, no more. Both operate **only on `edges.db` confirmed-eligible edges**
(`confidence_status` = `resolved_not_validated` / `confirmed` / `confirmed_source_backed`;
all 9 relationship classes). **Candidate-only resolution (method-2, collisions,
normalized, replica method-5, excluded-pool) lives in `nodes.db` payloads, never in
edges — the API never exposes it as a fact.**

```
get_start_seed(filters)      # discovery sample, NOT ranked
get_neighbour(depth, filters) # BFS frontier from a start node
```

**`get_start_seed`** — returns a **sample** of matching nodes, deterministically varied:
- Matching = filters; sample drawn via a caller-supplied `seed` (default 0) driving a
  deterministic PRNG over the sorted matching node-id list (sample without replacement).
  Reproducible for a given seed; different seeds → different samples (never always the
  lexicographically-first nodes).
- No ranking, no scoring, no "best" selection, no semantic reasoning.

**`get_neighbour`** — BFS from `start` up to `depth`, following edges (undirected by
default — reverse reachability is traversal, per the Step-1 contract, not a reverse edge):
- Each node visited once (visited-set → cycles handled, no infinite loops); a node
  reachable via multiple paths appears once at its shortest depth.
- Deterministic: output sorted by `(depth, edge_type, from, to)`.
- Duplicate edges are impossible (edges.db PK = `(src, tgt, type)`).

## 2. Filter schema (closed, machine-readable, validated)

Unknown filter names, invalid enum values, out-of-range integers, or filters used on
the wrong operation are **rejected with an error** — never silently ignored. An LLM can
know the complete legal API surface without inferring it from implementation behavior.

### `get_start_seed` — legal filters (all optional)

```
type:          enum[ Stat, Modifier, ModifierGroup, Tag, Passive, Gem, UniqueItem, ItemClass ]
id_contains:   string
name_contains: string
count:         integer [1..20]
seed:          integer
```

- `type` must be one of the 8 registered Phase-4 node types (not a free string).
  **`BaseItem` is NOT a node type in this KB** — base items are not nodes; the registry
  has `ItemClass` instead. No additional node types are invented.
- `id_contains` / `name_contains` are plain substring strings — no regex.
- At least one filter must be present (empty filter set → error).
- No ranking, scoring, or semantic parameters.

### `get_neighbour` — legal filters

```
start:                 node_id          (required)
depth:                 integer [1..4]   (required)
direction:             enum[ out, in, both ]
edge_types:            enum[ modifier_grants_stat, passive_grants_stat, gem_grants_stat,
                             unique_modifier_association, gem_has_tag, modifier_has_tag,
                             modifier_in_group, unique_in_class, stat_scales_with ][]
max_nodes_per_level:   integer [1..200]
include_provenance:    boolean
```

- `edge_types` entries must be from the 9 approved relationship classes.
- No wildcards, regex, SQL-like predicates, free-form semantic filters, or ranking
  parameters.
- Invalid `start` (non-existent `node_id`) → error (explicit, not empty result).

**Explicit per-operation validity:** the two filter sets above are the *only* legal
filters for their operation; cross-use (e.g. `depth` on `get_start_seed`, `seed` on
`get_neighbour`) → rejected.

## 3. Response format (compact, LLM-friendly)

No DB internals. Identity + edge type + direction + path/depth + provenance only.

```json
{ "seeds": [
    {"node_id": "stat:strength", "type": "Stat", "name": null},
    {"node_id": "mod:AddedFireDamagePerStrengthInfluence1", "type": "Modifier", "name": "AddedFireDamagePerStrengthInfluence1"},
    ...
]}
```

```json
{ "start": "stat:strength", "depth_requested": 2, "truncated": false,
  "levels": [
    {"depth": 1, "edges": [
       {"from": "stat:strength", "to": "stat:attack_minimum_added_fire_damage_per_10_strength",
        "type": "stat_scales_with", "direction": "out",
        "provenance": {"source_file": "repoe/stats.json", "role": "scaling_stat"}} ]},
    {"depth": 2, "edges": [
       {"from": "stat:attack_minimum_added_fire_damage_per_10_strength",
        "to": "mod:AddedFireDamagePerStrengthInfluence1",
        "type": "modifier_grants_stat", "direction": "in",
        "provenance": {"source_file": "repoe/mods.json", "field": "stats[].id"}} ]}
]}
```

`truncated=true` when a per-level cap was hit; the frontier is deterministic regardless.

## 4. Sampling / traversal behavior

- Seed: deterministic PRNG over sorted matching ids → controlled randomness,
  reproducible, no first-node bias.
- BFS: level-by-level; per level, edges sorted `(type, from, to)`; nodes deduped by
  shortest path; cycles cut by visited-set.
- Limits enforced as guardrails, reported via `truncated`, never silently dropped
  mid-level.

## 5. Limits

`count ≤ 20` (seeds) · `depth ≤ 4` · `max_nodes_per_level ≤ 200` · single `start` per
neighbour call.

## 6. Provenance

Per-edge compact provenance (as shown); full provenance (all supporting facts) available
in the edges store and surfaced via `include_provenance`. For
`unique_modifier_association`, method (1/4/5/6) is carried, distinguishing structural
resolution classes. Candidates are never surfaced.

## 7. Real discovery examples (grounded in the regenerated graph)

1. **Strength → Fire scaling → modifiers**: `get_start_seed([{type:"Stat", id_contains:"strength"}])`
   → `stat:strength` → `get_neighbour(depth=2, start="stat:strength")` → `stat_scales_with`
   → `stat:attack_min/max_added_fire_damage_per_10_strength` → `modifier_grants_stat`
   → `mod:AddedFireDamagePerStrengthInfluence1`.
2. **Unique → Modifier → shared Stat → other Modifier**: `get_neighbour(depth=3, start="unique:183")`
   → `unique_modifier_association` (method 1) → `mod:IncreasedAccuracyUniqueAmulet17_`
   → `modifier_grants_stat` → `stat:accuracy_rating` → (reverse) `mod:AbyssAccuracyRatingJewel1`.
3. **Whispers → Intelligence → Lightning scaling → Unholy Trinity**:
   `get_neighbour(depth=2, start="unique:1461")` returns Whispers' 4 confirmed mods
   (chaos-per-mana, reduced-mana, ES-recharge, skills-cost-ES) — **no hop to
   `stat:intelligence` exists** (confirmed gap); the API correctly exposes the absence.
   `get_neighbour(start="stat:intelligence")` → `stat_scales_with` → the per-10-intelligence
   lightning stats; `get_neighbour(start="gem:SupportUnholyTrinity")` → `gem_has_tag`
   → `tag:lightning/physical/chaos`.
4. **Unholy Trinity → Lightning/Physical/Chaos**: depth-1 `gem_has_tag` edges confirmed above.

## 8. Minimality verdict

**READY FOR IMPLEMENTATION.** Two calls + the minimal closed filter set suffice for all
four discovery tasks; the API exposes only confirmed graph facts, is deterministic,
compact, and adds no ranking/scoring/candidate logic. Decisions baked in:
seed-reproducible sampling (controlled randomness) and `direction` default `both`
(matches the contract's "reverse reachability is traversal").
