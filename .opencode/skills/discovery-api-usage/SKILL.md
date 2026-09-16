---

name: discovery-api-usage
description: Mandates the public Research API (santa-maria/tools/phase8_research.py and the research.py CLI, plus the phase6 discovery/traversal operations get_start_seed/get_neighbour) as the agent's ONLY interface to the PoE KB during research and build discovery, forbids all direct access to graph internals, SQLite databases, raw records, caches, and private helpers, and defines the API GAP protocol for when the API is insufficient. Use when running discovery or build-generation experiments, when asked for a random starting point or seed, when making any semantic KB query (lookup, carriers, mechanics, validation), or when tempted to bypass the API via nodes.db/edges.db/raw_records.db or phase internals.
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Skill: Discovery API Usage (Phase 8 boundary)

## Architectural rule

The data flow is always:

```text
research agent → public Research API → KB
```

never:

```text
research agent → API when convenient, internal DB/graph when API is inconvenient
```

The Phase 8 Research API is the agent's **public interface** to the KB during
research. The agent must not bypass it by directly inspecting or querying the
underlying graph, SQLite databases, raw records, caches, or private
implementation helpers.

## The public interface

**Phase 8 lookup/projection** (`santa-maria/tools/phase8_research.py`, CLI
`santa-maria/tools/research.py`):

* `resolve(query, type=None)` — complete, non-sampled node lookup by
  id/display-name substring (case-insensitive). Returns ids, types, names,
  `availability` (uniques), `passive_info` (passives). Duplicate display names
  are a valid lookup: all matches are returned and `meta.ambiguous` flags the
  duplication without removing anything.
* `carriers(node_id, edge_types=None)` — depth-1 reverse projection: what
  grants/carries a node (stats: which modifiers/gems/passives/uniques; a
  modifier: which uniques carry it). Results carry names, `edge_type`, availability,
  `passive_info`, and `meta.counts` per edge type. There is deliberately **no
  direction parameter**: the operation is inherently reverse.
* Envelope (both ops): `{error, results, meta}` — never raises. Input errors
  (`unknown_subject` with did-you-mean candidates, `unknown_filter`) are
  returned in `error`.

**Phase 6 discovery/traversal** (`santa-maria/tools/phase6_api.py`, also via
`research.py seed` / `research.py neighbour`):

* `get_start_seed(filters)` — sampled discovery.
* `get_neighbour(depth, filters)` — BFS traversal.

**Validation/feasibility** (already public, unchanged):
`phase7_build_validity.py` (`validate_addition`, `validate_build`),
`phase7_build_feasibility.py` (`can_support`, `slot_check`, `weapon_check`),
also via `research.py validate`.

CLI examples:

```text
python3 santa-maria/tools/research.py resolve "Marionettes" --type Passive
python3 santa-maria/tools/research.py carriers stat:critical_strike_chance_+%
python3 santa-maria/tools/research.py seed --type UniqueItem --count 3 --seed <int>
python3 santa-maria/tools/research.py neighbour <node_id> --depth 2
python3 santa-maria/tools/research.py validate '<build-state json>'
```

## Forbidden

Do not use any of the following as a substitute for missing API functionality:

* `_load_nodes()`, `_load_edges()`, adjacency internals, edge-index orientation
  (`[0]`/`[1]`) — private `GraphDB` implementation.
* Direct SQLite queries against `cache/nodes.db`, `cache/edges.db`,
  `cache/raw_records.db`, or any other KB database.
* Raw-record queries (RePoE/PoB source dumps) to answer research questions.
* Private helper methods (anything `_`-prefixed, e.g. `_passive_info`,
  `_unique_availability`, `_pob_availability`) and payload internals
  (`shared`/`variants`/`conflict` container shapes).
* Ad-hoc Python probe scripts that re-implement API functionality by accessing
  internals (the Phase 7C `drv.py`-style helpers are the anti-pattern).

**Allowed**: Python for post-processing data returned by the public API —
grouping, counting, filtering returned results, statistics, analysis. The
moment a computation needs data the API did not return, it is an API GAP (see
below), not a reason to open the database.

## Why direct access is not a trustworthy fallback

In Phase 7C a hand-written probe iterated the graph's in-adjacency as if it
were the out-adjacency and filtered by a node type that can never match on
that side. It silently returned zero rows. The KB actually contained the
relationships: the diagnostic found **313 ascendancy→crit-family
`passive_grants_stat` edges**. A hand probe that returns `[]` is
indistinguishable from a true absence — direct access is *less* trustworthy
than the API, not more. The regression test
(`santa-maria/tools/tests/test_phase8_research.py`) pins both the fact and the
failure shape.

## Epistemic contract — treat the API as authoritative

| API answer                                                                                        | Meaning                                                                     | Correct agent behavior                                                                                   |
| ------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| valid, complete empty result (`results: []`, `meta.counts` all zero)                              | legitimate research result: the relationship/thing does not exist in the KB | record it as a fact with the query that produced it                                                      |
| UNKNOWN (`error: null`, `availability: null`, `passive_info.ascendancy: null`, validator UNKNOWN) | knowledge limitation; fail-closed by design                                 | record as unknown; never guess, never inspect the DB to resolve it                                       |
| truncated (`meta.truncated.total > len(results)`)                                                 | incomplete result                                                           | refine the query (longer substring, narrower edge types) or report the total; do not treat as exhaustive |
| API lacks the capability entirely                                                                 | **API GAP**                                                                 | stop and report (protocol below)                                                                         |
| internal DB contains something the API does not expose                                            | **still an API GAP**                                                        | the agent must not use the DB to answer the research question                                            |

## API gap protocol

If the research question requires information that the public API does not
currently expose:

1. **STOP that line of research.**
2. Do **not** work around the limitation by querying the database or internal
   graph directly.
3. Report an explicit **API GAP** describing:

   * the research question,
   * what information/capability is missing,
   * which public API operations were available/attempted,
   * why they were insufficient.
4. Continue with other independent research only if it can be done entirely
   through the available public interface.

Do not invent new API operations mid-session and do not modify Phase 8 to make
a session convenient — an API GAP report is the deliverable.

## Random starting points (unchanged rule)

When the task asks for a **random** node, seed, Unique, or starting point,
**random means randomness generated by our API** (`get_start_seed` with a
recorded seed; `research.py seed --seed <int>`).

Do not choose something manually and call it random.

Use the API's random-selection mechanism and record the returned result.

The LLM must not select, bias, or replace an API-randomized starting point
based on what looks interesting.
