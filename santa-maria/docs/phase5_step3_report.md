# Phase 5 Step 3 — Relationship Graph: TDD + Adversarial Discovery Validation

Frozen inputs: `tools/extract_edges.py`, `cache/edges.db` (263,387 edges, 9 classes),
`cache/nodes.db`, `docs/phase5_edge_contract.json` v5.4, `docs/phase5_step2_report.md`.

This step validated what the populated graph can actually discover, against the
frozen `step0_coverage` baseline. All traversals were run against `edges.db`
(read-only); no edges were added and nothing was redesigned.

## A. Step 0 baseline conformance

| case | expected | actual | MATCH | explanation |
|---|---|---|---|---|
| T_exemplars | pass | pass | MATCH | all exemplar nodes exist |
| T4_unique_rare_shared_stat | pass | pass | MATCH | concrete path `unique:183 → mod:IncreasedAccuracyUniqueAmulet17_ → stat:accuracy_rating → mod:AbyssAccuracyRatingJewel1` |
| T1_firemin_firemax_shared | pass | pass | MATCH | both fire stats granted by `mod:AddedFireDamagePerStrengthInfluence1` |
| T2_per_charge_mods | pass | pass | MATCH | both endurance-charge fire stats granted by 3 mods |
| T_ut_types | pass | pass | MATCH | `gem:SupportUnholyTrinity → tag:lightning/physical/chaos` |
| T_int_grant_stat | pass | pass | MATCH | unique + Necropolis prefix both grant the stat |
| T_int_lightning_mods | pass | pass | MATCH | recombinator mod grants both per-10-int lightning stats |
| T_mana_lightning_anchor | pass | pass | MATCH | unique mod ↔ mana→lightning stat |
| R1_strength_to_fire | pass | pass | MATCH | `stat:strength → stat:attack_min/max_added_fire_damage_per_10_strength` (45 strength-scaled edges total) |
| R2_endurance_charge_to_fire | fail | fail | MATCH | damage side representable; head absent |
| R3_hopeshredder_scaling | fail | fail | MATCH | unique:739 method-2-only, 0 uma edges |
| R_adv_whispers_chain | partial | partial | MATCH | hop1/3 fail, hop2 passes, gem side traversable |

## B. Actual graph paths

- **Strength:** `stat:strength --stat_scales_with--> stat:attack_minimum_added_fire_damage_per_10_strength` → (reverse) `<-modifier_grants_stat- mod:AddedFireDamagePerStrengthInfluence1` (9 mods incl. unique/Synthesis/TwoHand variants). **PASS.**
- **Endurance Charge:** no `stat:endurance_charge` node; `stat_scales_with` from it = 0. Damage side only: `stat:minimum/maximum_added_fire_damage_per_endurance_charge ↔ mod:AddedFireDamagePerEnduranceChargeInfluence1` (+Influence2, ChargeBonus). **FAIL (baseline).**
- **Hopeshredder:** `unique:739` methods={2}, resolution `partial_or_indirect`, 0 uma edges. **FAIL (baseline).**
- **T4 Unique↔rare (concrete, no shortcut):** `unique:183 --unique_modifier_association(method 1, resolved_not_validated)--> mod:IncreasedAccuracyUniqueAmulet17_ --modifier_grants_stat--> stat:accuracy_rating <--modifier_grants_stat-- mod:AbyssAccuracyRatingJewel1 (suffix)`. **PASS.**
- **Whispers chain:**
  1. `unique:1461 → stat:intelligence` — **FAIL** (0 uma edges; method-2 only) — validation gap.
  2. `stat:intelligence → stat:minimum_added_lightning_damage_to_attacks_per_10_intelligence` — **PASS** via `stat_scales_with` (5 lightning-per-int targets).
  3. per-10-int lightning `↔` plain lightning — **FAIL** (0 edges either direction) — data absence.
  4. Gem side: `gem:SupportUnholyTrinity --gem_has_tag--> tag:chaos/tag:lightning/tag:physical/tag:support`. **PASS.**
- **Unholy Trinity → Lightning/Physical/Chaos:** reachable via 3 confirmed `gem_has_tag` edges; all 3 Tag nodes exist. **PASS.**

## C. Mismatches / missing bridges

None beyond the frozen baseline. Classification of the known failures:

- **R2/T2 head** → **A. Data absence** (`endurance_charge` has no Stat node) + contract limitation (resource-relative forms out of scope).
- **R3/T3** → **B. Contract limitation / validation gap** (only method-2 candidates; contract requires method 1/3/4 + resolved).
- **Whispers hop 1** → **B.** (same validation gap).
- **Whispers hop 3** → **A. Data absence** (no structural link exists between the scaling stat and plain lightning; the "0 of 40,354" audit holds — 0 edges verified in both directions).

No unanticipated pass/fail, no implementation defects, no test/traversal-interpretation
errors. No new bridge is warranted: every known missing relation is a genuine
data/validation boundary, and any candidate bridge (e.g. scaling→plain lightning)
would require semantic inference — reported as boundary, **not** implemented.

## D. Diagnostic verification (independent)

- **Gem tags:** distinct **53** · with Tag node **13** · genuinely gem-only **40** — confirms
  the Step 2 documentation-only label (53 was all distinct tags). `gem_has_tag`
  extraction unaffected (1,719 edges use the correct `f'tag:' in tag-node-set` check).
- **Numeric `_per_<N>_` operands:** total **350** · resolvable/emitted **122** · genuinely
  unresolved **228**; edges.db `stat_scales_with` = 122, **exact set equality** with the
  independently re-derived resolvable set. Confirms the 350 label was the total, not the
  unresolved count.

## E. Architectural verdict

**YES — the frozen Step 2 graph is sufficient as the factual relationship layer.**
The TDD/adversarial traversals realize the Step 0 baseline 12/12 (incl. preserved
failures), all discovered paths are composed of approved, provenance-backed edges,
no inference was required, and the graph stops exactly at the architectural boundary:
it holds facts and deterministic structural relationships; interpretation (Whispers
variance hypothesis, build reasoning, scoring) remains downstream.

## Stop condition

Met. No relationships added, nothing redesigned, no Graph API built. The two Step 2
documentation-only diagnostic labels (gem-only tags 53→40; unresolved operands
350→228) remain open documentation notes; the diagnostic code was not modified in
this step.
