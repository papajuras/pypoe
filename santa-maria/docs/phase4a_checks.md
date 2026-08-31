# Phase 4A — Targeted Checks (validation of profiling hypotheses)

Source: `cache/raw_records.db` only. No network, no writes to Phase 1-3 outputs, no taxonomy decisions (that is 4B).

## Check 1 — Unique item stat reconstruction via `visual_identity.id` crossref

Hypothesis: `uniques.json` holds name/art only; `visual_identity.id` cross-references `mods.json` records (the ~9,992 `Unique`-marked records) where the actual stat lines live.

### Crown of Eyes — full raw `uniques.json` record (record_key `168`)
```json
{
 "id": "Crown of Eyes",
 "inventory_height": 2,
 "inventory_width": 2,
 "is_alternate_art": false,
 "item_class": "Helmet",
 "name": "Crown of Eyes",
 "visual_identity": {
  "dds_file": "Art/2DItems/Armours/Helmets/CrownofEyes.dds",
  "id": "UniqueHelmetInt7"
 },
 "renamed_version": null,
 "base_version": null
}
```

`visual_identity.id = UniqueHelmetInt7` → `mods.json` records whose key contains that id:
resolved records: **11**
```json
// DivergentSpellDamageModifiersApplyToAttackDamageUniqueHelmetInt7 (generation_type: unique)
{
 "adds_tags": [],
 "domain": "item",
 "generation_type": "unique",
 "generation_weights": [],
 "grants_effects": [],
 "groups": [
  "SpellDamageModifiersApplyToAttackDamage"
 ],
 "implicit_tags": [
  "divergentunique",
  "damage",
  "attack"
 ],
 "is_essence_only": false,
 "name": "",
 "required_level": 69,
 "spawn_weights": [],
 "stats": [
  {
   "id": "additive_spell_damage_modifiers_apply_to_attack_damage",
   "max": 1,
   "min": 1
  }
 ],
 "text": "Attacks have 100% Arcane Might",
 "type": "SpellDamageModifiersApplyToAttackDamage",
 "gold_value": null
}
```
```json
// FireResistUniqueHelmetInt7 (generation_type: unique)
{
 "adds_tags": [],
 "domain": "item",
 "generation_type": "unique",
 "generation_weights": [],
 "grants_effects": [],
 "groups": [
  "FireResistance"
 ],
 "implicit_tags": [
  "elemental",
  "fire",
  "resistance"
 ],
 "is_essence_only": false,
 "name": "",
 "required_level": 1,
 "spawn_weights": [],
 "stats": [
  {
   "id": "base_fire_damage_resistance_%",
   "max": -30,
   "min": -30
  }
 ],
 "text": "-30% to Fire Resistance",
 "type": "FireResistance",
 "gold_value": null
}
```
```json
// IncreasedAccuracyUniqueHelmetInt7 (generation_type: unique)
{
 "adds_tags": [
  "has_attack_mod"
 ],
 "domain": "item",
 "generation_type": "unique",
 "generation_weights": [],
 "grants_effects": [],
 "groups": [
  "IncreasedAccuracy"
 ],
 "implicit_tags": [
  "attack"
 ],
 "is_essence_only": false,
 "name": "",
 "required_level": 1,
 "spawn_weights": [],
 "stats": [
  {
   "id": "accuracy_rating",
   "max": 350,
   "min": 300
  }
 ],
 "text": "+(300-350) to Accuracy Rating",
 "type": "IncreasedAccuracy",
 "gold_value": null
}
```
```json
// IncreasedAccuracyUniqueHelmetInt7Royale (generation_type: unique)
{
 "adds_tags": [
  "has_attack_mod"
 ],
 "domain": "item",
 "generation_type": "unique",
 "generation_weights": [],
 "grants_effects": [],
 "groups": [
  "IncreasedAccuracy"
 ],
 "implicit_tags": [
  "attack"
 ],
 "is_essence_only": false,
 "name": "",
 "required_level": 1,
 "spawn_weights": [],
 "stats": [
  {
   "id": "accuracy_rating",
   "max": 35,
   "min": 30
  }
 ],
 "text": "+(30-35) to Accuracy Rating",
 "type": "IncreasedAccuracy",
 "gold_value": null
}
```
```json
// LifeLeechPermyriadUniqueHelmetInt7 (generation_type: unique)
{
 "adds_tags": [],
 "domain": "item",
 "generation_type": "unique",
 "generation_weights": [],
 "grants_effects": [],
 "groups": [
  "LifeLeech"
 ],
 "implicit_tags": [
  "resource",
  "life",
  "attack"
 ],
 "is_essence_only": false,
 "name": "",
 "required_level": 1,
 "spawn_weights": [],
 "stats": [
  {
   "id": "base_life_leech_from_attack_damage_permyriad",
   "max": 80,
   "min": 40
  }
 ],
 "text": "(0.4-0.8)% of Attack Damage Leeched as Life",
 "type": "LifeLeechFromAttacksPermyriad",
 "gold_value": null
}
```
```json
// LifeLeechUniqueHelmetInt7 (generation_type: unique)
{
 "adds_tags": [
  "has_attack_mod"
 ],
 "domain": "item",
 "generation_type": "unique",
 "generation_weights": [],
 "grants_effects": [],
 "groups": [
  "LifeLeech"
 ],
 "implicit_tags": [
  "resource",
  "life",
  "physical",
  "attack"
 ],
 "is_essence_only": false,
 "name": "",
 "required_level": 1,
 "spawn_weights": [],
 "stats": [
  {
   "id": "old_do_not_use_life_leech_from_physical_damage_%",
   "max": 4,
   "min": 2
  }
 ],
 "text": "(0.4-0.8)% of Physical Attack Damage Leeched as Life",
 "type": "LifeLeech",
 "gold_value": null
}
```
```json
// LocalIncreasedEnergyShieldUniqueHelmetInt7 (generation_type: unique)
{
 "adds_tags": [],
 "domain": "item",
 "generation_type": "unique",
 "generation_weights": [],
 "grants_effects": [],
 "groups": [
  "DefencesPercent"
 ],
 "implicit_tags": [
  "defences",
  "energy_shield"
 ],
 "is_essence_only": false,
 "name": "",
 "required_level": 1,
 "spawn_weights": [],
 "stats": [
  {
   "id": "local_energy_shield_+%",
   "max": 150,
   "min": 120
  }
 ],
 "text": "(120-150)% increased Energy Shield",
 "type": "LocalEnergyShieldPercent",
 "gold_value": null
}
```
```json
// ManaLeechPermyriadUniqueHelmetInt7 (generation_type: unique)
{
 "adds_tags": [],
 "domain": "item",
 "generation_type": "unique",
 "generation_weights": [],
 "grants_effects": [],
 "groups": [
  "ManaLeech"
 ],
 "implicit_tags": [
  "resource",
  "mana",
  "attack"
 ],
 "is_essence_only": false,
 "name": "",
 "required_level": 1,
 "spawn_weights": [],
 "stats": [
  {
   "id": "base_mana_leech_from_attack_damage_permyriad",
   "max": 40,
   "min": 20
  }
 ],
 "text": "(0.2-0.4)% of Attack Damage Leeched as Mana",
 "type": "AttackDamageManaLeech",
 "gold_value": null
}
```
```json
// ManaLeechUniqueHelmetInt7 (generation_type: unique)
{
 "adds_tags": [
  "has_attack_mod"
 ],
 "domain": "item",
 "generation_type": "unique",
 "generation_weights": [],
 "grants_effects": [],
 "groups": [
  "ManaLeech"
 ],
 "implicit_tags": [
  "resource",
  "mana",
  "physical",
  "attack"
 ],
 "is_essence_only": false,
 "name": "",
 "required_level": 1,
 "spawn_weights": [],
 "stats": [
  {
   "id": "old_do_not_use_mana_leech_from_physical_damage_%",
   "max": 2,
   "min": 1
  }
 ],
 "text": "(0.2-0.4)% of Physical Attack Damage Leeched as Mana",
 "type": "ManaLeech",
 "gold_value": null
}
```
```json
// NonCriticalDamageMultiplierUniqueHelmetInt7 (generation_type: unique)
{
 "adds_tags": [],
 "domain": "item",
 "generation_type": "unique",
 "generation_weights": [],
 "grants_effects": [],
 "groups": [
  "DummyStatDisplayNothing"
 ],
 "implicit_tags": [],
 "is_essence_only": false,
 "name": "",
 "required_level": 1,
 "spawn_weights": [],
 "stats": [
  {
   "id": "dummy_stat_display_nothing",
   "max": 0,
   "min": 0
  }
 ],
 "text": null,
 "type": "DummyStatDisplayNothing",
 "gold_value": null
}
```
```json
// SpellDamageModifiersApplyToAttackDamageUniqueHelmetInt7 (generation_type: unique)
{
 "adds_tags": [],
 "domain": "item",
 "generation_type": "unique",
 "generation_weights": [],
 "grants_effects": [],
 "groups": [
  "SpellDamageModifiersApplyToAttackDamage"
 ],
 "implicit_tags": [
  "damage",
  "attack"
 ],
 "is_essence_only": false,
 "name": "",
 "required_level": 1,
 "spawn_weights": [],
 "stats": [
  {
   "id": "additive_spell_damage_modifiers_apply_to_attack_damage_at_150%_value",
   "max": 1,
   "min": 1
  }
 ],
 "text": "Attacks have 150% Arcane Might",
 "type": "SpellDamageModifiersApplyToAttackDamage150Percent",
 "gold_value": null
}
```

**Stat data present?** Yes — every resolved record carries `stats[].id` + `min`/`max`. The `Attacks have 150% Arcane Might` effect is `SpellDamageModifiersApplyToAttackDamageUniqueHelmetInt7` → `additive_spell_damage_modifiers_apply_to_attack_damage_at_150%_value` (min 1, max 1).

**Resolution caveats (not papered over):** the substring match over-matches. The 11 records include - a **variant**: `IncreasedAccuracyUniqueHelmetInt7Royale` (Royale-only roll);
  - a **dummy**: `NonCriticalDamageMultiplierUniqueHelmetInt7` with `text: null` and `dummy_stat_display_nothing`;
  - **legacy duplicates**: `LifeLeechUniqueHelmetInt7` / `ManaLeechUniqueHelmetInt7` use `old_do_not_use_*` stats alongside the modern `permyriad` variants.
Reconstructing the current item requires filtering `generation_type == 'unique'` + non-null `text`, dropping `Royale` / `old_do_not_use_*` / dummy records.

### Generalization — three more uniques
#### Mageblood (uniques key 1320)
```json
{
 "id": "Mageblood",
 "inventory_height": 1,
 "inventory_width": 2,
 "is_alternate_art": false,
 "item_class": "Belt",
 "name": "Mageblood",
 "visual_identity": {
  "dds_file": "Art/2DItems/Belts/InjectorBelt.dds",
  "id": "UniqueBelt43"
 },
 "renamed_version": null,
 "base_version": null
}
```
resolved mods: **1** (all `generation_type: unique`, all with `stats[].id`+min/max):
- `MutatedUniqueBelt43MagicUtilityFlasksAlwaysApplyRightmost` — 'Rightmost (2-4) Magic Utility Flasks constantly apply their Flask Effects to you' — `num_magic_utility_flasks_always_apply_rightmost 2-4`

#### Headhunter (uniques key 202)
```json
{
 "id": "Headhunter",
 "inventory_height": 1,
 "inventory_width": 2,
 "is_alternate_art": false,
 "item_class": "Belt",
 "name": "Headhunter",
 "visual_identity": {
  "dds_file": "Art/2DItems/Belts/Headhunter.dds",
  "id": "UniqueBelt7"
 },
 "renamed_version": null,
 "base_version": null
}
```
resolved mods: **8** (all `generation_type: unique`, all with `stats[].id`+min/max):
- `DamageOnRareMonstersUniqueBelt7` — '(20-30)% increased Damage with Hits against Rare monsters' — `damage_+%_vs_rare_monsters 20-30`
- `DexterityUniqueBelt7` — '+(40-55) to Dexterity' — `additional_dexterity 40-55`
- `GainRareMonsterModsOnKillUniqueBelt7_` — 'When you Kill a Rare monster, you gain its Modifiers for 60 seconds' — `gain_rare_monster_mods_on_kill_ms 20000-20000`
- `IncreasedLifeUniqueBelt7` — '+(50-60) to maximum Life' — `base_maximum_life 50-60`
- `MutatedUniqueBelt7CullingStrike` — 'Culling Strike' — `kill_enemy_on_hit_if_under_10%_life 1-1`
- `MutatedUniqueBelt7GainSoulEaterStackOnHit` — 'Eat a Soul when you Hit a Rare or Unique Enemy, no more than once every 0.25 seconds' — `gain_soul_eater_stack_on_hit_vs_unique_cooldown_ms 250-250`
- `MutatedUniqueBelt7RareAndUniqueEnemiesHaveIcons` — 'Rare and Unique Enemies within 120 metres have Minimap Icons' — `warden_tracker 1-1`
- `StrengthUniqueBelt7` — '+(40-55) to Strength' — `additional_strength 40-55`

#### The Squire (uniques key 1323)
```json
{
 "id": "The Squire",
 "inventory_height": 4,
 "inventory_width": 2,
 "is_alternate_art": false,
 "item_class": "Shield",
 "name": "The Squire",
 "visual_identity": {
  "dds_file": "Art/2DItems/Armours/Shields/CaspirosResonance.dds",
  "id": "UniqueShieldStrDex7_"
 },
 "renamed_version": null,
 "base_version": null
}
```
resolved mods: **3** (all `generation_type: unique`, all with `stats[].id`+min/max):
- `AllSocketsAreWhiteUniqueShieldStrDex7_` — 'All Sockets are White' — `local_all_sockets_are_white 1-1`
- `MutatedUniqueShieldStrDex7LocalGemsSocketedHaveNoAttributeRequirements` — 'Ignore Attribute Requirements of Socketed Gems' — `local_gems_socketed_have_no_attribute_requirements 1-1`
- `MutatedUniqueShieldStrDex7LocalIncreaseSocketedGemLevel` — '+1 to Level of Socketed Gems' — `local_socketed_gem_level_+ 1-1`

**Generalization verdict:** the pattern holds for Crown of Eyes + 3/3 samples. It is a **naming heuristic, not a foreign key**: Phase 1 shows only **589/1556** uniques have any matching mod key, and substring matches can over-match (variants/dummies/legacy). Reliable when it resolves, but per-item reconstruction needs the filtering above and ~62% of uniques have no match at all.

**Check 1 verdict: CONFIRMED** — the `visual_identity.id` → `mods.json` crossref resolves to stat-bearing records for Crown of Eyes and 3/3 additional samples; caveat: heuristic with over/under-match, filtered reconstruction required.

## Check 2 — `gems.json` `stat_conversions` as a Tier-3 signal

Hypothesis: `stat_conversions` may directly encode conversion-type relationships (Iron-Will-style `X becomes Y`) more cleanly than name pattern-matching.

**Count:** 701 of 1458 gems have a non-empty `stat_conversions`; total source→target pairs 2782.

**Full field structure — 6 representative examples (verbatim):**
#### Absolution
```json
{
 "absolution_duration_+%": "base_minion_duration_+%",
 "absolution_cast_speed_+%": "base_cast_speed_+%",
 "absolution_minion_area_of_effect_+%": "minion_area_of_effect_+%",
 "dominating_blow_and_absolution_additive_minion_damage_modifiers_apply_to_you_at_150%_value": "additive_minion_damage_modifiers_apply_to_you_at_150%_value"
}
```
#### AbsolutionAltX
```json
{
 "absolution_duration_+%": "base_minion_duration_+%",
 "absolution_cast_speed_+%": "base_cast_speed_+%",
 "absolution_minion_area_of_effect_+%": "minion_area_of_effect_+%",
 "dominating_blow_and_absolution_additive_minion_damage_modifiers_apply_to_you_at_150%_value": "additive_minion_damage_modifiers_apply_to_you_at_150%_value"
}
```
#### AlchemistsMark
```json
{
 "alchemists_mark_curse_effect_+%": "curse_effect_+%"
}
```
#### Ambush
```json
{
 "ambush_cooldown_speed_+%": "base_cooldown_speed_+%",
 "ambush_buff_critical_strike_multiplier_+": "vanishing_ambush_critical_strike_multiplier_+"
}
```
#### AncestorTotemSlash
```json
{
 "slash_ancestor_totem_damage_+%": "damage_+%",
 "slash_ancestor_totem_radius_+%": "base_skill_area_of_effect_+%",
 "slash_ancestor_totem_elemental_resistance_%": "totem_elemental_resistance_%"
}
```
#### AncestralCry
```json
{
 "warcry_skills_cooldown_is_4_seconds": "skill_cooldown_is_4_seconds",
 "warcry_buff_effect_+%": "skill_buff_effect_+%",
 "ancestral_cry_minimum_power": "minimum_power_from_skill_specific_stat",
 "ancestral_cry_exerted_attack_damage_+%": "warcry_grant_damage_+%_to_exerted_attacks",
 "ancestral_cry_attacks_exerted_+": "skill_empowers_next_x_melee_attacks"
}
```

**Explicit source→target?** Yes — it is `{source_stat_id: target_stat_id}`; both sides are stat-id strings (2777/2782 values match the stat-id pattern). It names a source stat and a target stat explicitly (a clean stat-to-stat link).

**Completeness/magnitude?** No. Values are bare stat-id strings — there is no fraction/magnitude/full-vs-partial notion. This is a **rename/alias map** (gem-specific stat name → canonical registry id), not a percentage conversion. The Iron-Will-style `becomes at 150%` mechanic lives elsewhere: `mods.json` stat ids with the `_at_150%_value` suffix (e.g. `additive_spell_damage_modifiers_apply_to_attack_damage_at_150%_value`) plus `stat_value_handlers.json`; **0** gems mention that stat.

**Only on gems?** In the raw data, `stat_conversions` occurs only in `repoe/gems.json`, `repoe/gems_minimal.json` (and their `data-formats` schemas); **0** records outside those contain it. No equivalent field exists on passives/uniques/mods. **Open question (not answered here):** whether the same alias/rename semantics exist implicitly in non-gem sources (e.g. PoB `SkillStatMap.json`, mod `type` naming) — that requires 4B work, not guessed here.

**Check 2 verdict: PARTIALLY CONFIRMED** — `stat_conversions` explicitly links source→target stat ids (cleaner than name pattern-matching; useful as an alias/hub signal), but it is alias-mapping only: no magnitude/completeness, and it does not carry the Iron-Will-style conversion mechanics.
