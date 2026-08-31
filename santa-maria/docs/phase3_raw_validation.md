# Phase 3 — Raw Snapshot Validation / Sanity Check

Source: `cache/raw_records.db` only (Phase 2 lossless raw snapshot). No source files were read; no schema/node/edge decisions.

## 1. Ignite vs. Ignited (distinct stat identifiers)

### `repoe/stats.json` — `base_chance_to_ignite_%`
```json
{
  "alias": {
    "when_in_off_hand": null,
    "when_in_main_hand": null
  },
  "is_aliased": false,
  "is_local": false
}
```
### `repoe/stats.json` — `damage_+%_while_ignited`
```json
{
  "alias": {
    "when_in_off_hand": null,
    "when_in_main_hand": null
  },
  "is_aliased": false,
  "is_local": false
}
```
**Statement:** the two stat ids are **distinct records/concepts** in `stats.json` (separate `record_key`s), and are referenced by separate `mods.json` records.

### Representative `repoe/mods.json` records referencing `base_chance_to_ignite_%`
#### `BetrayalUpgradeMonsterFireDamageAndIgnite`
```json
{
  "adds_tags": [],
  "domain": "monster",
  "generation_type": "unique",
  "generation_weights": [],
  "grants_effects": [],
  "groups": [
    "PhysicalAddedAsFire"
  ],
  "implicit_tags": [
    "physical_damage",
    "elemental_damage",
    "bleed",
    "damage",
    "physical",
    "elemental",
    "fire",
    "ailment"
  ],
  "is_essence_only": false,
  "name": "",
  "required_level": 1,
  "spawn_weights": [],
  "stats": [
    {
      "id": "physical_damage_%_to_add_as_fire",
      "max": 50,
      "min": 50
    },
    {
      "id": "all_damage_can_ignite",
      "max": 1,
      "min": 1
    },
    {
      "id": "base_chance_to_ignite_%",
      "max": 100,
      "min": 100
    }
  ],
  "text": null,
  "type": "MonsterFireDamageAndIgnite",
  "gold_value": null
}
```
#### `ChanceToIgnite1`
```json
{
  "adds_tags": [],
  "domain": "item",
  "generation_type": "suffix",
  "generation_weights": [],
  "grants_effects": [],
  "groups": [
    "ChanceToIgnite"
  ],
  "implicit_tags": [
    "elemental",
    "fire",
    "ailment"
  ],
  "is_essence_only": false,
  "name": "of Ignition",
  "required_level": 15,
  "spawn_weights": [
    {
      "tag": "sceptre",
      "weight": 1000
    },
    {
      "tag": "wand",
      "weight": 1000
    },
    {
      "tag": "default",
      "weight": 0
    }
  ],
  "stats": [
    {
      "id": "base_chance_to_ignite_%",
      "max": 24,
      "min": 18
    }
  ],
  "text": "(18-24)% chance to Ignite",
  "type": "ChanceToIgnite",
  "gold_value": null
}
```
### Representative `repoe/mods.json` records referencing `damage_+%_while_ignited`
#### `DamageWhileIgnitedUniqueRing18`
```json
{
  "adds_tags": [],
  "domain": "item",
  "generation_type": "unique",
  "generation_weights": [],
  "grants_effects": [],
  "groups": [
    "DamageWhileIgnited"
  ],
  "implicit_tags": [
    "damage"
  ],
  "is_essence_only": false,
  "name": "",
  "required_level": 1,
  "spawn_weights": [],
  "stats": [
    {
      "id": "damage_+%_while_ignited",
      "max": 30,
      "min": 30
    }
  ],
  "text": "30% increased Damage while Ignited",
  "type": "DamageWhileIgnited",
  "gold_value": null
}
```
#### `DamageWhileIgnitedUnique__1`
```json
{
  "adds_tags": [],
  "domain": "item",
  "generation_type": "unique",
  "generation_weights": [],
  "grants_effects": [],
  "groups": [
    "DamageWhileIgnited"
  ],
  "implicit_tags": [
    "damage"
  ],
  "is_essence_only": false,
  "name": "",
  "required_level": 85,
  "spawn_weights": [],
  "stats": [
    {
      "id": "damage_+%_while_ignited",
      "max": 70,
      "min": 50
    }
  ],
  "text": "(50-70)% increased Damage while Ignited",
  "type": "DamageWhileIgnited",
  "gold_value": null
}
```

## 2. Crown of Eyes
### `repoe/uniques.json` — record_key `168`
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

### `repoe/mods.json` — 11 records with key containing `UniqueHelmetInt7` (naming convention)
#### `DivergentSpellDamageModifiersApplyToAttackDamageUniqueHelmetInt7` (generation_type: unique)
```json
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
#### `FireResistUniqueHelmetInt7` (generation_type: unique)
```json
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
#### `IncreasedAccuracyUniqueHelmetInt7` (generation_type: unique)
```json
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
#### `IncreasedAccuracyUniqueHelmetInt7Royale` (generation_type: unique)
```json
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
#### `LifeLeechPermyriadUniqueHelmetInt7` (generation_type: unique)
```json
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
#### `LifeLeechUniqueHelmetInt7` (generation_type: unique)
```json
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
#### `LocalIncreasedEnergyShieldUniqueHelmetInt7` (generation_type: unique)
```json
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
#### `ManaLeechPermyriadUniqueHelmetInt7` (generation_type: unique)
```json
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
#### `ManaLeechUniqueHelmetInt7` (generation_type: unique)
```json
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
#### `NonCriticalDamageMultiplierUniqueHelmetInt7` (generation_type: unique)
```json
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
#### `SpellDamageModifiersApplyToAttackDamageUniqueHelmetInt7` (generation_type: unique)
```json
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

### `pob/ModItemExclusive.json` — 9 records with key containing `UniqueHelmetInt7`
#### `DivergentSpellDamageModifiersApplyToAttackDamageUniqueHelmetInt7`
```json
{
  "affix": "",
  "group": "SpellDamageModifiersApplyToAttackDamage",
  "level": 69,
  "modTags": [
    "divergentunique",
    "damage",
    "attack"
  ],
  "statOrder": [
    2717
  ],
  "tradeHashes": {
    "3811649872": [
      "Attacks have 100% Arcane Might"
    ]
  },
  "weightKey": [],
  "weightVal": [],
  "1": "Attacks have 100% Arcane Might"
}
```
#### `FireResistUniqueHelmetInt7`
```json
{
  "affix": "",
  "group": "FireResistance",
  "level": 1,
  "modTags": [
    "elemental",
    "fire",
    "resistance"
  ],
  "statOrder": [
    1652
  ],
  "tradeHashes": {
    "3372524247": [
      "-30% to Fire Resistance"
    ]
  },
  "weightKey": [],
  "weightVal": [],
  "1": "-30% to Fire Resistance"
}
```
#### `IncreasedAccuracyUniqueHelmetInt7`
```json
{
  "affix": "",
  "group": "IncreasedAccuracy",
  "level": 1,
  "modTags": [
    "attack"
  ],
  "statOrder": [
    1461
  ],
  "tradeHashes": {
    "803737631": [
      "+(300-350) to Accuracy Rating"
    ]
  },
  "weightKey": [],
  "weightVal": [],
  "1": "+(300-350) to Accuracy Rating"
}
```
#### `LifeLeechPermyriadUniqueHelmetInt7`
```json
{
  "affix": "",
  "group": "LifeLeechFromAttacksPermyriad",
  "level": 1,
  "modTags": [
    "resource",
    "life",
    "attack"
  ],
  "statOrder": [
    1691
  ],
  "tradeHashes": {
    "141810208": [
      "(0.4-0.8)% of Attack Damage Leeched as Life"
    ]
  },
  "weightKey": [],
  "weightVal": [],
  "1": "(0.4-0.8)% of Attack Damage Leeched as Life"
}
```
#### `LifeLeechUniqueHelmetInt7`
```json
{
  "affix": "",
  "group": "LifeLeech",
  "level": 1,
  "modTags": [
    "resource",
    "life",
    "physical",
    "attack"
  ],
  "statOrder": [
    1674
  ],
  "tradeHashes": {
    "3933739162": [
      "(2-4)% of Physical Attack Damage Leeched as Life"
    ]
  },
  "weightKey": [],
  "weightVal": [],
  "1": "(2-4)% of Physical Attack Damage Leeched as Life"
}
```
#### `LocalIncreasedEnergyShieldUniqueHelmetInt7`
```json
{
  "affix": "",
  "group": "LocalEnergyShieldPercent",
  "level": 1,
  "modTags": [
    "defences",
    "energy_shield"
  ],
  "statOrder": [
    1586
  ],
  "tradeHashes": {
    "4015621042": [
      "(120-150)% increased Energy Shield"
    ]
  },
  "weightKey": [],
  "weightVal": [],
  "1": "(120-150)% increased Energy Shield"
}
```
#### `ManaLeechPermyriadUniqueHelmetInt7`
```json
{
  "affix": "",
  "group": "AttackDamageManaLeech",
  "level": 1,
  "modTags": [
    "resource",
    "mana",
    "attack"
  ],
  "statOrder": [
    1732
  ],
  "tradeHashes": {
    "350069479": [
      "(0.2-0.4)% of Attack Damage Leeched as Mana"
    ]
  },
  "weightKey": [],
  "weightVal": [],
  "1": "(0.2-0.4)% of Attack Damage Leeched as Mana"
}
```
#### `ManaLeechUniqueHelmetInt7`
```json
{
  "affix": "",
  "group": "ManaLeech",
  "level": 1,
  "modTags": [
    "resource",
    "mana",
    "physical",
    "attack"
  ],
  "statOrder": [
    1724
  ],
  "tradeHashes": {
    "3907785920": [
      "(1-2)% of Physical Attack Damage Leeched as Mana"
    ]
  },
  "weightKey": [],
  "weightVal": [],
  "1": "(1-2)% of Physical Attack Damage Leeched as Mana"
}
```
#### `SpellDamageModifiersApplyToAttackDamageUniqueHelmetInt7`
```json
{
  "affix": "",
  "group": "SpellDamageModifiersApplyToAttackDamage150Percent",
  "level": 1,
  "modTags": [
    "damage",
    "attack"
  ],
  "statOrder": [
    2718
  ],
  "tradeHashes": {
    "185598681": [
      "Attacks have 150% Arcane Might"
    ]
  },
  "weightKey": [],
  "weightVal": [],
  "1": "Attacks have 150% Arcane Might"
}
```

### `pob/TradeSiteStats.json` — Crown trade-id entries (within group record_key `1`, label `Explicit`)
```json
{
  "id": "explicit.stat_4015621042",
  "text": "#% increased Energy Shield (Local)",
  "type": "explicit"
}
```
```json
{
  "id": "explicit.stat_141810208",
  "text": "#% of Attack Damage Leeched as Life",
  "type": "explicit"
}
```
```json
{
  "id": "explicit.stat_350069479",
  "text": "#% of Attack Damage Leeched as Mana",
  "type": "explicit"
}
```
```json
{
  "id": "explicit.stat_803737631",
  "text": "+# to Accuracy Rating",
  "type": "explicit"
}
```
```json
{
  "id": "explicit.stat_3372524247",
  "text": "+#% to Fire Resistance",
  "type": "explicit"
}
```
```json
{
  "id": "explicit.stat_3811649872",
  "text": "Attacks have 100% Arcane Might",
  "type": "explicit"
}
```
```json
{
  "id": "explicit.stat_185598681",
  "text": "Attacks have 150% Arcane Might",
  "type": "explicit"
}
```

### `pob/QueryMods.json` — context record_key `Explicit`, mod-key slots whose `tradeMod.id` is a Crown trade id
#### `1461_IncreasedAccuracy`
```json
{
  "AbyssJewel": {
    "max": 300,
    "min": 10
  },
  "Amulet": {
    "max": 480,
    "min": 50
  },
  "Gloves": {
    "max": 600,
    "min": 50
  },
  "Helmet": {
    "max": 600,
    "min": 50
  },
  "Quiver": {
    "max": 600,
    "min": 50
  },
  "Ring": {
    "max": 480,
    "min": 50
  },
  "Shield": {
    "max": 480,
    "min": 50
  },
  "sign": "",
  "specialCaseData": [],
  "tradeMod": {
    "id": "explicit.stat_803737631",
    "text": "+# to Accuracy Rating",
    "type": "explicit"
  }
}
```
#### `1461_IncreasedAccuracyForJewel`
```json
{
  "sign": "",
  "specialCaseData": [],
  "tradeMod": {
    "id": "explicit.stat_803737631",
    "text": "+# to Accuracy Rating",
    "type": "explicit"
  }
}
```
#### `1461_LightRadiusAndAccuracy`
```json
{
  "sign": "",
  "specialCaseData": [],
  "tradeMod": {
    "id": "explicit.stat_803737631",
    "text": "+# to Accuracy Rating",
    "type": "explicit"
  }
}
```
#### `1586_LocalEnergyShieldAndStunRecoveryPercent`
```json
{
  "Boots": {
    "max": 42,
    "min": 6
  },
  "Chest": {
    "max": 42,
    "min": 6
  },
  "Gloves": {
    "max": 42,
    "min": 6
  },
  "Helmet": {
    "max": 42,
    "min": 6
  },
  "Shield": {
    "max": 42,
    "min": 6
  },
  "sign": "",
  "specialCaseData": {
    "overrideModLine": "#% increased Energy Shield"
  },
  "tradeMod": {
    "id": "explicit.stat_4015621042",
    "text": "#% increased Energy Shield (Local)",
    "type": "explicit"
  }
}
```
#### `1586_LocalEnergyShieldPercent`
```json
{
  "Boots": {
    "max": 100,
    "min": 11
  },
  "Chest": {
    "max": 110,
    "min": 11
  },
  "Gloves": {
    "max": 100,
    "min": 11
  },
  "Helmet": {
    "max": 100,
    "min": 11
  },
  "Shield": {
    "max": 110,
    "min": 11
  },
  "sign": "",
  "specialCaseData": {
    "overrideModLine": "#% increased Energy Shield"
  },
  "tradeMod": {
    "id": "explicit.stat_4015621042",
    "text": "#% increased Energy Shield (Local)",
    "type": "explicit"
  }
}
```
#### `1586_LocalEnergyShieldPercentSuffix`
```json
{
  "AbyssJewel": {
    "max": 50,
    "min": 25
  },
  "sign": "",
  "specialCaseData": {
    "overrideModLine": "#% increased Energy Shield"
  },
  "tradeMod": {
    "id": "explicit.stat_4015621042",
    "text": "#% increased Energy Shield (Local)",
    "type": "explicit"
  }
}
```
#### `1586_LocalIncreasedEnergyShieldAndLife`
```json
{
  "Boots": {
    "max": 28,
    "min": 12
  },
  "Chest": {
    "max": 28,
    "min": 12
  },
  "Gloves": {
    "max": 28,
    "min": 24
  },
  "Helmet": {
    "max": 28,
    "min": 12
  },
  "Shield": {
    "max": 28,
    "min": 12
  },
  "sign": "",
  "specialCaseData": {
    "overrideModLine": "#% increased Energy Shield"
  },
  "tradeMod": {
    "id": "explicit.stat_4015621042",
    "text": "#% increased Energy Shield (Local)",
    "type": "explicit"
  }
}
```
#### `1652_FireDamageAvoidanceMaven`
```json
{
  "Boots": {
    "max": 30,
    "min": 20
  },
  "Shield": {
    "max": 30,
    "min": 20
  },
  "sign": "",
  "specialCaseData": [],
  "tradeMod": {
    "id": "explicit.stat_3372524247",
    "text": "+#% to Fire Resistance",
    "type": "explicit"
  }
}
```
#### `1652_FireResistance`
```json
{
  "Amulet": {
    "max": 48,
    "min": 6
  },
  "Belt": {
    "max": 48,
    "min": 6
  },
  "Boots": {
    "max": 48,
    "min": 6
  },
  "Chest": {
    "max": 48,
    "min": 6
  },
  "Gloves": {
    "max": 48,
    "min": 6
  },
  "Helmet": {
    "max": 48,
    "min": 6
  },
  "Quiver": {
    "max": 48,
    "min": 6
  },
  "Ring": {
    "max": 48,
    "min": 6
  },
  "Shield": {
    "max": 48,
    "min": 6
  },
  "sign": "",
  "specialCaseData": [],
  "tradeMod": {
    "id": "explicit.stat_3372524247",
    "text": "+#% to Fire Resistance",
    "type": "explicit"
  }
}
```
#### `1652_FireResistanceAilments`
```json
{
  "Gloves": {
    "max": 48,
    "min": 46
  },
  "sign": "",
  "specialCaseData": [],
  "tradeMod": {
    "id": "explicit.stat_3372524247",
    "text": "+#% to Fire Resistance",
    "type": "explicit"
  }
}
```
#### `1652_FireResistanceEnemyLeech`
```json
{
  "Amulet": {
    "max": 48,
    "min": 46
  },
  "sign": "",
  "specialCaseData": [],
  "tradeMod": {
    "id": "explicit.stat_3372524247",
    "text": "+#% to Fire Resistance",
    "type": "explicit"
  }
}
```
#### `1652_FireResistanceForJewel`
```json
{
  "AbyssJewel": {
    "max": 15,
    "min": 12
  },
  "AnyJewel": {
    "max": 15,
    "min": 12
  },
  "BaseJewel": {
    "max": 15,
    "min": 12
  },
  "sign": "",
  "specialCaseData": [],
  "tradeMod": {
    "id": "explicit.stat_3372524247",
    "text": "+#% to Fire Resistance",
    "type": "explicit"
  }
}
```
#### `1652_FireResistanceLeech`
```json
{
  "Amulet": {
    "max": 48,
    "min": 46
  },
  "sign": "",
  "specialCaseData": [],
  "tradeMod": {
    "id": "explicit.stat_3372524247",
    "text": "+#% to Fire Resistance",
    "type": "explicit"
  }
}
```
#### `1652_FireResistancePhysTakenAsFire`
```json
{
  "Helmet": {
    "max": 48,
    "min": 46
  },
  "sign": "",
  "specialCaseData": [],
  "tradeMod": {
    "id": "explicit.stat_3372524247",
    "text": "+#% to Fire Resistance",
    "type": "explicit"
  }
}
```
#### `1652_FireResistancePrefix`
```json
{
  "sign": "",
  "specialCaseData": [],
  "tradeMod": {
    "id": "explicit.stat_3372524247",
    "text": "+#% to Fire Resistance",
    "type": "explicit"
  }
}
```
#### `1691_LifeLeechFromAttacksPermyriad`
```json
{
  "AbyssJewel": {
    "max": 0.3,
    "min": 0.3
  },
  "AnyJewel": {
    "max": 0.3,
    "min": 0.3
  },
  "BaseJewel": {
    "max": 0.3,
    "min": 0.3
  },
  "sign": "",
  "specialCaseData": [],
  "tradeMod": {
    "id": "explicit.stat_141810208",
    "text": "#% of Attack Damage Leeched as Life",
    "type": "explicit"
  }
}
```

### `pob/ModCache.json` — Crown display texts present as keys (partial overlap; range-form texts absent by design)
#### `Attacks have 150% Arcane Might`
```json
[
  [
    {
      "flags": 0,
      "keywordFlags": 0,
      "name": "SpellDamageAppliesToAttacks",
      "type": "FLAG",
      "value": true
    },
    {
      "flags": 0,
      "keywordFlags": 0,
      "name": "ImprovedSpellDamageAppliesToAttacks",
      "type": "MAX",
      "value": 150
    }
  ]
]
```
#### `Attacks have 100% Arcane Might`
```json
[
  [
    {
      "flags": 0,
      "keywordFlags": 0,
      "name": "SpellDamageAppliesToAttacks",
      "type": "FLAG",
      "value": true
    },
    {
      "flags": 0,
      "keywordFlags": 0,
      "name": "ImprovedSpellDamageAppliesToAttacks",
      "type": "MAX",
      "value": 100
    }
  ]
]
```
#### `-30% to Fire Resistance`
```json
[
  [
    {
      "flags": 0,
      "keywordFlags": 0,
      "name": "FireResist",
      "type": "BASE",
      "value": -30
    }
  ]
]
```

**Observed lookup chain (factual, no schema design):** `uniques.visual_identity.id = UniqueHelmetInt7` → (naming convention) → 11 `mods.json` keys → `mods.stats[].id`; PoB side: same keys → `ModItemExclusive.tradeHashes[hash]` → `TradeSiteStats` `explicit.stat_<hash>` → text; `QueryMods` indexes those trade ids across its own mod-key slots; `ModCache` normalizes some display texts. The unique and its structured modifiers survived the Phase 2 snapshot and are traceable.

## 3. Iron Will — `repoe/passive_skill_trees/Default.json` (single-file record `record_key=''`) → `passives["50288"]`
```json
{
  "flavour_text": "Legend tells of incantations so powerful that only giants could recite them.",
  "hash": 50288,
  "icon": "Art/2DArt/SkillIcons/passives/KeystoneIronWill.dds",
  "id": "iron_will_keystone2850",
  "is_ascendancy_starting_node": false,
  "is_icon_only": false,
  "is_jewel_socket": false,
  "is_keystone": true,
  "is_multiple_choice": false,
  "is_multiple_choice_option": false,
  "is_notable": false,
  "name": "Iron Will",
  "reminder_text": [],
  "skill_points": 0,
  "stats": {
    "strong_casting": 1
  }
}
```
- `id`: `iron_will_keystone2850` | `name`: `Iron Will` | `is_keystone`: `true` | `stats`: `{"strong_casting": 1}`

## 4. Avatar of Fire — `Default.json` → `passives["44941"]`
```json
{
  "flavour_text": "\"In my dreams I see a great warrior, his skin scorched black, his fists aflame.\"",
  "hash": 44941,
  "icon": "Art/2DArt/SkillIcons/passives/KeystoneAvatarOfFire.dds",
  "id": "avatar_of_fire1543",
  "is_ascendancy_starting_node": false,
  "is_icon_only": false,
  "is_jewel_socket": false,
  "is_keystone": true,
  "is_multiple_choice": false,
  "is_multiple_choice_option": false,
  "is_notable": false,
  "name": "Avatar of Fire",
  "reminder_text": [],
  "skill_points": 0,
  "stats": {
    "keystone_avatar_of_fire": 1
  }
}
```
- `id`: `avatar_of_fire1543` | `name`: `Avatar of Fire` | `is_keystone`: `true` | `stats`: `{"keystone_avatar_of_fire": 1}`

## Validation result
| target | result |
|---|---|
| Ignite stat | PASS |
| Ignited stat | PASS |
| Crown of Eyes | PASS |
| Iron Will | PASS |
| Avatar of Fire | PASS |
| **Overall** | **PASS** |

Every required raw record is present in `raw_records`. The Phase 2 snapshot preserved the raw data required for the next phase.
