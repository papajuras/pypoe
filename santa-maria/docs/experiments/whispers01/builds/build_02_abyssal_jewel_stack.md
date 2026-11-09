# Build 02 — Lightless Abyssal-Jewel Mana Stack

**Status: VALIDATED** (passed `phase7_build_validity` checks — slots, availability, ascendancy composition; NOT a full PoE build-validity claim)

Central interaction: every abyssal jewel affecting the character raises maximum mana by a percentage (Lightless ascendancy notable) while Shroud of the Lightless pays out flat life, flat mana, and elemental penetration per jewel — and Whispers of Infinity turns the resulting mana pool into added chaos damage on attacks.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | **Whispers of Infinity** [available] | carries: **`AttacksGainMinMaxAddedChaosDamageBasedOnManaUnique__1`** → `stat:max_attack_added_chaos_damage_per_100_mana` + `stat:min_attack_added_chaos_damage_per_100_mana` · `PercentReducedMaximumManaUnique_1` → `stat:maximum_mana_+%` (group: `MaximumManaIncreasePercent`; sign not exposed by API) · `SkillsCostEnergyShieldInsteadOfManaLifeUnique__1` → `stat:base_skills_cost_es_instead_of_mana_life` · `ReducedEnergyShieldDelayImplicit1_` → `stat:energy_shield_delay_-%` |
| Body Armour | Shroud of the Lightless [available] | carries: **`IncreasedManaPerAbyssalJewelUnique__2`** → `stat:maximum_mana_+%_per_abyssal_jewel_affecting_you` · `IncreasedLifePerAbyssalJewelUnique__2` → life % per abyssal jewel · `ElementalPenetrationPerAbyssalJewelUnique__1` → `stat:penetrate_elemental_resistance_%_per_abyssal_jewel_affecting_you` · `LocalDisplayGrantLevelXShadeFormUnique__1` · `LocalIncreasedEvasionAndEnergyShieldUnique__11_` |
| Passive | Lightless (AscendancyCustomTrickster14, Trickster — Phrecia alternate) | grants: `stat:maximum_mana_+%_per_abyssal_jewel_affecting_you` · `stat:maximum_life_+%_per_abyssal_jewel_affecting_you` |

**Ascendancy:** Trickster (Phrecia alternate namespace `AscendancyCustomTrickster*`)

Jewel sockets are filled with `item_class:AbyssJewel` jewels (count is the scaling axis; the validator does not track jewel sockets, so the jewels themselves are not validated — marked UNKNOWN, not assumed).

Note: the Research API exposes modifier/stat identifiers, not display text; lists above are exact API ids, unmodified.

## Why it works

The jewel count X is a single investment axis: each abyssal jewel raises maximum mana % (twice — via the Shroud and via Lightless), raises life %, and adds flat life/mana through the Shroud. Mana is never spent (WoI pays costs from energy shield), so the whole pool feeds WoI's per-100-mana attack chaos. The per-jewel elemental penetration boosts the elemental portion of the same attacks — a second, jewel-scaled path into the hit.

## Scaling claim

**Multi-use with a partial second damage path (not confirmed quadratic).** X = abyssal jewels → A: maximum mana % (flat + percentage, two sources) → WoI added chaos; B: elemental penetration per jewel → same attacks' elemental damage; C: life % per jewel (defence). A and B both scale with X into the same attack, but the KB does not establish that the chaos and elemental shares interact — recorded as hypothesis at most.

## Evidence

- `carriers(stat:maximum_mana_+%_per_abyssal_jewel_affecting_you)` → exactly 3 carriers: 2 Shroud mods + `passive:AscendancyCustomTrickster14` (redundant %mana sources)
- `mod:IncreasedManaPerAbyssalJewelUnique__2` (uma carriers: unique:734, unique:735 — both Shroud of the Lightless variants)
- `mod:ElementalPenetrationPerAbyssalJewelUnique__1` → `stat:penetrate_elemental_resistance_%_per_abyssal_jewel_affecting_you`

## Validation

3/3 additions valid; final `validate_build` (final=True): **valid** — availability all available, class_mix `['Trickster']`. Abyssal jewels themselves: UNKNOWN (outside validator scope).
