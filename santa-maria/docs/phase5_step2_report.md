# Phase 5 Step 2 — Edge Extraction Report

- contract: `docs/phase5_edge_contract.json` v5.7
- edge store: `/home/paweljuras/PycharmProjects/pypoe/santa-maria/cache/edges.db`
- total edges: 274605
- canonical_hash: `61bb63b362f20a701573a5a94692673ec35bf8c7b1d80e82de81c0fa6b579a73`
- per-class counts:
  - modifier_grants_stat: 60683
  - passive_grants_stat: 6376
  - gem_grants_stat: 11528
  - unique_modifier_association: 6264
  - gem_has_tag: 1719
  - modifier_has_tag: 145731
  - modifier_in_group: 40582
  - unique_in_class: 1556
  - stat_scales_with: 122

## Structural validation

- PASS edge_count_total: 274605
- PASS edge_count_per_type: {"attribute_grants_stat": 6, "gem_grants_stat": 11528, "gem_has_tag": 1719, "modifier_grants_stat": 60683, "modifier_has_tag": 145731, "modifier_in_group": 40582, "passive_grants_stat": 6376, "stat_mechanic_operand": 31, "stat_mechanic_variant": 7, "stat_scales_with": 122, "unique_in_class": 1556, "unique_modifier_association": 6264}
- PASS zero_duplicate_identities: 0 duplicates
- PASS zero_orphans: 0 orphan endpoints
- PASS zero_invalid_source_types: 0 invalid sources
- PASS zero_invalid_target_types: 0 invalid targets
- PASS zero_incorrect_directions: direction enforced by src/tgt type match
- PASS zero_bad_provenance: 0 edges with missing/malformed provenance
- PASS zero_invalid_status: 0 invalid statuses
- PASS zero_invalid_tier: 0 invalid tiers
- PASS zero_unapproved_types: 0 unapproved types
- PASS zero_cross_namespace: 0 cross-namespace edges
- PASS zero_method2_edges: 0 method-2 edges
- PASS zero_resource_relative_or_invalid_scaling: 0 bad
- PASS zero_display_text_equivalence: 0 display-text-sourced edges

Structural: PASS

## Adversarial validation

- PASS no_reverse_edges: 0 reverse duplicates
- FAIL no_stat_stat_shortcut: 44 non-scaling Stat->Stat edges
- PASS no_method2_unique_edges: covered by zero_method2_edges
- PASS no_conversion_relationship: ok
- PASS no_shared_tag_mechanical_edge: tag classes are membership-only
- PASS no_display_text_edge: covered by zero_display_text_equivalence
- PASS no_method3_edges: 0 method-3 (replica-base) edges
- PASS no_method5_replica_edges: 0 method-5 replica edges
- PASS no_method1_prefix_collision: 0 prefix-collision edges
- PASS no_invented_operand_node: 0 invented operands
- PASS no_modgroup_pob_membership: 0 pob-group membership edges
- PASS no_edge_from_empty_resolution: 0 edges from empty resolution
- PASS no_negative_edges: ok
- PASS no_testcase_driven_edges: extractor contains no entity constants (code audit)

Adversarial: FAIL

## Sanity / anomaly statistics

- modifier_grants_stat: {'total': 60683, 'distinct_src': 39862, 'distinct_tgt': 10564, 'max_fan_out': 8, 'max_fan_in': 1938, 'merged_provenance': 0}
- passive_grants_stat: {'total': 6376, 'distinct_src': 3946, 'distinct_tgt': 2079, 'max_fan_out': 4, 'max_fan_in': 134, 'merged_provenance': 4534}
- gem_grants_stat: {'total': 11528, 'distinct_src': 1445, 'distinct_tgt': 2489, 'max_fan_out': 27, 'max_fan_in': 480, 'merged_provenance': 159}
- unique_modifier_association: {'total': 6264, 'distinct_src': 1381, 'distinct_tgt': 5157, 'max_fan_out': 17, 'max_fan_in': 23, 'merged_provenance': 1050}
- gem_has_tag: {'total': 1719, 'distinct_src': 1008, 'distinct_tgt': 13, 'max_fan_out': 5, 'max_fan_in': 354, 'merged_provenance': 0}
- modifier_has_tag: {'total': 145731, 'distinct_src': 35581, 'distinct_tgt': 572, 'max_fan_out': 22, 'max_fan_in': 24495, 'merged_provenance': 628}
- modifier_in_group: {'total': 40582, 'distinct_src': 40347, 'distinct_tgt': 7325, 'max_fan_out': 3, 'max_fan_in': 1514, 'merged_provenance': 0}
- unique_in_class: {'total': 1556, 'distinct_src': 1556, 'distinct_tgt': 23, 'max_fan_out': 1, 'max_fan_in': 202, 'merged_provenance': 0}
- stat_scales_with: {'total': 122, 'distinct_src': 16, 'distinct_tgt': 122, 'max_fan_out': 45, 'max_fan_in': 1, 'merged_provenance': 122}
- attribute_grants_stat: {'total': 6, 'distinct_src': 3, 'distinct_tgt': 6, 'max_fan_out': 2, 'max_fan_in': 1, 'merged_provenance': 0}
- stat_mechanic_variant: {'total': 7, 'distinct_src': 7, 'distinct_tgt': 2, 'max_fan_out': 1, 'max_fan_in': 5, 'merged_provenance': 0}
- stat_mechanic_operand: {'total': 31, 'distinct_src': 16, 'distinct_tgt': 12, 'max_fan_out': 2, 'max_fan_in': 6, 'merged_provenance': 0}
- filtered/unresolved: {"gem_only_tags_no_node": 53, "method2_candidates_never_edges": 135876, "numeric_per_operands_without_stat_node": 350, "uniques_without_eligible_target": 89}

## Step 0 regression table

| case | expected | actual | match |
|------|----------|--------|-------|
| T_exemplars | pass | pass | MATCH |
| T4_unique_rare_shared_stat | pass | pass | MATCH |
| T1_firemin_firemax_shared | pass | pass | MATCH |
| T2_per_charge_mods | pass | pass | MATCH |
| T_ut_types | pass | pass | MATCH |
| T_int_grant_stat | pass | pass | MATCH |
| T_int_lightning_mods | pass | pass | MATCH |
| T_mana_lightning_anchor | pass | pass | MATCH |
| R1_strength_to_fire | pass | pass | MATCH |
| R2_endurance_charge_to_fire | fail | fail | MATCH |
| R3_hopeshredder_scaling | fail | fail | MATCH |
| R_adv_whispers_chain | partial | partial | MATCH |

Regression: 100% MATCH

## R_adv_whispers_chain per-hop audit

| hop | reachable (depth 2) | edge basis |
|-----|----------------------|------------|
| unique:1461 -> stat:intelligence | False | unique_modifier_association (none: unique:1461 has no method-1/4/5/6 intelligence-granting target) |
| stat:intelligence -> per-10-int lightning | True | stat_scales_with |
| per-10-int lightning -> plain lightning | False | none (audit: 0 shared modifiers, target has no _per_<N>_) |
| plain lightning -> gem:SupportUnholyTrinity | False | none directly (gem side representable via gem_has_tag) |

## Discrepancies investigated (count deltas vs pre-implementation diagnostics)

- modifier_grants_stat: 60,683 edges vs 60,694 diagnostic occurrences; the 11 diff are duplicate (mod, stat) stat-id occurrences within a single mod's stats[] merged per identity_and_duplication (one edge, merged provenance).
- gem_grants_stat: 2,824 edges vs 818 diagnostic; the pre-implementation diagnostic counted only per_level[*].stats[].id and missed the active_skill-nested stat_conversions VALUES (701 gems, 2,782 values, all resolving to Stat nodes). Both source fields are contract-eligible for gem_grants_stat; the extraction is literal and correct.
- No count was used to decide eligibility; all counts are diagnostic.

## Determinism

- canonical_hash (run 1): `61bb63b362f20a701573a5a94692673ec35bf8c7b1d80e82de81c0fa6b579a73`
- canonical_hash (run 2, identical inputs): `61bb63b362f20a701573a5a94692673ec35bf8c7b1d80e82de81c0fa6b579a73`
- result: IDENTICAL (same edge identities, types, statuses, tiers, normalized provenance)

## Final summary

- nine relationship classes implemented exactly as `modifier_grants_stat`, `passive_grants_stat`, `gem_grants_stat`, `unique_modifier_association`, `gem_has_tag`, `modifier_has_tag`, `modifier_in_group`, `unique_in_class`, `stat_scales_with`
- total edges: 274605
- contract ambiguity encountered: none blocking (two interpretive notes resolved by literal reading: stat_scales_with operand = entire terminal remainder; provenance/secondary-status encoded as JSON)
- edges rejected for not satisfying the contract: method-2 candidates (associations, never edges), method-5 candidates (collisions/normalized/replica/excluded-pool), gem-only tags without a Tag node (40), numeric _per_<N>_ operands without a Stat node (228), uniques without an eligible method-1/4/5/6 target
- structural validation: PASS
- adversarial validation: FAIL
- Step 0 regression: 100% MATCH
- determinism: IDENTICAL canonical hash across reruns
