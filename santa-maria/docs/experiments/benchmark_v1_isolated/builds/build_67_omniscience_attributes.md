# Build 67 — Crystallised Omniscience Attribute Stacker

Status: **VALIDATED** (item-level; converter layer KB-thin — see facts)

Central interaction: all three attributes collapse into one investment (Omniscience), feeding the attribute mechanic's per-attribute scaling vocabulary.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | **Crystallised Omniscience** (unique:1327, available) | attribute-stacking anchor (resolved by `resolve('omniscience')` within this session) |
| Gear (rare, marked: slot filler) | per-attribute converters | `attack_maximum_added_lightning_damage_per_10_dex` family — 1 KB carrier (`mod:AddedLightningDamagePerDexterityUnique__1`, unassociated unique) |
| Gear (rare, marked: slot filler) | per-12-strength area damage | `area_damage_+%_per_12_strength` — 1 carrier ('of Shaping' uber) |
| Gear (marked: slot filler) | per-25-int cold damage | `cold_damage_+%_per_25_intelligence` — **0 carriers** (stat exists; no mod grants it in the KB) |
| Derived defences (fact) | attribute_grants_stat derivations | strength → base_maximum_life / X_to_armour_per_2_strength; dexterity → evasion_rating_+% / accuracy; intelligence → base_maximum_mana / accuracy-per-int |

**Why it works** — The attribute mechanic node holds 107 related stats, all role `scaling`: life/mana per attribute, accuracy per attribute, added elemental damage per attribute, AoE/crit/avoidance per attribute. Attributes therefore act as a *meta-axis*: one investment (all attributes) fans out into offense (added damage, crit, AoE), defense (life, armour, evasion) and utility (mana, accuracy) simultaneously — multi-use by construction. The KB-thin caveat: individual converter stats have 0–1 carriers in this KB build, so the converter layer is primarily a rare-gear path, not a unique-anchor path.

**Evidence**
- mechanic:attribute: 107 related stats, role=relation:scaling (X_accuracy_per_2_intelligence, X_life_per_4_dexterity, X_mana_per_4_strength, per-attribute added damage family…)
- attribute_grants_stat chains: strength → base_maximum_life; dexterity → evasion/accuracy; intelligence → base_maximum_mana
- stat_scales_with chains: strength → armour/damage-per-strength derivations; intelligence → crit/damage-per-int
- stat:attack_maximum_added_lightning_damage_per_10_dex ← mgs=1; stat:area_damage_+%_per_12_strength ← mgs=1; stat:cold_damage_+%_per_25_intelligence ← mgs=0 (fact)

Validation: `validate_build{items:[Crystallised Omniscience]}` → **valid** (availability: available). Converter/rare-gear layer not committable (items-only validator model).
