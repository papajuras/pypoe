# Build 01 — Iron Whisper Strength-Stacker

**Status: VALIDATED** (passed `phase7_build_validity` checks — slots, availability, ascendancy composition; NOT a full PoE build-validity claim)

Central interaction: strength is the single axis feeding attack damage through two independent paths — Shaper's Touch converts strength into mana, and Whispers of Infinity converts every 100 mana into added chaos damage on attacks — while The Iron Fortress converts the strength damage bonus into melee physical damage instead.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | **Whispers of Infinity** [available] | carries: **`AttacksGainMinMaxAddedChaosDamageBasedOnManaUnique__1`** → `stat:max_attack_added_chaos_damage_per_100_mana` + `stat:min_attack_added_chaos_damage_per_100_mana` · `PercentReducedMaximumManaUnique_1` → `stat:maximum_mana_+%` (group: `MaximumManaIncreasePercent`; sign not exposed by API) · `SkillsCostEnergyShieldInsteadOfManaLifeUnique__1` → `stat:base_skills_cost_es_instead_of_mana_life` · `ReducedEnergyShieldDelayImplicit1_` → `stat:energy_shield_delay_-%` |
| Gloves | Shaper's Touch [available] | carries: **`ManaPerStrengthUnique__1__`** → `stat:X_mana_per_4_strength` · `AccuracyPerIntelligenceUnique__1` · `DivergentEnergyShieldPerStrengthUnique__1` · `DivergentEvasionRatingPerIntelligenceUnique__1` · `DivergentMeleePhysicalDamagePerDexterityUnique__1_` · `LifePerDexterityUnique__1` |
| Body Armour | The Iron Fortress [available] | carries: **`StrengthDamageBonus3Per10Unique__1`** → `stat:strength_damage_bonus_grants_melee_physical_damage_+3%_per_10_strength_instead` · `DivergentBlockChancePer50StrengthUnique__1` · `ExtraRollsSpellBlockUnique__1` · `MutatedUniqueBodyStr9AttackBlockLuck` · `MutatedUniqueBodyStr9SpellBlockPer50Strength` · `StrengthUnique__13_` |
| Passive | Mental Conditioning (AscendancyCustomBerserker11, Berserker — Phrecia alternate) | grants: `stat:X_mana_per_4_strength` |
| Passive | Strength and Armour (AscendancyCustomBerserker1, Berserker small) | strength + armour small node |

**Ascendancy:** Berserker (Phrecia alternate namespace `AscendancyCustomBerserker*`)

Note: the Research API exposes modifier/stat identifiers, not display text; lists above are exact API ids, unmodified.

## Why it works

All skill costs are paid from energy shield (WoI), so the mana pool is never taxed and can be stacked as a pure damage stat. Strength drives the pool two ways (Shaper's Touch gloves + Mental Conditioning ascendancy both grant mana per strength), and every 100 mana becomes added chaos on every attack. The same strength investment simultaneously raises melee physical damage through the Iron Fortress conversion and block through per-strength block stats — one stat, two damage paths plus defence.

## Scaling claim

**Compound (multi-path into one output), not confirmed quadratic.** X = strength → path A: mana pool → WoI added-chaos on attacks; path B: melee physical damage % (Iron Fortress `StrengthDamageBonus3Per10Unique__1`). The KB evidences both converters; whether the added-chaos and melee-phys terms interact multiplicatively is not modelled in the KB, so X² is a hypothesis, not a claim.

## Evidence

- `mod:ManaPerStrengthUnique__1__` → `stat:X_mana_per_4_strength` (uma carrier: Shaper's Touch)
- `passive:AscendancyCustomBerserker11` → same stat (second generator — redundancy by design)
- `unique:1461` → `stat:max/min_attack_added_chaos_damage_per_100_mana`
- `mod:StrengthDamageBonus3Per10Unique__1` (uma carrier: The Iron Fortress) → `stat:strength_damage_bonus_grants_melee_physical_damage_+3%_per_10_strength_instead`

## Validation

5/5 additions valid; final `validate_build` (final=True): **valid** — availability all available, class_mix `['Berserker']`.

## Alternate generator (not duplicated as a separate build)

`passive:AscendancyCustomDeadeye14` ("an infinite pursuit", Phrecia Deadeye) grants `stat:X_mana_per_dexterity` — a dexterity-stacked variant of this same skeleton; recorded to avoid artificial duplication.
