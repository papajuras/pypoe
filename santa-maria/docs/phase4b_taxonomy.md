# Phase 4B — Semantic Node Taxonomy (proposal, revised)

Proposal for what counts as a node in the PoE mechanics knowledge graph.
**No nodes are created here; no edges.** This only decides entity types.
Inputs: `phase4a_profile.json`, `phase4a_summary.md`, `phase4a_checks.md`,
`phase4b_unresolved_check.md` (all produced from `cache/raw_records.db`).

## Hard constraints

- **Node schema (mandatory):** `node_id | type | origin | payload`.
  All Phase 4 nodes have `origin = source` (extracted directly from game
  data; derived nodes are out of scope).
- **Edge tiers** every proposed type is evaluated against:
  T1 shared stat_id · T2 shared tag/domain · T3 hub/conversion
  (`_applies_to_`, `_gained_as_`, `_at_<N>%_value`, `stat_value_handlers`) ·
  T4 hub producers/consumers · T5 manual cluster gating.
- **Established facts (from 4A checks + 4B sweep, treated as fixed):**
  1. Unique item stats live in `mods.json`, reached from `uniques.json` via
     a **multi-method resolver**, not a single cross-reference:
     `visual_identity.id → modifier key` is only the **fast-path heuristic**;
     the full-set sweep (below) showed it is incomplete. Whatever method is
     used, resolved modifiers are filtered to `generation_type == 'unique'`
     AND non-null `text`, EXCLUDING `Royale` variants, `old_do_not_use_*`
     stats, and null/dummy entries (verified on Crown of Eyes, Mageblood,
     Headhunter, The Squire).
  2. Real conversion mechanics live in `mods.json` stat ids with
     `_at_<N>%_value` suffixes (+ `stat_value_handlers.json`). `gems.json`
     `stat_conversions` is an **alias/rename map** (Tier-1 id normalization),
     not a Tier-3 conversion signal.
  3. **UniqueItem → Modifier resolution sweep baseline** (from
     `phase4b_unresolved_check.md`, over the 967 uniques the vid-substring
     could not resolve): **880 candidate text matches** via **normalized
     effect-text matching** (association-level matches, **not yet
     semantically validated** — modifier keys are semantic names, e.g.
     `ReflectBleedingToSelfUnique__1`), **84** have no PoB display text
     usable by that method (mapped to `no_source_text_for_current_method` —
     not absence), **3** remain unmatched. **Methods 3–4 (replica→base,
     passive-grant) were not systematically applied or validated in this
     sweep.** Empty `resolved_targets` is **not** evidence of "no structured
     mechanics".

## Core principle: node storage ≠ LLM/query exposure

A large population of nodes (e.g. ~40k Modifiers) is **not** a problem by
itself. The query/LLM layer can expose only the relevant subset; the graph
layer retains everything deterministic. Concretely, per node type:

1. **nodes** are stored exhaustively when they carry a deterministic join
   surface (stat ids, tags, groups) that would otherwise have to be
   reconstructed from raw data later;
2. **exposure/filtering** happens at query time, deterministically, via
   `ModifierGroup`, stat, tag, domain, `generation_type`, etc. — not by
   dropping nodes at ingestion;
3. **ranking** (relevance scoring for the LLM) is a query-layer concern and
   is out of scope here, but the taxonomy must not bake in a size-based
   exclusion that a later ranking layer cannot undo.

This is the rationale behind keeping `Modifier` as a candidate node type.

---

## 1. Stat

- **source** — `repoe/stats.json` (record_key = the stat id; 23,344
  records: `{alias, is_aliased, is_local}`). The **observed union** of stat
  ids is wider: `mods.json stats[].id` (10,564 distinct), passive-tree
  `stats` keys (1,219 in Default), gem `per_level`/`static`/`constant_stats`
  and `stat_conversions` (both sides). Canonical node set = `stats.json`
  keys; ids referenced elsewhere but absent from `stats.json` are added as
  observed-only nodes (flagged). **`stat_conversions` KEYS are gem-local
  alias names, not stats** — they are normalized via the alias map to the
  canonical id (retained on the Gem payload) and are NOT added as
  observed-only Stat nodes.
- **identity** — the stat id string itself (`strong_casting`,
  `base_chance_to_ignite_%`, `local_energy_shield_+%`). Unique and stable.
- **candidate node type** — `Stat`.
- **inclusion/exclusion** — Retain all `stats.json` record_keys **as a
  data-model decision**: they are the critical **join atoms** for Tier 1/3
  (every cross-file edge flows through a stat id), which is a stronger
  reason than any claim that every entry is a meaningful player-facing
  mechanic. `stats.json` is an **observed/stat registry**: it contains
  aliases (`is_aliased`, `alias.when_in_main_hand/off_hand`),
  display-oriented dummies, and legacy ids. None of these are silently
  dropped — they are **flagged** (`legacy`, `dummy`, `observed_only`) in the
  payload so the taxonomy never erases information. The "is this a real
  mechanic" question is a later semantic-layer concern, not a 4B gate.
- **payload** — `{is_local, is_aliased, alias (when_in_off_hand /
  when_in_main_hand), flags: [legacy|dummy|observed_only], observed_in: [sources]}`.
- **provenance** — `raw_records('repoe/stats.json', <stat_id>,
  repoe@<commit>)`; observed-only ids carry the file/record_key they came from.
- **potential relations** — referenced by `Modifier.stats[].id`, `Passive.stats`
  keys, `Gem` (per_level/static/stat_conversions), `Buff.stats`;
  `stat_conversions` links Gem-local alias ids → canonical Stat ids.
- **problems/ambiguities** — name collisions (a stat id is a flat string;
  no namespaces); `alias.when_in_main_hand/off_hand` implies context-split
  behavior; some ids are display dummies. The `record_key` signal is the
  same heuristic set as mods' `field_id` — a few ids may be tag-like, not
  real stats (4B does not resolve this; flagged for 4C).
- **relevant tiers** — **T1** (the join atom), **T3** (conversion is a
  property OF stat ids: `_at_<N>%_value` etc. — detected on the id string),
  **T4** (hub producers/consumers enumerated per stat).
- **tier-readiness of payload** — Yes for T1 (raw id). For T3, the raw id +
  a link to `stat_value_handlers.json` (see §"supporting data") must be
  retained to later decide full vs partial magnitude; the id string alone is
  retained, so suffix detection is lossless.

---

## 2. Modifier

- **source** — `repoe/mods.json` (record_key = mod key; 40,354 records).
  Fields: `generation_type` (34 values), `domain` (42), `text`, `name`,
  `stats[].id/min/max`, `groups[]`, `spawn_weights[].tag/weight`,
  `implicit_tags[]`, `adds_tags[]`, `required_level`, `is_essence_only`,
  `grants_effects[].granted_effect_id`, `gold_value`.
- **identity** — the mods.json record_key (e.g. `Strength1`,
  `LocalIncreasedEnergyShieldUniqueHelmetInt7`, `FireResistUniqueHelmetInt7`).
  Unique, stable, arbitrary.
- **candidate node type** — `Modifier`.
- **inclusion/exclusion** — **Include all 40,354.** The justification is
  **not** that every Modifier is a semantic "concept". A `Strength1`-style
  flat roll is an **exact source entity / mechanic carrier**: it is the
  record that carries the `modifier → stat_id/value → tag → text → group`
  join surface. Dropping per-roll records would destroy the only lossless
  deterministic join surface, which would later have to be reconstructed
  from raw data. Key points:
  - node **storage** is kept exhaustive (join surface);
  - **query/LLM exposure** is a separate layer: candidates are filtered and
    ranked deterministically via `ModifierGroup`, stat, tag, domain,
    `generation_type` (the query layer exposes only the relevant subset);
  - the coarser **conceptual** aggregation is `ModifierGroup` (§3), not a
    reason to delete Modifiers.
  `domain=monster/area` etc. are included (they reference real stat ids).
- **payload** — `{generation_type, domain, text, name, required_level,
  is_essence_only, gold_value, groups[], spawn_weights[{tag,weight}],
  implicit_tags[], adds_tags[], stats[{id,min,max}], grants_effects[]}`.
- **provenance** — `raw_records('repoe/mods.json', <mod_key>,
  repoe@<commit>)`.
- **potential relations** — `Modifier → Stat` (many, via `stats[].id`);
  `Modifier → Tag` (spawn/implicit/adds tags); `Modifier → ModifierGroup`
  (via `groups[]`); `Modifier → Buff` (via `grants_effects[].granted_effect_id`,
  pending profiling); `UniqueItem → Modifier` (resolver, §5).
- **problems/ambiguities** — (a) unique linkage is a heuristic (over-matches
  Royale/dummy/legacy; under-covers) — see §5; (b) `domain`/
  `generation_type` overlap (`crucible_tree` spans domains); (c) legacy
  `old_do_not_use_*` stats coexist with modern permyriad ones in separate
  records of the same mod.
- **relevant tiers** — **T1** (`stats[].id`), **T2** (tags/domain),
  **T3** (the verified carrier of `_at_<N>%_value` conversion stat ids),
  **T4** (once a hub stat is known, its producers = Modifiers feeding it,
  consumers = Modifiers using it).
- **tier-readiness of payload** — Yes. T3 needs the raw stat id (retained)
  + min/max (magnitude for full/partial) + `text` + a link to
  `stat_value_handlers` (retained via §"supporting data"); completeness
  (full vs partial/conditional) is derivable at edge-gen time from these.

---

## 3. ModifierGroup (candidate — status pending 4C)

- **source** — `repoe/mods.json` `groups[]` (7,325 distinct) and
  `pob/ModItemExclusive.json` `group` (4,180 distinct). These are **two
  different vocabularies** and must not be silently equated.
- **identity** — the group string (`LifeLeech`, `ChanceToIgnite`). Strings
  can collide across domains/contexts; treated as a coarse grouping id, with
  payload listing the domains it appears in.
- **candidate node type** — `ModifierGroup` (candidate aggregation/index).
- **inclusion/exclusion** — Do **not** assume `mods.json.groups[]`
  necessarily represents a true semantic mechanic concept. The final status
  of this node type depends on **4C validation**. Distinct readings of the
  same data:
  - **source grouping / crafting identity** — RePoE `groups[]` and PoB
    `group` are the game's mod-group identifiers (used by crafting
    benches / exclusion rules); this is what the data actually guarantees;
  - **semantic mechanic concept** — whether `LifeLeech`-style group == a
    player-facing mechanic concept is a **hypothesis** to validate, not a
    given;
  - **query/traversal aggregation** — ModifierGroup is useful regardless of
    the above as a deterministic bucket (T2 batching, T5 curation anchor).
  Propose the node type for its aggregation/index value; mark semantic
  equivalence as unproven until 4C.
- **payload** — `{domains: [...], generation_types: [...], member_count,
  representative text, source_vocab: [repoe_groups|pob_group]}`.
- **provenance** — derived from `mods.json groups[]` /
  `ModItemExclusive.group` (origin still `source`; crossref-counted in 4A:
  7,325 / 4,180).
- **potential relations** — `ModifierGroup → Modifier` (members);
  `ModifierGroup → Stat` (union of member stat ids).
- **problems/ambiguities** — group name reuse across domains; RePoE vs PoB
  group vocabularies overlap only partially and must be mapped, not merged.
- **relevant tiers** — **T2** (group-level candidate batching),
  **T5** (manual conjunction gating anchor).
- **tier-readiness** — T2 yes (group id); T5 yes (curation anchor).

---

## 4. UniqueItem

- **source** — `repoe/uniques.json` (record_key numeric string; 1,556
  records: `id/name, item_class, inventory_width/height, is_alternate_art,
  visual_identity{id, dds_file}, renamed_version, base_version`). No stats
  in this file. Modifier stats are reached via the **multi-method resolver**
  below.
- **identity** — the uniques record_key (numeric string, unique + stable).
  The `id`/`name` is a display property, NOT the identity: alternate-art
  records and renamed/base versions share a name but are distinct records.
- **candidate node type** — `UniqueItem`.
- **inclusion/exclusion** — Include all 1,556. Alternate-art / renamed /
  base-version variants are separate records; they are kept as separate
  nodes linked via `renamed_version`/`base_version` (payload), not merged.
  **Unresolved or unmatched uniques are never discarded.**
- **payload** — `{name/id, item_class, inventory dims, is_alternate_art,
  visual_identity{id, dds_file}, base_version, renamed_version,
  resolved_targets: [{target_type: Modifier|Passive, target_key, method, status}],
  resolution_status, resolution_evidence}`.
- **provenance** — `raw_records('repoe/uniques.json', <key>,
  repoe@<commit>)`; each resolved target carries its own provenance.
- **potential relations** — `UniqueItem → Modifier` (resolved set, methods
  1–3); `UniqueItem → Passive` (method 4, passive-grant); `UniqueItem →
  ItemClass`; `UniqueItem → Stat` (transitively via resolved mechanic
  carriers such as Modifier or Passive); `UniqueItem → UniqueItem`
  (base/renamed/alternate linkage).
- **problems/ambiguities — the resolver is a MULTI-METHOD cross-reference.**
  The 4B sweep (`phase4b_unresolved_check.md`, `phase4b_sweep.json`)
  disproved the assumption that `visual_identity.id → mods.json key
  substring` is the (complete) UniqueItem → Modifier link. It is a
  **fast-path heuristic only**. The resolver must be modeled as a
  multi-method cross-reference, with methods of **unequal evidential
  strength**:
  1. **visual_identity.id → modifier key** — direct naming match
     (fast path; the classic Crown-of-Eyes case);
  2. **normalized effect/display-text matching** — the bulk of the 880
     **candidate text matches** in the sweep (association-level matches,
     **not yet semantically validated**); modifier keys are semantic
     (`ReflectBleedingToSelfUnique__1`); evidence = matched effect line +
     candidate mod keys;
  3. **replica → base-unique resolution** — replicas (`…21x`) share the
     base unique's (`…21`) modifier set where applicable;
  4. **passive-grant resolution** — a unique's mechanic represented by a
     passive rather than a direct mod (e.g. Natural Affinity →
     `JewelExpansionNaturesPatience`). This method resolves to a **Passive**
     (`UniqueItem → Passive`), **not** a Modifier; methods 1–3 typically
     resolve to a `UniqueItem → Modifier`.
  The taxonomy must **not** assume methods 1–4 have identical evidential
  strength: provenance must record **which method(s)** established each
  UniqueItem → resolved-target association so a later consumer can weigh or
  re-run them. Consequences:
  - an **empty `resolved_targets` is NOT proof** the unique has no structured
    mechanics; it may mean `unresolved_by_current_resolver` or
    `no_source_text_for_current_method`;
  - **"no match" and "no display text" are not proof of absence.** The
    `resolution_status` must be at minimum: `resolved` /
    `partial_or_indirect` / `unresolved_by_current_resolver` /
    `no_source_text_for_current_method` / `genuinely_absent_confirmed`
    (partial = some mechanics resolved, some not; indirect = association
    inferred indirectly, e.g. a shared/ambiguous text match, not a primary
    resolution method; `genuinely_absent_confirmed` requires
    **evidence-backed absence** from the structured mods/passive
    representation, e.g. retired/removed content — not merely a
    failed lookup);
  - **method-2 (text) matches are candidate associations** — the 880 sweep
    figure is association-level, **not yet semantically validated**, so it
    must not be treated as confirmed resolution; `resolution_status` for a
    text match is only `resolved` after validation/confirmation;
  - `resolution_evidence` retains, per resolved association, the method,
    matched text/phrase, and candidate target keys, so a later, better
    resolver can re-run without re-deriving from raw data;
  - **resolution evidence is NOT a new node type** — the graph relationship
    remains conceptually `UniqueItem → Modifier → Stat` or
    `UniqueItem → Passive → Stat`; resolution method and confidence belong
    to **provenance / lookup data / relationship-generation evidence**, not
    to a new graph entity.
  Resolver implementation is **out of scope** here; the taxonomy only keeps
  the provenance/evidence that makes later resolution possible.
- **relevant tiers** — **T1** (via resolved mechanic carriers' stat ids),
  **T3** (a unique carrying an `_at_<N>%_value` modifier, e.g. Crown of
  Eyes), **T4**.
- **tier-readiness** — Yes: resolved target keys + their stat ids are in
  payload; T3 magnitude flows from the modifier payload. Unresolved items
  simply have no edges until the resolver improves — they are not dropped.

---

## 5. Passive

- **source** — `repoe/passive_skill_trees/*.json` (7 files). A tree is a
  **single-file record** in the raw snapshot; the entity unit is one entry
  of its `passives` map (keyed by numeric hash string): `{hash, id, name,
  flavour_text, icon, reminder_text, skill_points, is_keystone,
  is_notable, is_jewel_socket, is_ascendancy_starting_node, is_multiple_choice(…),
  stats:{stat_id: value}}`. Counts: Default 2,987 (49 keystone, 696
  notable, 60 jewel socket); Atlas 1,029; Royale 212; BrequelTree 134; etc.
- **identity** — the passive `id` field (e.g. `iron_will_keystone2850`,
  `avatar_of_fire1543`). The same node appears in multiple trees
  (Default + DefaultAltAscendancies overlap); node_id = `id`, payload lists
  every tree + hash it appears under.
- **candidate node type** — `Passive`, with a `kind` discriminator
  (`keystone | notable | jewel_socket | ascendancy_start | multiple_choice | regular`).
  Keystone is the Tier-relevant subset, not a separate node type.
- **inclusion/exclusion** — **Do not pre-delete "regular" passives.** They
  are entities in the source model and carry stat ids, which may be required
  for later queries/edges (e.g. every notable/jewel node on a cluster, or
  ascendant-style edge cases). Distinguish, rather than delete:
  - **meaningful semantic passives/keystones/notables** — candidate high-value
    nodes (T3-relevant keystones, etc.);
  - **ordinary stat-granting passives** — retained as nodes (they are
    entities + carry stat ids → deterministic T1 joins); their *exposure*
    is a query-layer decision;
  - **tree scaffolding** (`art`, `groups`, `roots`, `title`) — NOT nodes,
    retained as tree provenance only.
  The inclusion test is: is the passive an entity in the source model, and
  does retaining it enable deterministic joins? Both are true for regular
  passives — do not invent a size-based exclusion.
- **payload** — `{id, name, kind flags, flavour_text, icon, reminder_text,
  skill_points, stats:{stat_id: value}, trees:[{file, hash}]}`.
- **provenance** — `raw_records('repoe/passive_skill_trees/<file>', '',
  repoe@<commit>)`, entry addressed by `passives.<hash>`.
- **potential relations** — `Passive → Stat` (stats map keys; Tier 1);
  `Passive → Passive` (ascendancy/multiple-choice grouping, via
  flags + tree structure, not yet extracted); `UniqueItem` none.
- **problems/ambiguities** — same passive id across trees must be deduped
  (hash differs per tree? recorded, not resolved here); **dedup by `id`
  assumes the same passive has identical `stats` across trees** — if a
  shared id ever differs by tree, the node would hold only one variant, so
  per-tree stats (or the same-id-same-stats assumption) must be recorded;
  `stats` values are
  magnitudes (usually 1 = marker) but keystone conversion semantics live in
  the referenced stat id (e.g. `strong_casting`), not in the passive record
  itself — the passive alone does NOT encode "Strength becomes Spell
  Damage"; that is the Stat/Modifier layer.
- **relevant tiers** — **T1** (stats keys), **T3** (keystones may reference
  conversion mechanics, but see tier-readiness caveat), **T4**.
- **tier-readiness** — T1 yes (raw stat ids retained). **T3 is NOT directly
  supported by the passive payload alone:** a keystone's own stat id (e.g.
  `strong_casting`) is a marker, NOT the T3 conversion carrier — the
  conversion stat (e.g.
  `additive_spell_damage_modifiers_apply_to_attack_damage_at_150%_value`)
  lives on Modifiers under a **different** id, and no retained field links
  the two. Reaching T3 from a keystone therefore requires a stat↔display
  alias bridge (`stat_translations.json` — currently a candidate supporting
  source) to be elevated to a required supporting lookup. Until then, the
  T3 claim for Passives is conditional, not derivable from retained payloads.

---

## 6. Gem

- **source** — `repoe/gems.json` (record_key = gem name; 1,458 records):
  `active_skill{id, types[], description, …}`, `base_item{id, …}`,
  `is_support`, `color`, `tags[]`, `per_level` (keyed by level string:
  costs, stats[{}], stat_text{…}, required_level…), `static`,
  `stat_conversions{alias_stat: canonical_stat}` (701/1,458 gems),
  `quest_reward`, `tooltip_order`.
- **identity** — gems record_key (`Fireball`, `VaalFireball`,
  `Absolution`, `AbsolutionAltX`). Stable; variant entries (`AltX`) are
  separate records.
- **candidate node type** — `Gem`.
- **inclusion/exclusion** — Include all 1,458. Per-level stat lines are
  NOT separate nodes — retained in the Gem payload (`per_level`), as they
  are level-scaling values of the gem, not entities.
- **payload** — `{active_skill.id/types, base_item.id, is_support, color,
  tags[], per_level (compact: level → stat_text + stat ids/values),
  static, stat_conversions, quest_reward}`.
- **provenance** — `raw_records('repoe/gems.json', <gem_key>,
  repoe@<commit>)`.
- **potential relations** — `Gem → Stat` (per_level/static stat ids AND
  both sides of `stat_conversions`); `Gem → Tag` (types/tags).
- **problems/ambiguities** — `stat_conversions` is a **gem-local alias →
  canonical stat id** rename map (verified: values are bare stat-id
  strings, no magnitude/full-partial). It must be used as a **Tier-1
  normalization lookup** (map gem-local ids to canonical before joining),
  NOT as a conversion/Tier-3 signal. `stat_text` keys can embed literal
  `\n`; `per_level.stats` has null slots.
- **relevant tiers** — **T1** (normalized stat ids), **T2** (types/tags).
  **Not T3** (no conversion semantics here).
- **tier-readiness** — T1 yes (ids + alias map retained). T3 intentionally
  not provided here.

---

## 7. Tag

- **source** — tag vocabulary observed in `mods.json` (`spawn_weights[].tag`
  499 distinct, `implicit_tags[]` 58, `adds_tags[]` 52) and the candidate
  supporting sources `repoe/tags.json` / `repoe/tag_details.json`
  (see unlisted-source section).
- **identity** — the tag string (`fire`, `attack`, `ailment`,
  `str_armour`, `2h_axe_adjudicator`).
- **candidate node type** — `Tag`.
- **inclusion/exclusion** — Include the deduplicated tag vocabulary. Tag
  occurrences (weights) are NOT nodes — retained on the Modifier payload.
- **payload** — `{name, used_as: [spawn_weights|implicit_tags|adds_tags],
  observed_count}` (extends with `tags.json` inheritance when profiled).
- **provenance** — observed from `mods.json` (source); `tags.json` candidate.
- **potential relations** — `Modifier → Tag`; `Tag → Tag` (inheritance, if
  `tags.json` provides it).
- **problems/ambiguities** — two vocabularies (base tags vs spawn-weight
  tags with suffixes); inheritance is in a candidate supporting source.
- **relevant tiers** — **T2** (the coarse grouping axis).
- **tier-readiness** — yes.

---

## 8. ItemClass

- **source** — `uniques.json item_class` (22 values) and the candidate
  supporting source `repoe/item_classes.json` (see unlisted-source section).
- **identity** — the class string (`Helmet`, `Ring`, `Body Armour`,
  `HeistContract`…).
- **candidate node type** — `ItemClass`.
- **inclusion/exclusion** — Include the vocabulary (small). Class-specific
  crafting/equip metadata lives in the candidate supporting file.
- **payload** — `{name, observed_from: [uniques, base_items…]}`.
- **provenance** — `uniques.json`/`base_items` observed; `item_classes.json`
  candidate.
- **potential relations** — `UniqueItem → ItemClass`; (later) `ItemBase →
  ItemClass`.
- **problems/ambiguities** — none significant.
- **relevant tiers** — **T2** (grouping axis).
- **tier-readiness** — yes.

---

## 9. Buff (provisional — needs profiling)

- **source** — `mods.json grants_effects[].granted_effect_id` (701 distinct
  ids like `Affliction`, `HeraldOfTheBreach`) cross-references the candidate
  supporting source `repoe/buffs.json`.
- **identity** — the buff id (pending confirmation of the buffs.json key).
- **candidate node type** — `Buff`.
- **inclusion/exclusion** — Proposed because Modifier already references
  buffs; finalize only after `repoe/buffs.json` is profiled.
- **payload** — TBD from buffs.json profiling (stat ids, max stacks,
  groups).
- **relevant tiers** — **T1** (buff stat ids).
- **tier-readiness** — not yet assessable.

---

## Supporting data required per node type (nodes vs data-retention)

A source record can occupy one of five roles. "Not a node" never means
"discard it".

1. **a node** — the entity itself (above).
2. **payload of another node** — carried verbatim on the owning node.
3. **evidence/provenance** — recorded so a later step can re-derive.
4. **lookup/index for deterministic resolution** — a function, not an entity.
5. **raw-snapshot-only** — retained in `raw_records.db`; not exposed.

Per node type, the required **supporting** data even if it is not a node:

| node type | supporting data (not a node) | role |
|---|---|---|
| Stat | `stat_value_handlers.json` (candidate source) | T3 magnitude/completeness lookup |
| Stat | `stat_translations.json` + `stat_translations/*` (candidate sources) | display text lookup |
| Stat | `gems.json` `stat_conversions` | T1 alias normalization lookup (map gem-local → canonical id before joining) |
| Stat | PoB `SkillStatMap.json` (candidate source) | same alias-normalization role on the PoB side |
| Modifier | `mods_by_base.json` (candidate source) | mod → base spawn-context lookup |
| Modifier | `mod_types.json`, `crafting_bench_options.json`, `essences.json`, `fossils.json` (candidate sources) | eligibility/crafted-mod lookups |
| Modifier | PoB `ModItem.json`, `ModScalability.json` (candidate sources) | statOrder + value-scaling lookups (T3 magnitude) |
| UniqueItem | **multi-method unique-modifier resolver** (method 1 vid-substring fast path; method 2 normalized effect-text matching; method 3 replica→base fallback; method 4 passive-grant keys → resolves to a **Passive**, not a Modifier) | resolution is a **lookup function**, not a node; each method has **unequal evidential strength**; taxonomy keeps per-association `method` + `resolution_status` + `resolution_evidence` (roles 3+4) so a later consumer can weigh, re-run, or improve it |
| UniqueItem | `pob/ModItemExclusive.json`, `pob/QueryMods.json`, `pob/TradeSiteStats.json`, `pob/ModCache.json` | supporting lookups: trade-hash → trade-stat-id → text, mod → tradeMod.id, display-text cache (none are nodes) |
| UniqueItem | `pob/Uniques/*.json` text blocks | resolver input/evidence for method 2 (normalized effect-text matching) — role 3 |
| Passive | tree `groups`/`roots`/`title` | tree provenance only |
| Gem | `active_skill_types.json` (candidate source) | T2 type-tag lookup |
| Tag | `tags.json`, `tag_details.json` (candidate sources) | inheritance/weight lookup |

`ModItemExclusive`, `QueryMods`, `TradeSiteStats`, `ModCache` are therefore
**lookup/index data** in this taxonomy — they power deterministic resolution
(trade representation, query building, display) but are not mechanics nodes.
Materialization of these role-4 lookups (a derived lookup table in the
graph DB, or a query-time function over `raw_records.db`) is a 4C/4D
concern; the raw snapshot is the durable store either way.

---

## Not-a-node decisions (with retention mapping — feeds 4C coverage checks)

| data | why not a node | retention role |
|---|---|---|
| `Strength1`-style per-roll Modifier records | they ARE nodes (§2) — the exact mechanic carrier; the *concept* is ModifierGroup (pending 4C) | Modifier node + ModifierGroup node |
| Gem `per_level` stat lines | level-scaling values of the gem, not entities | Gem payload (`per_level`) |
| `gems.json` `stat_conversions` | alias/rename map, not an entity | Gem payload; used as a T1 normalization lookup |
| TradeSiteStats entries (`explicit.stat_*`) | trade-site display/query lookup, not mechanics | lookup/index (role 4) |
| QueryMods slot maps (`tradeMod.id`, min/max per slot) | trade-query construction data | lookup/index; the trade ids are the join keys |
| ModCache entries | parsed-condition text cache | lookup/index keyed by mod display text |
| `spawn_weights[].tag/weight` occurrences | a tag is the node; the weight is a property | Tag node + Modifier payload |
| PoB `Uniques/*.json` text blocks | display text; the resolver uses them as **evidence** | resolver input / evidence for method 2 (role 3) |
| UniqueItem resolution `method`/`confidence`/`evidence` | resolution provenance, NOT a graph entity | relationship-generation evidence (roles 3+4); relationship stays `UniqueItem → Modifier → Stat` or `UniqueItem → Passive → Stat` |
| `stats_by_file.json` | provenance index | lookup for coverage audits (role 4) |
| `data-formats/*` JSON-Schemas | documentation, not data | repo docs |
| tree scaffolding (`art`, `groups`, `roots`, `title`) | structure, not entities | tree provenance (role 3) |
| `gold_value`, `tooltip_order`, `quest_reward` etc. | metadata | retained on the owning node's payload |

---

## Unlisted sources — candidate supporting sources, not scope expansion

The 319 unlisted files from `phase4a_profile.json` are **candidate
supporting sources requiring targeted profiling**. They are **not** an
automatic expansion of the Phase 1 download scope. 4C determines which are
actually **load-bearing** for the approved taxonomy; only sources
demonstrated to be necessary trigger a later, targeted data step. Until
then they remain unprofiled and are flagged per node type as "needs
targeted profiling before finalizing":

- **Stat (Tier 3 readiness):** `repoe/stat_value_handlers.json`,
  `repoe/stat_translations.json` (+ dir), `repoe/stats_by_file.json`.
- **Modifier:** `repoe/mods_by_base.json`, `repoe/mod_types.json`,
  `repoe/crafting_bench_options.json`, `repoe/essences.json`,
  `repoe/fossils.json`, `repoe/buffs.json`; the PoB `Mod*` family —
  `ModItem.json`, `ModScalability.json`, `ModExplicit/ModImplicit/ModVeiled/
  ModMaster/ModDelve/ModSynthesis/ModEldritch/ModJewel*/ModMap/ModFlask/
  ModCorrupted/ModScourge/ModTincture/ModNecropolis/ModMercenary/ModFoulborn*/
  ModGraft.json`, plus `Essence.json`, `ClusterJewels.json`, `Rares.json`,
  `Vestigial.json`, `Pantheons.json`, `BossSkills.json`, `Crucible.json`,
  `BeastCraft.json`.
- **Passive:** `repoe/cluster_jewel_notables.json`,
  `repoe/cluster_jewels.json`, `pob/TimelessJewelData/LegionPassives.json`,
  `pob/TattooPassives.json`, `pob/ClusterJewels.json`.
- **Gem (Tier 2):** `repoe/active_skill_types.json`; `pob/Gems.json`,
  `pob/SkillStatMap.json`, `pob/Skills/*`, `pob/StatDescriptions/*`.
- **Tag / ItemClass:** `repoe/tags.json`, `repoe/tag_details.json`,
  `repoe/item_classes.json`.
- **ItemBase (candidate, not yet proposed):** `repoe/base_items.json` (+ 87
  dir) and `repoe/Metadata/Items/*` — base items carry implicit mods; if
  implicits are wanted as first-class they drive a new node type that needs
  this targeted profiling first.

---

## Summary — node types × tiers

| node type | identity | T1 | T2 | T3 | T4 | T5 | needs profiling before lock |
|---|---|---|---|---|---|---|---|
| Stat | stat id | ✓ | | ✓ | ✓ | | stat_value_handlers, stat_translations |
| Modifier | mods key | ✓ | ✓ | ✓ | ✓ | | Mod* family, mods_by_base, mod_types, crafting family, buffs |
| ModifierGroup (candidate) | group string | | ✓ | | | ✓ | semantic equivalence → 4C validation |
| UniqueItem | uniques key | ✓ | | ✓ | ✓ | | multi-method resolver (vid fast-path + effect-text + replica-base + passive-grant → Modifier or Passive) |
| Passive | passive id | ✓ | | (✓)* | ✓ | | cluster/legion/tattoo passives; T3 requires stat_translations bridge |
| Gem | gem key | ✓ | ✓ | ✗ | | | active_skill_types, PoB Gems/SkillStatMap |
| Tag | tag string | | ✓ | | | | tags.json, tag_details |
| ItemClass | class string | | ✓ | | | | item_classes.json |
| Buff (provisional) | buff id | ✓ | | | | | buffs.json |

`*` Passive T3 is conditional on a stat↔display alias bridge
(`stat_translations.json`) being elevated from candidate to required — see
the Passive tier-readiness note.

## Open items handed to 4C

1. **Coverage gaps**: uniques with `resolution_status = unresolved_by_current_resolver`,
   `no_source_text_for_current_method` (the 84 no-display-text items), or
   `genuinely_absent_confirmed` (baseline from the 4B sweep: **880 candidate
   text matches, not yet semantically validated** / 3 not-found / 84 no-text
   of the 967 vid-unresolved; method-2 only — methods 3–4 were not
   systematically applied); observed-only stat ids absent from `stats.json`;
   the candidate supporting sources above (4C decides which are load-bearing).
2. **Tier-3 completeness**: full vs partial/conditional conversion is
   decided at edge-generation from `Modifier.stats[].id` + `min/max` +
   `stat_value_handlers.json` — confirm the handler linkage during the
   targeted stat_value_handlers profile.
3. **Alias normalization**: `gems.json` `stat_conversions` and (candidate)
   PoB `SkillStatMap.json` should feed a shared stat-alias lookup used by
   Tier-1 joins; whether alias semantics exist implicitly on non-gem sources
   remains an open question.
4. **UniqueItem resolver (multi-method)**: `resolution_status` /
   `resolution_evidence` / per-association `method` are retained so the
   resolver can be improved (effect-text, replica-base, passive-grant →
   Modifier or Passive) without re-deriving from raw data; the vid-substring
   fast path must not be the only method.

### 4C coverage requirements for UniqueItem (updated by the sweep)

- **No silent loss**: UniqueItem extraction must not drop modifier
  associations merely because the `visual_identity.id` heuristic fails —
  unresolved-by-heuristic ≠ no mechanics.
- **Re-runnable resolver**: retained data must allow the UniqueItem →
  resolved-target (Modifier or Passive) resolver to be re-run or improved
  later (per-association `method`, `status`, and the matching text/key
  evidence).
- **Method-distinguished provenance**: provenance must distinguish
  direct/naming matches (method 1) from text-based (method 2),
  replica/base (method 3), and passive-grant (method 4, → Passive)
  resolution.
- **Diagnostic separation**: "no resolved target" and "no source text for
  the current method" must remain diagnostically distinct from "resolver
  failed" and from evidence-backed absence (`genuinely_absent_confirmed`),
  via `resolution_status`.
- **Raw snapshot authoritative**: `raw_records.db` / `data/` are never
  modified by resolution or extraction.

---

## Changes from previous taxonomy

1. **Modifier justification corrected.** Previously framed as "a concept
   node". Now explicitly: `Modifier` is an **exact source entity / mechanic
   carrier** retained for its deterministic join surface; node **storage**
   is separated from **query/LLM exposure** (filtering/ranking via
   ModifierGroup, stat, tag, domain, generation_type is a query-layer
   decision). No size-based exclusion.
2. **ModifierGroup certainty downgraded.** No longer asserted to be a
   semantic mechanic concept. It is a **candidate aggregation/index node**
   whose semantic reading is unproven until 4C; the three distinct readings
   (source/crafting identity vs semantic concept vs query/traversal
   aggregation) are separated, and the RePoE `groups[]` vs PoB `group`
   vocabularies are no longer equated.
3. **Stat wording corrected.** `stats.json` is an **observed/stat registry**
   that may contain aliases, dummies and legacy ids; retaining all registry
   ids as candidate `Stat` nodes is stated as a **data-model decision**
   (join atoms) rather than a claim that every entry is a meaningful
   mechanic. Legacy/dummy/observed-only info is flagged, not dropped.
4. **Passive inclusion revisited.** Regular passives are **kept** as
   candidate nodes (they are source-model entities carrying stat ids for
   deterministic T1 joins); the meaningful-vs-ordinary-vs-scaffolding
   distinction replaces any size-based exclusion.
 5. **UniqueItem resolver finding incorporated.** The
    `visual_identity.id` substring resolver is now explicitly **incomplete**;
    the 4B sweep (880 **candidate text matches** / 3 not-found / 84 no-text;
    association-level, **not yet semantically validated**) is cited;
    `resolution_status` (resolved /
    unresolved_by_current_resolver / genuinely_absent_confirmed /
    partial_or_indirect / no_source_text_for_current_method) and
    `resolution_evidence` are added so an empty `resolved_targets` is never
    treated as proof of absence.
 6. **Node vs data-retention strengthened.** A five-role retention model
    (node / payload / evidence / lookup / raw-snapshot-only) is now explicit,
    with a supporting-data table per node type (ModItemExclusive, QueryMods,
    TradeSiteStats, ModCache, stat_translations, stat_value_handlers, and
    the unique-modifier resolver all identified as lookup/evidence, not
    nodes).
 7. **Unlisted-source section reconsidered.** Reframed as **candidate
    supporting sources requiring targeted profiling**; no automatic scope
    expansion; 4C decides which are load-bearing for the approved taxonomy.
 8. **Preserved unchanged:** node schema (`node_id | type | origin | payload`),
    `origin = source`, the T1–T5 tier analysis, payload/provenance sections,
    bloat discussion, retention mapping, conversion-readiness discussion,
    raw-vs-extracted distinction.

---

### Revision from Unique Resolution Sweep

Substantive changes in this revision (driven by `phase4b_unresolved_check.md`
and `phase4b_sweep.json`, full-set over the 967 vid-unresolved uniques):

1. **UniqueItem → Modifier is now a multi-method resolver, not a single
   cross-reference.** The `visual_identity.id → mods.json key` substring
   match is demoted to **fast-path method 1**. Three further methods are
   added, of **unequal evidential strength**: (2) normalized effect/display-
   text matching (**880 candidate text matches** — association-level, **not
   yet semantically validated**), (3) replica → base-unique resolution,
   (4) passive-grant resolution. **Methods 3–4 were not systematically
   applied or validated in this sweep.** Methods 1–3 typically resolve to a
   **Modifier**; method 4 resolves to a **Passive** (`UniqueItem →
   Passive`) when the mechanic is represented by a passive. The
   established-facts section and the UniqueItem section now state this
   explicitly; the supporting-data table records the method/evidence
   retention roles.
2. **Resolution status taxonomy formalized** at minimum: `resolved` /
   `partial_or_indirect` / `unresolved_by_current_resolver` /
   `no_source_text_for_current_method` / `genuinely_absent_confirmed`.
   An empty `resolved_targets` is explicitly NOT equivalent to "no
   structured mechanics"; "no match" and "no display text" are not proof of
   absence; `genuinely_absent_confirmed` requires evidence-backed absence
   (e.g. retired content), not merely a failed lookup.
3. **Resolution evidence is not a node.** The graph relationship stays
   `UniqueItem → Modifier → Stat` **or** `UniqueItem → Passive → Stat`;
   resolution method/confidence/evidence belong to provenance / lookup data
   / relationship-generation evidence (roles 3+4 in the retention model)
   and are added to the not-a-node mapping.
4. **Per-association provenance** now requires recording **which method**
   established each UniqueItem → resolved-target link, so a later consumer
   can weigh or re-run them.

**Effect on 4C:** UniqueItem extraction must not silently lose modifier or
passive associations when the vid heuristic fails; retained data must let
the resolver be re-run/improved; provenance must distinguish direct/naming
vs text-based vs replica/base vs passive-grant resolution; "no resolved
target" and "no source text for the current method" must remain
diagnostically distinct from "resolver failed" and from evidence-backed
absence; the raw snapshot stays authoritative and unmodified.

**Effect on 4D:** the final payload structure for UniqueItem resolution
evidence is not fixed here — the required information (per-association
`method`, `status`, matched text, candidate target keys; node-level
`resolution_status`; resolved targets may be Modifier or Passive) is
specified, but the exact JSON representation is left to 4D.

No nodes or edges were created; no Phase 5 mechanical/conversion analysis
was performed; the newly discovered resolution methods are **not** treated
as semantically equivalent; unmatched uniques are not discarded; Modifier
nodes are not replaced by ModifierGroup nodes; no new node type was
introduced for resolution evidence; the `node_id | type | origin | payload`
schema is unchanged.
