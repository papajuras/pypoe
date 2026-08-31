Phase 4 — Node Extraction Design & Implementation

4A — Machine profiling / taxonomy discovery

Goal: understand what kinds of entities actually exist in the raw
snapshot. LLM/scripts analyze raw_records.db, but do not create nodes yet.

Produce a compact, machine-readable profiling report for significant
sources, including:

- record counts
- variants of generation_type, domain, etc.
- naming patterns
- stat IDs
- cross-reference patterns
- structurally distinct record shapes
- representative examples
- candidate record classes

Priority sources:
mods.json
stats.json
uniques.json
passive_skill_trees/*
gems.json

Supporting sources:
ModItemExclusive
QueryMods
TradeSiteStats
ModCache

The profiling output should be compact and aggregation-oriented, not a
second giant copy of the raw data. Detailed records can be queried from
raw_records.db when needed.

Output: small machine-readable profiling report, plus optional concise
markdown summary.

No "this is a node" decisions yet.


4B — Semantic taxonomy proposal

LLM receives the 4A profiling output, not the full raw inventory.

Question to answer: what entities should we represent as nodes?

Example candidates: UniqueItem, Modifier, Stat, Keystone, Passive, Gem,
etc. — but this must be inferred from the data, not assumed up front.

For each proposed entity, specify:

- source
- identity
- candidate node type
- inclusion/exclusion rationale
- payload
- provenance
- potential relations
- problems/ambiguities
- which edge-generation tier (1: shared stat_id, 2: shared tag,
  3: hub/conversion detection, 4: hub-adjacent verification,
  5: manual cluster gating) this entity type is relevant to
- whether its proposed payload supports that tier

Bloat filtering happens here explicitly.

Example: is a raw "Strength1" modifier its own knowledge entity?
Probably not — but the decision must be explicit and justified, not
silently dropped.

Important distinction:
"not a node" does NOT mean "discard the data". Data may still be needed
as payload, provenance, evidence, lookup data, or future re-processing.

Output: phase4_taxonomy.md, reviewed like the other design documents.


4C — Coverage & edge-readiness review

Take the proposed taxonomy and ask:

Does excluding something from nodes lose information we'll need later
for edge generation or mechanical analysis?

Example:

Crown of Eyes
→ unique modifier
→ stat

ModItemExclusive does not necessarily need to become a node, but its data
may still be required to establish or verify relations later.

For every excluded source/record class, explicitly classify its
information as one of:

- safely discardable after extraction
- retained in node payload
- retained as provenance/evidence
- retained only in the raw snapshot for future re-processing

This distinguishes node data from evidence/lookup data and prevents
building a clean but unusable graph.

Explicitly check conversion-relevant sources (e.g. keystones like
Iron Will, items like Crown of Eyes): does the retained data contain
enough information for the later conversion analysis defined by the
North Star, including the Iron Will Test?

This is a data-retention check only. Do not perform the conversion
analysis or decide full vs. partial/conditional conversion here.

Output: approved taxonomy plus a list of information that must survive
extraction even when the source itself is not represented by nodes.


4D — Formal extraction contract

Turn the approved decisions into something machine-executable.

Hard requirement: the contract must instantiate the existing node schema
from the North Star document exactly:

node_id | type | origin (source/derived) | payload

Do not invent a new or more convenient node shape.

At this phase, every extracted node has origin = source — it comes
directly from RePoE/PoB game data. Derived nodes (e.g. archetype/payoff
nodes from cluster gating) are out of scope for Phase 4 and are not
produced here.

For each node type, specify:

- source
- how a record is identified as this type
- inclusion criteria
- identity / node_id assignment
- payload
- provenance
- any required retained evidence

Output: phase4_extraction_rules.json.

The exact rules format is finalized after 4A–4C, but generated nodes must
conform exactly to node_id/type/origin/payload.


4E — Node extraction implementation

Only now write code.

raw_records.db
-> extraction_rules.json
-> extract_nodes.py
-> nodes

The extractor should be as dumb as possible.

It executes the approved rules and must not perform independent semantic
inference, guessing, or taxonomy decisions.

Still no edges.


4F — Extraction validation

"The script ran" is not sufficient.

Validate:

- node count per type
- how many source records were recognized
- how many were rejected and why
- whether identities (node_id) are unique
- whether provenance is present and internally consistent
- whether required payload/evidence identified in 4C was retained
- whether conversion-related nodes retain all source information
  identified in 4C as necessary for later conversion analysis
- whether expected exemplars exist:
  - Crown of Eyes
  - Iron Will
  - Avatar of Fire
  - ignite
  - ignited
- whether extraction is deterministic — re-running produces an identical
  result

Do not attempt to determine conversion completeness or perform Phase 5
mechanical analysis here.

Output: validation report with PASS/FAIL and enough detail to diagnose
any coverage or determinism failure.