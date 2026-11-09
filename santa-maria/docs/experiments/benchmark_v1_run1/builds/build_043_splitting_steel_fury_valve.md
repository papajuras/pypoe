# Build 043 — Splitting Steel Projectile-Conversion (Fury Valve)

**Status: VALIDATED** (passed all checks implemented by `phase7_build_validity` — slot occupancy, weapon configuration, gem supportability, ascendancy composition; NOT a full PoE build-validity claim)

Central interaction: Splitting Steel already converts projectile-count modifiers into extra split counts; the Fury Valve ascendancy node grants the same conversion stat, evidencing that the conversion is a shared, multi-source mechanic rather than a gem-internal quirk.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Weapon (slot filler — chosen only to give the gem group a resolvable weapon context; a rare one-hander may be preferable) | The Princess [available] | carries: `AccuracyPercentImplicitSword1` · `LocalAddedPhysicalDamageUniqueOneHandSword12` · `LocalIncreasedAttackSpeedUniqueOneHandSword12` · `LocalIncreasedPhysicalDamagePercentUniqueOneHandSword12` · `PhysicalAddedAsColdUniqueOneHandSword12` · `DamageTakenFromGhostsUniqueOneHandSword12` · `DamageTakenFromSkeletonsUniqueOneHandSword12_` |
| Gem group | **Splitting Steel** supported by **Greater Multiple Projectiles** | Splitting Steel grants: **`stat:modifiers_to_number_of_projectiles_instead_apply_to_splitting`** · `stat:projectile_number_to_split` · `stat:projectiles_can_split_at_end_of_range` · `stat:projectiles_can_split_from_terrain` · `stat:attacks_impale_on_hit_%_chance` · `stat:steel_skill_%_chance_to_not_consume_ammo` · `stat:base_is_projectile` · `stat:base_skill_area_of_effect_+%` · `stat:damage_+%` · `stat:skill_projectiles_cannot_return`; GMP grants: `stat:number_of_additional_projectiles` · `stat:support_multiple_projectile_damage_+%_final` |
| Passive | Fury Valve (AscendancyCustomAscendant48, Ascendant — Phrecia alternate namespace) | grants: `stat:modifiers_to_number_of_projectiles_instead_apply_to_splitting` |

**Ascendancy:** Ascendant (alternate-namespace node `AscendancyCustomAscendant48`)

Note: the Research API exposes modifier/stat identifiers, not display text; the lists above are the exact ids returned by the API, unmodified.

## Why it works

GMP's `number_of_additional_projectiles` would normally add projectiles; Splitting Steel's conversion stat reroutes that modifier into additional splits, multiplying the number of shards and therefore impale applications per attack. Fury Valve carries the identical conversion stat at the ascendancy layer — carrier evidence: 4 gems (SplittingSteel, SplittingSteelAltX, IceSpearAltX, SplitArrowAltX), 1 unique mod (`ProjectileModifiersApplyToSplitsUnique__1`), and this passive all grant the same stat.

## Scaling claim

**Converter / multi-use (no quadratic claim).** X = projectile-count modifiers → A: split count → hit count → total damage and impale applications. Both damage terms flow through the single hit-count intermediary; that is one path with two beneficiaries, not two independent X paths into one output.

## Evidence

- `gem:SplittingSteel` → `stat:modifiers_to_number_of_projectiles_instead_apply_to_splitting` (gem_grants_stat)
- `carriers(stat:modifiers_to_number_of_projectiles_instead_apply_to_splitting)` → 6 carriers across gem/modifier/passive edge types
- `passive:AscendancyCustomAscendant48` (Fury Valve) → same stat (passive_grants_stat)

## Validation

Fury Valve addition: valid. The Princess addition: valid (slot filler for weapon context — without a weapon the gem group resolves to UNKNOWN, see validation note). Final `validate_build` (final=True): **valid** — availability valid, class_mix `['Ascendant']`. Note: the first validation attempt with no weapon equipped returned UNKNOWN (`weapon_restriction unknown: weapon context not uniquely determined`) — recorded, not guessed.
