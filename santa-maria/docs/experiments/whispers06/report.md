# whispers06 — Whispers of Infinity build discovery

Run: 2026-09-21 · Clean slate (previous runs not read or reused) · All mechanics derived from the public Research API (`resolve` / `carriers` / `neighbour` / `validate`) · Alternate-ascendancy exclusion ON (`excluded_alternate_ascendancies: 0` in every probe — no suppression occurred).

Seed: `unique:1461` **Whispers of Infinity** (Amulet, available):

- **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana**
- (60-40)% reduced maximum Mana
- (10-15)% faster start of Energy Shield Recharge
- **Skills Cost Energy Shield instead of Mana or Life**

The headline mod makes **maximum mana** the amulet's scaling input; the amulet itself *reduces* maximum mana, so every architecture below needs external mana/Intelligence generation. The cost conversion means mana is *not spent* by skills — mana-spent effects (Indigon, trigger-on-spend) are dead weight here (see Rejected).

---

## Scaling axes found (all API-derived)

| Axis | Generators (KB evidence) | Consumers feeding attack damage |
| ---- | ------------------------ | ------------------------------- |
| Maximum mana | `rule:intelligence_mana` "1 Mana per 2 Intelligence" (surfaces on `stat:base_maximum_mana` via `rule_applies_to` + `attribute_grants_stat` from `stat:intelligence`); 11 passive granters of `stat:base_maximum_mana` (e.g. Deep Wisdom, Path of the Savant, Soul Siphon, Revelry); 235 modifier granters | Whispers chaos/100 mana; Kinetic Blast of Clustering (added phys = % max mana); Power Siphon of the Archmage (added lightning = % max mana); Mind of the Council (added lightning = 6% max mana); Synthesis implicit increased Attack Damage per 500 max mana |
| Intelligence | 89 passives grant `stat:base_intelligence`; 123 mods grant `stat:additional_intelligence`; %int mods (Whispering Ice, HoWA, HoTM) | int→mana→everything above; Hand of Wisdom and Action (added lightning/10 int); Heavy Strike of Trarthus (double-damage chance per 10 int); Whispering Ice spell dmg/10 int → Arcane Might bridge |
| Defense riders | — | Skyforth (stun threshold = 500% mana); Omeyocan (evasion per 500 mana); Mind of the Council (30% lightning damage taken from mana) |

The spell→attack bridge is a first-class KB mechanic: `mechanic:applies_to_spell_damage_applies_to_attacks`, operands `stat:spell_damage_+%` (input) → `stat:attack_damage_+%` (output), with variants incl. `..._at_150%_value` (carried by Crown of Eyes' "Attacks have 150% Arcane Might") and `..._while_wielding_wand` (no live carrier in KB — true absence under `carriers()`).

---

## Build 1 — Arcane Might Staff (Int → mana + spell→attack bridge)

Status: **VALIDATED** (slot occupancy, weapon configuration, gem supportability, ascendancy composition; passives/ascendancy left uncommitted → not ascendancy-checked). Ascendancy: UNKNOWN.

Central interaction: Intelligence feeds staff attack damage through two interacting paths — via the mana pool (Whispers' per-100-mana added chaos) and via spell-damage-per-Int converted to attack damage at 150% value (Crown of Eyes' Arcane Might). Added × increased = quadratic-in-Int structure; Heavy Strike of Trarthus adds a third Int-fed path (double-damage chance per 10 Int).

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | **Whispers of Infinity** (available) | **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana**; (60-40)% reduced maximum Mana; (10-15)% faster start of Energy Shield Recharge; **Skills Cost Energy Shield instead of Mana or Life** |
| Helmet | **Crown of Eyes** (available) | **Attacks have 150% Arcane Might**; +(300-350) to Accuracy Rating; (120-150)% increased Energy Shield; (0.4-0.8)% of Attack Damage Leeched as Life; (0.2-0.4)% of Attack Damage Leeched as Mana; -30% to Fire Resistance |
| Weapon | **The Whispering Ice** (Staff, available) | **1% increased Spell Damage per 10 Intelligence**; Grants Level 1 Icestorm Skill; (14-18)% increased Intelligence; +1 to Level of Socketed Support Gems; (8-12)% increased Cast Speed |
| Attack gem | **Heavy Strike of Trarthus** (level/quality UNKNOWN — gem values not exposed by API) | Gem-granted stats: `chance_to_deal_double_damage_%_per_10_intelligence`, `active_skill_additive_spell_damage_modifiers_apply_to_attack_damage_at_%_value` (per-gem % value UNKNOWN), `chance_to_deal_double_damage_%`, `damage_+%`, `attack_speed_+%`, `trigger_level_20_bone_corpses_on_stun`, tag `attack` |
| Passives | Tree (uncommitted) | 89 passive granters of base Intelligence; mana notables (Deep Wisdom, Path of the Savant, Soul Siphon, …); engine rule `intelligence_mana`: 1 Mana per 2 Intelligence |

**Why it works** — The staff converts Intelligence into spell damage (1%/10 Int); Crown of Eyes applies spell-damage modifiers to attack damage at 150% of their value, so that same Int now multiplies staff attack hits. Independently, Intelligence generates maximum mana (1 mana per 2 Int, engine rule), and every 100 mana adds attack chaos damage on the amulet. Both paths scale linearly with the same X and combine multiplicatively in one output (added term × increased term) — quadratic structure. Heavy Strike of Trarthus is the attack: it natively carries the spell→attack bridge stat and adds double-damage chance per 10 Int, a third Int-dependent multiplier on the same hits. Validator confirmed staff + Heavy Strike of Trarthus weapon compatibility.

**Evidence** —
`stat:intelligence` → `attribute_grants_stat` → `stat:base_maximum_mana`; `rule:intelligence_mana` → `rule_applies_to` → `stat:base_maximum_mana`
`mod:SpellDamagePerIntelligenceUniqueStaff12` → `unique:326`
`mod:SpellDamageModifiersApplyToAttackDamageUniqueHelmetInt7` → grants `stat:additive_spell_damage_modifiers_apply_to_attack_damage_at_150%_value` → `stat_mechanic_variant` → mechanic `applies_to_spell_damage_applies_to_attacks` (operands: `stat:spell_damage_+%` in, `stat:attack_damage_+%` out)
`gem:HeavyStrikeAltY` → `gem_grants_stat` → `stat:chance_to_deal_double_damage_%_per_10_intelligence` + bridge stat
`unique:1461` → `unique_modifier_association` → `mod:AttacksGainMinMaxAddedChaosDamageBasedOnManaUnique__1` "(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana"

Ladder: **quadratic confirmed (structure)** — X=Int; paths: Int→mana→added chaos, Int→spell dmg→150% bridge→increased attack damage, Int→double-damage chance; common output: Heavy Strike hits; combining mechanic: added-damage term × increased-damage term (× hit-double chance). Magnitudes are ranges/UNKNOWN (gem values not exposed).

---

## Build 2 — Hand of Wisdom and Action Int-stacker (multi-use, honest linear)

Status: **VALIDATED** (same scope as Build 1). Ascendancy: UNKNOWN.

Central interaction: Intelligence feeds the same claw attack hits through two independent additive paths — direct added lightning per 10 Int on the weapon, and via mana through the amulet's per-100-mana added chaos. Two consumers, one output: multi-use, not quadratic (no Int-fed multiplier exists outside the rival claw — see evidence).

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | **Whispers of Infinity** (available) | **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana**; (60-40)% reduced maximum Mana; (10-15)% faster start of Energy Shield Recharge; **Skills Cost Energy Shield instead of Mana or Life** |
| Weapon | **Hand of Wisdom and Action** (Claw, available) | **Adds 1 to 12 Lightning Damage to Attacks with this Weapon per 10 Intelligence**; 1% of Attack Damage Leeched as Life; (8-12)% increased Intelligence; (8-12)% increased Dexterity |
| Attack gem | **Lightning Strike** (level/quality UNKNOWN) | Claw-legal per validator weapon check (`weapon_restriction` passed) |
| Passives | Tree (uncommitted) | base Intelligence granters + mana notables; rule `intelligence_mana` (1 Mana per 2 Int) |

**Why it works** — The claw turns every 10 Intelligence into added lightning on its attacks; the amulet turns the mana that Intelligence generates into added attack chaos. Both added-damage streams land on the same claw hits, and the claw's own %Int compounds the generator. This is genuinely two consumers of one axis (multi-use); the KB has an Int→crit modifier (5% increased Critical Strike Chance per 25 Int) but its only carrier is the rival claw Hand of Thought and Motion — same slot, so it cannot join this build. Without an Int-fed multiplier the architecture stays linear.

**Evidence** —
`mod:AddedLightningDamagePerIntelligenceUnique__1` → `unique:597`
`mod:CriticalStrikeChancePerIntelligenceUnique__1` → `unique:596` (Hand of Thought and Motion, Claw — slot-exclusive, excluded here)
`rule:intelligence_mana` → `stat:base_maximum_mana` → `unique:1461` chaos/100 mana

Ladder: **multi-use** (two additive paths, one output). Slot-exclusivity of the crit mod is a KB fact, not a judgment call.

---

## Build 3 — Mana-Archmage Wand (multi-use; X² with an unknown-availability multiplier)

Status: **VALIDATED** (both boot options validated). Ascendancy: UNKNOWN.

Central interaction: maximum mana itself is the weapon — league-gem attacks convert % of maximum mana into added phys/lightning on wand attacks, stacking with the amulet's per-100-mana chaos. A Synthesis implicit multiplier (increased Attack Damage per 500 max mana) exists in the KB but has no carrier row, so the quadratic version is a hypothesis pending availability.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | **Whispers of Infinity** (available) | **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana**; (60-40)% reduced maximum Mana; (10-15)% faster start of Energy Shield Recharge; **Skills Cost Energy Shield instead of Mana or Life** |
| Weapon | **Storm Prison** (Wand, available — availability-legal slot stand-in) | Adds (1-2) to (9-11) Lightning Damage to Spells and Attacks; Adds 1 to (35-45) Lightning Damage; (15-25)% increased Mana Regeneration Rate; (25-35)% chance to gain a Power Charge on Kill |
| Attack gem (main option) | **Kinetic Blast of Clustering** (level/quality UNKNOWN) | Gem-granted stats include `added_physical_damage_to_attacks_equal_to_%_maximum_mana` (% value UNKNOWN), `active_skill_additive_spell_damage_modifiers_apply_to_attack_damage_at_%_value` (value UNKNOWN), `skill_can_fire_wand_projectiles` |
| Attack gem (alt option) | **Power Siphon of the Archmage** (level/quality UNKNOWN) | Gem-granted stats include `attack_skills_have_added_lightning_damage_equal_to_%_of_maximum_mana` (% value UNKNOWN), bridge stat (value UNKNOWN), power-charge-on-hit stats |
| Boots (main) | **Skyforth** (available) | **Stun Threshold is based on 500% of your Mana instead of Life**; +(60-120) to maximum Mana; 25% chance to gain a Power Charge on Critical Strike |
| Boots (alt, validated) | **Omeyocan** (available) | **20% increased Evasion Rating per 500 Maximum Mana**; (15-20)% increased maximum Mana; You have Onslaught while not on Low Mana; Lose 7% of Mana per Second |
| Multiplier (uncommitted) | Synthesis implicit | **(6-8)% / (12-14)% increased Attack Damage per 500 Maximum Mana** (`mod:SynthesisImplicitAttackDamagePerMana1/2`) — availability UNKNOWN (no carrier rows in KB) |
| Passives | Tree (uncommitted) | 11 passive granters of `stat:base_maximum_mana`; mana notables |

**Why it works** — Three KB-evidenced consumers turn the same mana pool into wand attack damage: the gem's %-of-mana added damage (phys via Kinetic Blast of Clustering, lightning via Power Siphon of the Archmage), and the amulet's added chaos per 100 mana. The gems also natively carry the spell→attack bridge stat, so spell-damage sources have a modeled (value-UNKNOWN) route onto these attacks. Skyforth converts the huge mana pool into anti-stun EHP and feeds Power Charges; Omeyocan trades that for evasion-per-mana — but its 7%/s mana drain works against %-of-maximum-mana damage and its "Onslaught while not on Low Mana" requirement, a flagged tension. The quadratic claim needs the Synthesis implicit (added per mana × increased per mana); until a carrier exists in the KB it stays a hypothesis.

**Evidence** —
`gem:KineticBlastAltX` → `gem_grants_stat` → `stat:added_physical_damage_to_attacks_equal_to_%_maximum_mana`
`gem:PowerSiphonAltX` → `gem_grants_stat` → `stat:attack_skills_have_added_lightning_damage_equal_to_%_of_maximum_mana`
`unique:1461` → chaos/100 mana; `mod:SynthesisImplicitAttackDamagePerMana1/2` → `stat:attack_damage_+%_per_500_maximum_mana` (0 carriers)
`unique:448` stun-threshold/500% mana; `unique:795` evasion/500 mana + mana drain

Ladder: **multi-use confirmed; quadratic candidate (blocked on Synthesis implicit availability)**.

---

## Build 4 — Mind of the Council Mana-Burner (mana as fuel, damage and buffer)

Status: **VALIDATED** (bow version; a claw-delivery variant with Hand of Wisdom and Action also validated). Ascendancy: UNKNOWN.

Central interaction: the helmet makes mana a burning fuel — attack skills add lightning equal to 6% of *maximum* mana, each attack drains 3% of mana, and 30% of lightning damage taken is absorbed by mana first. With the amulet adding chaos per 100 maximum mana, the same pool pays for damage twice and tanks lightning.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | **Whispers of Infinity** (available) | **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana**; (60-40)% reduced maximum Mana; (10-15)% faster start of Energy Shield Recharge; **Skills Cost Energy Shield instead of Mana or Life** |
| Helmet | **Mind of the Council** (available) | **Attack Skills have Added Lightning Damage equal to 6% of maximum Mana**; **Lose 3% of Mana when you use an Attack Skill**; **30% of Lightning Damage is taken from Mana before Life**; +20% chance to be Shocked; +(15-20) to maximum Energy Shield; (230-260)% increased Evasion and Energy Shield |
| Weapon | **Doomfletch** (Bow, available) | Adds (12-16) to (20-24) Physical Damage; (10-14)% increased Attack Speed; 60% increased Mana Regeneration Rate |
| Boots | **Skyforth** (available) | **Stun Threshold is based on 500% of your Mana instead of Life**; +(60-120) to maximum Mana; 25% chance to gain a Power Charge on Critical Strike |
| Attack gem | **Tornado Shot** (level/quality UNKNOWN) | Bow-legal per validator weapon check |
| Passives | Tree (uncommitted) | mana generators as above |

**Why it works** — Maximum mana drives two additive damage streams (helmet lightning at 6% of max, amulet chaos per 100) while the helmet simultaneously burns mana per attack and shields lightning with mana — the pool is damage, fuel, and buffer at once. Skill costs land on Energy Shield (amulet), so mana regen (Doomfletch 60%, tree) refills the burn/tank budget rather than paying for skills. Note the amulet's own reduced maximum mana cuts this pool; mana generators must outpace it (KB-evidenced generators listed; the increased/reduced netting is engine-internal and not modeled by the validator).

**Evidence** —
`unique:533` → mods: AttackLightningDamageMaximumMana (6% max mana), LoseManaOnAttackSkill (3% per attack), LightningTakenFromMana (30%)
`unique:1461` → chaos/100 mana + ES-cost conversion
`unique:244` → mana regen rider; `unique:448` → mana-based stun threshold

Ladder: **multi-use** (damage ×2 + defense from one axis; no multiplicative interaction between the paths).

---

## Rejected combinations (KB-text reasons, not judgment)

- **Mask of the Stitched Demon** (`unique:779`): "Cannot Gain Energy Shield" + "Energy Shield starts at zero" directly conflict with Whispers' "Skills Cost Energy Shield instead of Mana or Life" — no ES can ever be available to pay costs. Also carries "Intelligence provides no inherent bonus to Maximum Mana" (`stat:gain_no_maximum_mana_from_intelligence`, `rule_negated_by` on `rule:intelligence_mana`) — kills the Int→mana generator.
- **Indigon** (`unique:748`): both scaling mods accrue on *mana spent recently* ("(50-60)% increased Cost of Skills for each 200 total Mana Spent Recently", "(20-25)% increased Spell Damage for each 200 total Mana you have Spent Recently, up to 2000%"). Under Whispers' ES-cost conversion skills spend no mana, so the accrual never advances (semantic inference from the two mod texts; flagged as inference, not a validator result).
- **Omeyocan inside Build 3**: kept as a validated *alternative*, with the drain/onslaught tension flagged in the sheet.

## Architecture subgraph (roles)

- **seed**: `unique:1461` Whispers of Infinity — consumer of maximum mana (added chaos), enabler (ES-cost conversion), in all four builds.
- **scaling axis**: X=Intelligence (Builds 1-2; generator via `rule:intelligence_mana` into mana), X=Maximum mana (Builds 3-4; generators: rule + passives + flat mods).
- **consumers/converters**: Crown of Eyes (spell→attack 150%), Whispering Ice (Int→spell dmg), HoWA (Int→added lightning), KB-of-Clustering / PS-of-Archmage (mana→added), Mind of the Council (mana→lightning + burn + buffer), Heavy Strike of Trarthus (Int→double damage), Synthesis implicits (mana/Int→increased, carrier-less).
- **defense**: Skyforth (mana→stun threshold), Omeyocan (mana→evasion), MotC mana-buffer, ES-recharge implicit on the seed.
- **axis re-anchoring**: none — the seed's own mod anchors mana; Int enters as the upstream generator (rule) rather than replacing the axis.

## Sweep log

1. Seed mods → axes (max mana, ES-cost, ES-recharge); per-mana chaos mod exclusive to the seed; ES-cost mod exclusive to the seed.
2. Mana consumer sweep (`maximum_mana` resolve, 66 stats) → attack consumers (KB/PS gems, Synthesis implicit, MotC mod), defense consumers (Skyforth, Omeyocan), rule-negation stat; Int family sweep (45 mods) → per-Int attack/spell/crit/defense mods.
3. Bridge sweep → `mechanic:applies_to_spell_damage_applies_to_attacks`, operand stats both sides, 150% variant ↔ Crown of Eyes, wand variant carrierless; keystone uniques' full mod lists; generator counts (89/123/11/235).
4. Anti-synergy sweep → MotSD conflict, Indigon conflict, "no mana from Int" negation, missing-mana consumers (1 mod, defensive only — no damage-per-missing-mana architecture exists in the KB).
5. Validation sweep — four build states through `validate_build`; weapon contexts fixed (staff/claw/wand/bow); claw and bow alternatives probed. No new live nodes or edges; loop stopped at fixed point.

## API GAPs / recorded unknowns

- **Gem numeric values are not exposed** (`resolve`/`neighbour`/`carriers` return names + granted stat ids only): %-of-maximum-mana values on KB-of-Clustering / PS-of-Archmage, the `..._at_%_value` bridge percentage on every gem carrier, and Heavy Strike of Trarthus' double-damage numbers are UNKNOWN. Only value-bearing *mod text* on uniques/mods is available.
- **Gem availability is `null`** for all gems (no obtainability model) — validator treats gems outside its availability checks.
- **Synthesis implicit mods** (`SynthesisImplicitAttackDamagePerMana1/2`, `SynthesisImplicitDamagePerIntelligence1`) have **no carrier rows** — item availability cannot be established; the Build 3 quadratic stays a hypothesis.
- **`stat:additive_spell_damage_modifiers_apply_to_attack_damage_at_%_value_while_wielding_wand`** exists with zero carriers — true absence under `carriers()`.
- The seed's "(60-40)% reduced maximum Mana" is rendered exactly as returned (range direction unusual but not interpreted).
- Increased/reduced mana netting and cost-conversion order are engine-internal; not modeled by the validator (its `limitations` string applies to all VALID verdicts).
