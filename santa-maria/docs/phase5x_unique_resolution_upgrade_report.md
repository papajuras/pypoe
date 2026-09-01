# Phase 5.x — Unique → Modifier Resolution Upgrade Report

Contract amendment v5.4 -> v5.5 (`docs/phase5_edge_contract.json`), resolver upgrade
(`tools/extract_nodes.py`), extractor upgrade (`tools/phase5_extract_edges.py`),
regeneration of `nodes.db` and `edges.db`.

## A. Baseline (frozen, pre-change)

- `nodes.db`: canonical_hash `429702b660da…`, 83,534 nodes
- `edges.db`: canonical_hash `db07c78acb51…`, 263,387 edges
- Unique nodes: **1,556** · confirmed `unique_modifier_association`: **3,794**
  (method 1: 3,542 · method 3: 242 · method 4: 10)
- Unique nodes ≥1 confirmed: **635** · 0 confirmed: **921**
- Resolver method-sets: `(1,2):547` `(2,):833` `():88` `(2,4):7` `(1,):31` `(2,3):47` `(3,):2` `(1,2,3):1`

## B. Contract amendment (v5.5)

- `unique_modifier_association` eligibility extended to methods `{1,4,5,6}`.
- **Method 1**: digit-boundary rule (a vid must not match a longer numeric-prefix
  identifier: `UniqueTwoHandAxe1` no longer matches `UniqueTwoHandAxe10/11/12`).
- **Method 3 (replica → base inheritance): REJECTED** (moved to rejected_deferred_classes).
- **Method 5 (PoB-compatible template matching)**: exact-singleton + approved pool
  + item-class + non-Replica -> resolved; everything else candidate-only.
- **Method 6 (Vestigial ownership)**: structured mod-key -> unique-name; confirmed
  only when the mod key exists and the unique name resolves to exactly one node.
- Approved pool = `mods.json` record with `generation_type == 'unique'`; excluded
  pools (Eldritch/Veiled/Influence-rare/Synthesis-named/corruption/special) may be
  candidates but never edges.
- Replica policy: method-5 matches are candidate-only for Replicas; method-6
  Vestigial still provides structured confirmed edges.
- Step-0 R3 note updated (see N).

## C. Implementation changes

- `tools/extract_nodes.py`: `_pob_mod_classes` class-token extraction (Unique/Implicit
  prefix, substring-collision safe — `Shield` inside `EnergyShield` no longer matches);
  new loaders `load_pob_templates`, `load_base2class`, `load_vestigial`;
  `parse_unique_block`; `resolve_unique_all` rewritten (method-1 digit boundary,
  method-3 removed, methods 5/6 added, status aggregation updated).
- `tools/phase5_extract_edges.py`: eligibility `{1,3,4}` -> `{1,4,5,6}`; method-specific
  provenance (PoB block line for 5, Vestigial record for 6); new adversarial checks
  `no_method3_edges`, `no_method5_replica_edges`, `no_method1_prefix_collision`.

## D. New resolution algorithm (method 5)

```
Unique PoB block -> current-variant resolution -> header/base-line removal
  -> {tags:}/{variant:} strip -> exact template lookup ("1".."7", approved pools)
  -> item-class constraint (base-type line -> repoe/base_items.json)
  -> approved-pool filter (generation_type == 'unique')
  -> exact singleton + non-Replica  => resolved
     (normalized / collisions / replica / excluded-pool) => candidate
```

## E. Before/after coverage

| metric | before | after |
|---|---|---|
| Unique nodes | 1,556 | 1,556 |
| confirmed uma edges | 3,794 | **6,264** |
| uniques ≥1 confirmed | 635 | **1,381** |
| uniques 0 confirmed | 921 | **175** |
| nodes.db canonical_hash | `429702b6…` | `c7175e76…` |
| edges.db canonical_hash | `db07c78a…` | `2308a2ab…` |
| total edges | 263,387 | 265,857 |

Confirmed uma edges by method-set (merged provenance): `{1}:1,701` `{1,5}:972`
`{5}:3,156` `{1,6}:71` `{6}:354` `{4,5}:7` `{4}:3`. Edges with method 1: 2,744 ·
method 5: 4,135 · method 6: 425.

## F. Added confirmed edges

- **3,509 added** (2,755 unchanged + 1,039 removed = 3,794 baseline).
- Added method-sets: `{5}`: 3,156 · `{6}`: 353 (all other new associations merge
  into previously-existing method-1/4 edges as added provenance).

## G. Removed / corrected edges

- **1,039 removed**, all explainable:
  - **798 method-1** — every one independently verified as a prefix-collision
    (`UniqueTwoHandAxe1` -> `…UniqueTwoHandAxe10/11/12…`).
  - **241 method-3** — replica→base inheritance (50 from `Replica `-named sources;
    the rest from vid-suffix-replica records), now rejected.

## H. Method-1 correction

Digit-boundary enforced in the resolver; adversarial `no_method1_prefix_collision`
= 0. The 798 false associations are gone.

## I. Replica correction

Method-3 inheritance removed. Replica Abyssus now has exactly 1 confirmed edge via
method 6 (Vestigial), and its method-5 matches are candidates only
(`no_method5_replica_edges` = 0).

## J. Vestigial handling

Method 6 consumed `pob/Vestigial.json`; 425 edges (353 pure-new, 71 merged with
method 1). Duplicated unique names -> candidate (never first-match); e.g. unique:136
Abyssus and unique:1145 Replica Abyssus each get their own Vestigial Divergent edge.

## K. Whispers verification

`unique:1461` now has 4 confirmed method-5 edges:
`AttacksGainMinMaxAddedChaosDamageBasedOnManaUnique__1`,
`PercentReducedMaximumManaUnique_1`, `ReducedEnergyShieldDelayImplicit1_`,
`SkillsCostEnergyShieldInsteadOfManaLifeUnique__1`. The ES line
(`+(50-100) to maximum Energy Shield`) correctly yields the two identical-stat
duplicate candidates and NO edge (no arbitrary selection).

## L. Ambiguity policy

- Duplicate-equivalent / genuine collisions: candidate-only (never iteration-order).
- Normalized-only singletons: candidate-only (amendment scope).
- Excluded-pool matches: candidate-only.
- Replica method-5 matches: candidate-only.
- Vestigial ambiguous names: candidate-only.

## M. Adversarial validation

All PASS, including new checks: `no_method3_edges`=0, `no_method5_replica_edges`=0,
`no_method1_prefix_collision`=0, `zero_method2_edges`=0, plus the full existing suite
(no reverse duplicates, no orphans, no invalid src/tgt, valid provenance, no
cross-namespace, no display-text, no invented operands).

## N. Step 0 / Step 3 regression

| case | expected | actual | classification |
|---|---|---|---|
| T_exemplars, T4, T1, T2, T_ut_types, T_int_grant_stat, T_int_lightning_mods, T_mana_lightning_anchor, R1 | pass | pass | preserved |
| R2 (endurance charge) | fail | fail | preserved (data absence) |
| R3 (Hopeshredder) | fail | fail (frozen test asserts `method in {1,3,4}`; item now has 7 method-5 confirmed edges) | **EXPECTED IMPROVEMENT** beyond the frozen assertion (test not modified) |
| R_adv hop1 (`unique:1461 -> stat:intelligence`) | fail | fail (none of Whispers' 4 confirmed mods grants intelligence) | **PRESERVED FAILURE** |
| R_adv hop2/hop3 | preserved | preserved | preserved |

Step 0 regression table: **100% MATCH**.

## O. Determinism

- `nodes.db`: two runs -> identical canonical hash `c7175e76…` and byte-identical
  content.
- `edges.db`: two runs -> identical canonical hash `2308a2ab…` and byte-identical
  content (all rows + meta). No filesystem/hash/iteration-order dependence.

## P. Remaining unresolved population

- 175 unique nodes with 0 confirmed edges (down from 921).
- 795 of the former 921 gained ≥1 method-5 singleton candidate; 96 (88 empty-resolution
  + 8 fully-unmatched blocks) still have no usable candidate.
- Replicas remain candidate-only for method 5 by policy; method-6 covers their
  Vestigial Divergent ownership.

## Q. Unexpected findings

- The class-token matcher initially used raw substring matching and incorrectly
  detected `Shield` inside `EnergyShield`; fixed to extract the class only after
  `Unique`/`Implicit` (verified: 0 Whispers regressions after fix).
- Total edges grew from 263,387 to 265,857 (net +2,470) — all from the 
  unique_modifier_association class; every other class is byte-identical.

## R. Final verdict

The upgrade is deterministic, fully explainable, and contract-compliant:
- 1,039 incorrect associations removed (798 prefix-collisions + 241 replica-base),
  each verified.
- 3,509 new associations from approved deterministic sources (PoB templates +
  Vestigial), all provenance-backed, none from fuzzy/heuristic/pool-excluded/replica
  text matching.
- Structural, adversarial, Step-0 regression (100% MATCH) and determinism all pass.
- Every removed edge has an explainable reason; no regression outside the intended
  Unique-resolution scope.

**Stop condition met** — no Phase 6, no Graph API.
