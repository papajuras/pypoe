---
name: scaling-discovery
description: Identify, validate, and pursue genuine scaling axes during PoE build discovery with the santa-maria knowledge base. Primary target: quadratic or higher-order scaling — the same investment in X entering the same output through multiple interacting paths. Use when exploring the KB graph for build concepts, evaluating scaling relationships, or deciding whether a promising interaction warrants deeper exploration.
metadata:
  "opencode/autoinvoke": false
  version: 5
---

# Skill: Scaling Discovery (v5)

Use during build discovery to identify meaningful scaling, validate it, and decide what deserves deeper exploration.

## 0. Governing invariant — no curated discovery lists

What to investigate must be derived from the **KB structure and the discovered axis** — never from a predefined list of mechanics, attributes, stat families, item families, or known synergies.

Prohibited:

* hard-coded checklists of mechanism families (bridges, conversions, per-attribute/per-pool scalers, accuracy, charges, …);
* predefined item or stat names;
* special handling for any specific stat, item, or interaction.

Known examples may appear **only** in the quarantined Coverage fixtures (§13) as property-form checks — never inside the discovery algorithm, and never as a search strategy.

## 1. Scaling axis

A scaling axis is a variable **X** such that increasing X improves an important build output through an explicit game mechanic:

**increase X → mechanic uses/converts X → output improves**

The output must change because X changes. A generic bonus or multiplier is not an axis; a multiplier matters when a scaling axis feeds it.

**The seed is an entry point, not necessarily the pivot.** When the seed's neighborhood evidences a stronger scaling axis elsewhere (seed `life` → discovered `strength` scaling), re-anchor the axis and pursue it. The seed must still be **part of the scaling**: it stays validator-committed and participates in the architecture subgraph through at least one live edge that contributes to the scaling structure (path, consumer, enabler, generator, multiplier input) — it just is not required to be the axis X. Record every re-anchoring in the report (`from → to`, why).

## 2. Primary target: quadratic or higher-order scaling

The target is X entering the **same meaningful output** through two or more interacting paths:

**X → A, X → B, A × B → output** → X²

**X → A, X → B, X → C, A × B × C → output** → X³

Ladder:

* **single-use** — X → A
* **multi-use** — X → A, X → B, independent outputs
* **quadratic / cubic+** — X feeds ≥2 / ≥3 interacting inputs of one output

Rules:

* **Multi-use is not double dip.** Damage + defense from X is multi-use; independent consumers do not interact.
* **Consumer count is not evidence of quadratic scaling.** X → A, B, C remains multi-use until the effects interact toward one output.
* **Degree ≠ practical strength.** Never rank candidates by degree alone.
* When claiming higher-order scaling, name X, every relevant path, the common output, the combining mechanic, and the degree. If a path is unconfirmed, call it a hypothesis.

## 3. Validate

For any candidate establish **X → mechanism → output**. For higher-order candidates establish every relevant path and their interaction.

Prefer explicit KB/graph relationships. Do not infer multiplicative interaction merely because two effects share a stat or both improve damage.

## 4. Architecture subgraph and the growth loop

The discovery artifact is a **subgraph**, not a line: allocated nodes (items, gems, passives, key stats) by role, the live KB edges between them, and an evidence status per edge (**confirmed / hypothesis / unknown**).

A confirmed X² relationship is a finding, not the end — grow the subgraph around it with a fixed-point loop:

1. **Sweep** — for *every* node already in the subgraph, probe the KB (`neighbour`, `carriers`) — expansion scope defined by §5 — for directions not yet represented: additional paths from X, additional consumers/conversions of A/B, multipliers whose inputs are themselves affected by subgraph nodes, another axis Y interacting with the established scaling, feedback or recursive scaling, generators/enablers. Inspect the **intrinsic/core mechanics of every encountered entity through the same generic ops**: reverse projections include attribute→resource conversions (`attribute_grants_stat`) and default engine rules (`rule_applies_to` / `rule_negated_by` / `rule_modified_by`) wherever they apply — read those rows as first-class evidence (each carries the rule statement, its formula/value, and its bound exception mechanisms). Never maintain or consult a curated list of rule names; if an entity's intrinsic row is missing, that is a KB fact, not a prompt to guess one.
2. **Reclassify** — as the structure grows, existing nodes and edges may change role or ladder class (§11). A consumer can turn out to be a second scaling path.
3. **Add & validate** — accepted findings join the subgraph; build components go through `validate_addition` (§10).
4. **Repeat** until a full sweep produces **no new nodes or edges and no reclassifications** — that is the fixed point.

Limits:

* **Hard cap: 10 sweeps.** If the cap is hit without a fixed point, stop and report remaining findings as open leads.
* Skip re-probing a node whose neighborhood is unchanged since its last probe.
* Per-sweep additions stay small (§7 applies per sweep).
* Never manufacture candidates (§8). A sweep adds nothing unless KB evidence supports it.

An additional layer matters only if it expands the established scaling architecture. **Do not explore graph depth for its own sake.**

## 5. Generic expansion protocol

The sweep is not a random walk over neighbours: it is a systematic expansion of the current axis across every relationship space the public API exposes. The probe set is **regenerated from data every run** — never stored, never assumed.

1. **Vocabulary harvest** — collect every stat id and modifier text reachable from the axis (seed stats, tags on their mods, carrier rows). Split harvested ids into meaningful components and use them as `resolve` name queries; use harvested modifier text as prose queries (literal normalized substring only — abbreviation variance is the stat door's job, wording variance is the prose door's job).
2. **Pattern mining** — from the harvested id/text set, mine recurring structural patterns (e.g. `per_N_<unit>`, `<unit>_%`, `%_of_<unit>`, `equal_to_%_<unit>`, `..._apply_to_...`, `..._convert_to...`, `..._scales_with...`, `<unit>_per_<other_unit>`, `..._at_%_value`). The pattern list is produced by this run's own data. Probe each mined pattern with `resolve` (prose form) and `carriers` (stat form); probe associated tags with `neighbour(tag)`.
3. **Multi-space, two-direction probing** — for every frontier node, probe **both directions across every space the API exposes**:
   * **carrier space** — `carriers()` (reverse; includes `meta.counts` per edge type);
   * **forward space** — `neighbour()`;
   * **tag space** — `neighbour(tag:…)` (`carriers(tag)` returns 0 by design; the tag door is `neighbour`);
   * **mechanic space** — `stat_mechanic_relation` / `stat_mechanic_variant` / `stat_mechanic_operand` rows surfaced on probed entities; mechanic nodes reachable through them are first-class discovery targets;
   * **rule space** — intrinsic rows (`rule_applies_to` / `rule_negated_by` / `rule_modified_by`) surfaced wherever they apply; read each row (statement, formula, bound exceptions) as first-class evidence;
   * **attribute space** — `attribute_grants_stat` rows; per-attribute stat families are found by resolving the attribute names that appear inside harvested ids.

## 6. Full-slot audit

Composition quality is audited, not assumed. For every equipment/skill capacity:

1. **Derive the slot list from KB structure**: the `item_class:*` nodes reachable via `unique_in_class` edges from discovered carrier items, plus gem/flask/jewel capacities evidenced in the subgraph. Never assume a fixed slot table.
2. **Search each slot** for axis-evidenced carriers: `carriers()` on axis stats, with the carrier's own `unique_in_class` edge establishing its class/slot fit.
3. **Record empty searches**: a slot with no evidenced carrier is reported with the exact queries performed and their `meta.counts` — a recorded empty search, never a silent skip.

## 7. Explore proportionally

Accept a sweep finding only when it has:

1. a meaningful scaling axis X;
2. credible generation of X;
3. a meaningful output;
4. a second interacting path toward that output, or a plausible route to one.

Otherwise park it on the §8 agenda or drop it. A sweep that adds nothing is progress toward the fixed point — report it as empty and continue or stop. A full-slot audit (§6) that returns only recorded empty searches counts the same way.

## 8. Small agenda

Park at most a few candidates, each with one concrete revisit reason: a possible second X-path, an unconfirmed multiplier, an unexplored consumer, a possible higher-order layer, or pending validation. Agenda items are **sweep inputs** — each parked revisit reason is probed on the next sweep that touches the relevant node.

The agenda is a memory aid, not an algorithm — no scores, quotas, or parallel exploration. Never manufacture candidates; drop a parked branch when its reason dies.

## 9. Roles

**scaling axis** · **generator** · **consumer/converter** · **enabler** · **multiplier** · **defense**

They interact but are not interchangeable: a generator is not automatically an axis, a multiplier is not a second scaling path, and a second consumer is not a double dip.

## 10. Build validation

Graph reasoning and build validity are separate concerns. Commit components via `santa-maria/tools/phase7_build_validity.py`:

**propose component → validate_addition → VALID: commit / INVALID: reject / UNKNOWN: do not assume valid**

Use rejection reasons to steer alternatives. Validate components when actually adding them; keep committed state explicit; finish with `validate_build`.

VALID means only implemented deterministic constraints passed. Never invent missing constraints or move feasibility rules into the semantic graph.

Classify committed items as:

**core scaling component · scaling enabler · mechanic converter · synergy component · slot filler · generic placeholder**

Mark slot fillers explicitly. Prefer builds whose important non-defensive components participate in the scaling architecture.

**Two-tier output.** Every architecture is rendered in two tiers:

* **VALIDATED core** — only components the validator can check.
* **CANDIDATE maximized variant** — for architectures containing unmodellable components (e.g. influenced-only mods, no-slot-model jewels/flasks, unexposed gem values), emit the maximized variant. Each such component carries its **exact quoted reason**: the validator's `limitations` entry, the numbered API gap, or the zero-carrier verdict. No component without a stated reason; no speculation.

## 11. Evidence and decision

At each promising discovery ask:

> Does increasing X merely provide multiple independent benefits, or does X enter the same output through multiple interacting paths?

Classify:

**isolated → multi-use → quadratic candidate → quadratic confirmed → cubic+ candidate/confirmed**

Do not manufacture causal links, multiplicative interactions, or higher-order behavior. X appearing in two places is not X² unless both dependencies interact in the same meaningful output.

Partially known relationships remain hypotheses. Never substitute general game knowledge for missing KB evidence when claiming a relationship was discovered from the KB.

## 12. Report the architecture subgraph

Every discovery report contains an **Architecture subgraph** section stating:

* the skill version this run ran under (from this file's frontmatter);
* nodes by role (§9), including the seed's role;
* edges with evidence status (confirmed / hypothesis / unknown);
* axis re-anchoring decisions (`from → to`, why), if any;
* the sweep log — what each sweep added, and why the loop stopped (fixed point or 10-sweep cap with open leads);
* which generic expansion steps ran (mined patterns + spaces probed, §5);
* new mechanism families discovered — especially those not anticipated by any fixture (§13);
* which slots were audited (§6), each with its verdict: evidenced carrier, or searches performed + empty;
* VALIDATED vs CANDIDATE per component with exact reasons (§10);
* genuine KB/API coverage gaps encountered (fail-closed, per the discovery-api-usage protocol).

## 13. Coverage fixtures (quarantined)

This section lists **property-form checks** the generic process must surface when applied to a seed. They are regression coverage only: never feed them into the probe set, never special-case a failed fixture, never let them become a search strategy. A fixture that fails is reported as a **process gap** (§12), and the failure is investigated in the process — never patched by naming the fixture's subject inside the algorithm.

* an item carrying ≥2 simultaneously usable applies-to bridge stats, composed **together** in one build;
* a single item converting ≥3 attributes into different resources;
* attribute→resource engine rules surfaced via intrinsic rows on probed stats;
* stat families with zero unique carriers reaching the CANDIDATE tier with the exact gap reason;
* an accuracy/hit-chance audit performed for every attack build (evidenced carrier, or recorded empty search);
* charge generation/consumption families linked to the axis;
* per-pool consumer families for every pool stat the axis touches;
* a spell→attack damage bridge when the output is attacks; DoT/ailment-multiplier families when the output is chaos/ailment damage.

## Objective

Find coherent build concepts where investment in X produces **quadratic or higher-order scaling**, then **grow the architecture subgraph to its fixed point**: re-evaluate every allocated node for further interacting layers until a full sweep adds nothing.

**X → A, X → B, A × B → output**

The seed starts the walk; the best-evidenced axis carries the scaling; the seed stays part of the structure. Multi-use, compound, generator-spender, and deep architectures matter only insofar as they help discover or expand such interacting dependencies.

**The primary target is genuine quadratic-or-higher scaling, not merely many uses of the same stat.**
