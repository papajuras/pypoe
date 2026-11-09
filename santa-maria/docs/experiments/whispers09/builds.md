# whispers09 — build sheets

Eight architectures discovered around `unique:1461` Whispers of Infinity. Each sheet is one
validated (or explicitly partial) build state. Every modifier list is the complete association set
returned by `neighbour <unique> --depth 1`; nothing is added, dropped or paraphrased. Numbers are
the API's roll ranges — no roll was selected.

Legend: **bold** = the modifier(s) that establish this build's interaction. `VALIDATED` = passed
`validate_build` (slot occupancy, weapon configuration, gem supportability, ascendancy
composition, item availability) — no stronger claim than the validator makes.

---

## Build 1 — Pool-Transfiguration Multiplier

Maximum Mana is not just the seed's damage input: **mana and life *modifiers* are themselves
converted into damage** at 30% of their value, and the same helmet raises life, mana *and* global
Energy Shield at once. Mana investment therefore enters the damage calculation twice, life
investment a third time.

**VALIDATED** — status `valid`; availability `valid`; passive/ascendancy `valid`;
`gem:HeavyStrikeAltY` support chain `valid`, weapon restriction `valid` ("Staff is an allowed
weapon class").

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | **Whispers of Infinity** (available) | **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana** · (60-40)% reduced maximum Mana · (10-15)% faster start of Energy Shield Recharge · **Skills Cost Energy Shield instead of Mana or Life** |
| Helmet | **Crown of the Inward Eye** (available) | 333% increased Armour and Energy Shield · **(9-21)% increased maximum Life, Mana and Global Energy Shield** · **Transfiguration of Body** · **Transfiguration of Mind** · **Transfiguration of Soul** |
| Body Armour | Shroud of the Lightless (available) | Penetrate 4% Elemental Resistances per Abyss Jewel affecting you · 3% increased Maximum Life per Abyss Jewel affecting you · **3% increased Maximum Mana per Abyss Jewel affecting you** · 20% chance to Trigger Level 20 Shade Form when you Use a Socketed Skill · (160-180)% increased Evasion and Energy Shield |
| Ring (right slot) | Shavronne's Revelation (available) | +(60-75) to Intelligence · Left ring slot: Regenerate 40 Mana per Second · Left ring slot: +250 to maximum Energy Shield · Left ring slot: You cannot Recharge or Regenerate Energy Shield · Right ring slot: Regenerate 6% of Energy Shield per second · **Right ring slot: +250 to maximum Mana** · Right ring slot: You cannot Regenerate Mana |
| Ring | Perandus Signet (available) | 3% chance for Slain monsters to drop an additional Scroll of Wisdom · 2% increased Experience gain · **2% increased Intelligence for each Unique Item Equipped** · +(25-30) to maximum Mana · (45-65)% increased Mana Regeneration Rate |
| Weapon | Cane of Kulemak (available, Staff) | (60-90)% increased Unveiled Modifier magnitudes |
| Gem | **Heavy Strike of Trarthus** (gem, tag:attack) | grants `chance_to_deal_double_damage_%_per_10_intelligence` · `attack_speed_+%` · `damage_+%` · `active_skill_additive_spell_damage_modifiers_apply_to_attack_damage_at_%_value` · `trigger_level_20_bone_corpses_on_stun` · `quality_display_spell_damage_to_attack_damage_is_gem`. Weapon restriction `['Staff','Warstaff']` — satisfied by Cane of Kulemak |
| Ascendancy | Hierophant | Notable: **Divine Guidance** (`passive:AscendancyHeirophant7`, `ascendancy: Hierophant`) → `additive_mana_modifiers_apply_to_damage_at_30%_value` + `base_damage_removed_from_mana_before_life_%` + `maximum_mana_+%` |
| Tree | Energy Shield and Mana (`passive:energy_shield1631`) | `base_maximum_energy_shield`, `base_maximum_mana` |
| Tree | Spell Damage and Mana (`passive:spell_damage721`) | `base_maximum_mana`, `spell_damage_+%` |
| Tree | Mana (`passive:mana1647`) | `maximum_mana_+%` |
| Tree | Heart and Soul (`passive:life_mana_notable1638`, notable) | `maximum_life_+%`, `maximum_mana_+%` |

**Why it works.** Whispers of Infinity pays flat added attack chaos per 100 maximum Mana, so the
whole economy is "make the pool huge". Crown of the Inward Eye's Transfiguration of Mind makes
*additive mana modifiers* apply to damage at 30% of value, and Divine Guidance grants the same
bridge from the tree — so every `maximum_mana_+%` and flat mana source is simultaneously a pool
increase (→ seed chaos) and a damage modifier (→ 30% of its value as damage). Transfiguration of
Body does the same for life modifiers against attack damage, and the helmet's single
"increased maximum Life, Mana and Global Energy Shield" line is the shared input for all three
pools. Because the seed removes Mana and Life as skill costs, the ES half of that line is pure
sustain headroom rather than wasted budget.

**Evidence**
- Whispers of Infinity → `Added Attack Chaos Damage per 100 Maximum Mana` (prose only; 0 `modifier_grants_stat`)
- Crown of the Inward Eye "Transfiguration of Mind" → `stat:additive_mana_modifiers_apply_to_damage_at_30%_value`
- Crown of the Inward Eye "Transfiguration of Body" → `stat:additive_life_modifiers_apply_to_attack_damage_at_30%_value`
- Crown of the Inward Eye "Transfiguration of Soul" → `stat:additive_energy_shield_modifiers_apply_to_spell_damage_at_30%_value`
- Crown of the Inward Eye → `stat:maximum_life_mana_and_energy_shield_+%` (sole carrier)
- Divine Guidance → same mana→damage-30% bridge, from the tree
- Shroud of the Lightless → `stat:maximum_mana_+%_per_abyssal_jewel_affecting_you` (3% per abyss jewel)
- Shavronne's Revelation → `stat:local_right_ring_slot_maximum_mana` (sole carrier)

---

## Build 2 — Arcane Might: mana → spell damage % → attack damage %

Maximum Mana is spent twice on the *same* attack output: once as the seed's flat added chaos, and
once as spell damage % (Prodigal Perfection) which Crown of Eyes converts into attack damage %.
One investment, two damage paths of different mathematical kind.

**VALIDATED** — status `valid`; availability `valid`; passive/ascendancy `valid`;
`gem:HeavyStrikeAltY` `valid`, weapon restriction `valid` ("Staff is an allowed weapon class").

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | **Whispers of Infinity** (available) | **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana** · (60-40)% reduced maximum Mana · (10-15)% faster start of Energy Shield Recharge · **Skills Cost Energy Shield instead of Mana or Life** |
| Helmet | **Crown of Eyes** (available) | -30% to Fire Resistance · +(300-350) to Accuracy Rating · (0.4-0.8)% of Attack Damage Leeched as Life · (120-150)% increased Energy Shield · (0.2-0.4)% of Attack Damage Leeched as Mana · **Attacks have 150% Arcane Might** |
| Ring (right slot) | Shavronne's Revelation (available) | +(60-75) to Intelligence · Left ring slot: Regenerate 40 Mana per Second · Left ring slot: +250 to maximum Energy Shield · Left ring slot: You cannot Recharge or Regenerate Energy Shield · Right ring slot: Regenerate 6% of Energy Shield per second · **Right ring slot: +250 to maximum Mana** · Right ring slot: You cannot Regenerate Mana |
| Ring | Perandus Signet (available) | 3% chance for Slain monsters to drop an additional Scroll of Wisdom · 2% increased Experience gain · **2% increased Intelligence for each Unique Item Equipped** · +(25-30) to maximum Mana · (45-65)% increased Mana Regeneration Rate |
| Weapon | Cane of Kulemak (available, Staff) | (60-90)% increased Unveiled Modifier magnitudes |
| Gem | **Heavy Strike of Trarthus** (gem, tag:attack) | `chance_to_deal_double_damage_%_per_10_intelligence` · `active_skill_additive_spell_damage_modifiers_apply_to_attack_damage_at_%_value` · `attack_speed_+%` · `damage_+%` · `trigger_level_20_bone_corpses_on_stun`. Restriction `['Staff','Warstaff']` — satisfied |
| Ascendancy | Hierophant | Small node: Mana Regeneration, Mana (`passive:AscendancyHeirophant4_`) → `mana_regeneration_rate_+%`, `maximum_mana_+%` |
| Tree | **Prodigal Perfection** (`passive:mana_spell_damage_notable2609`, notable) | `spell_damage_+%_per_100_maximum_mana_up_to_60%` · `maximum_mana_+%` |
| Tree | Spell Damage and Mana (`passive:spell_damage721`) | `base_maximum_mana`, `spell_damage_+%` |
| Tree | Mana (`passive:mana1647`) | `maximum_mana_+%` |
| Tree | Energy Shield and Mana (`passive:energy_shield1631`) | `base_maximum_energy_shield`, `base_maximum_mana` |

**Why it works.** Prodigal Perfection is the only carrier in the KB of
`spell_damage_+%_per_100_maximum_mana_up_to_60%`, and it also grants `maximum_mana_+%`, so it is
self-feeding. Crown of Eyes is the only carrier of the `..._at_150%_value` variant of the
spell→attack bridge; the bridge's declared operands are `spell_damage_+%` and `attack_damage_+%`,
so the pool that Whispers of Infinity wants for flat chaos is the same pool that feeds a
*multiplicative* attack damage channel. Heavy Strike of Trarthus carries the bridge gem-side and
adds its own Intelligence→double-damage line, so the attribute, the pool and the output are all
on one chain.

**Evidence**
- Prodigal Perfection → `stat:spell_damage_+%_per_100_maximum_mana_up_to_60%` (sole carrier) + `stat:maximum_mana_+%`
- Crown of Eyes "Attacks have 150% Arcane Might" → `stat:additive_spell_damage_modifiers_apply_to_attack_damage_at_150%_value`
- `stat:additive_spell_damage_modifiers_apply_to_attack_damage` → operands `stat:attack_damage_+%` (input) + `stat:spell_damage_+%` (input)
- 15 attack gems carry `active_skill_..._at_%_value`, incl. Heavy Strike of Trarthus, Kinetic family, Power Siphon family, Somatic Shell
- Heavy Strike of Trarthus → `stat:chance_to_deal_double_damage_%_per_10_intelligence` (sole carrier)

**Hypothesis, not fact (API gap 5):** the bridge's declared operand is the generic
`stat:spell_damage_+%`; Prodigal Perfection grants `stat:spell_damage_+%_per_100_maximum_mana_up_to_60%`,
a different stat id. The API does not say whether the latter is caught by the former. Recorded as
**UNKNOWN**.

---

## Build 3 — Chaos-poison feedback loop

The seed's damage type is its own delivery system. Added attack chaos applies poison, poison
stacks multiply hit damage (which is where the seed's chaos sits) *and* unlock a further chunk of
added chaos from the weapon — a loop that closes on itself.

**VALIDATED** — status `valid`; availability `valid`; passive/ascendancy `valid`;
`gem:ViperStrike` support chain `valid`, weapon restriction `valid` ("Claw is an allowed weapon
class").

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | **Whispers of Infinity** (available) | **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana** · (60-40)% reduced maximum Mana · (10-15)% faster start of Energy Shield Recharge · **Skills Cost Energy Shield instead of Mana or Life** |
| Weapon (Claw) | **The Wasp Nest** (available) | **Attacks with this Weapon deal 80 to 120 added Chaos Damage against Enemies affected by at least 5 Poisons** · (20-25)% increased Critical Strike Chance · +(330-350) to Accuracy Rating · (20-25)% increased Attack Speed · (150-170)% increased Physical Damage |
| Gloves | Snakebite (available) | 6% increased Accuracy Rating per Frenzy Charge · **Attacks have 60% chance to Poison while at maximum Frenzy Charges** · 2% increased Attack Speed per Frenzy Charge · +5% to Damage over Time Multiplier for Poison per Frenzy Charge · 10% reduced Frenzy Charge Duration per Frenzy Charge · +(60-70) to maximum Life · (150-180)% increased Evasion Rating |
| Helmet | Crown of the Inward Eye (available) | 333% increased Armour and Energy Shield · **(9-21)% increased maximum Life, Mana and Global Energy Shield** · Transfiguration of Body · **Transfiguration of Mind** · Transfiguration of Soul |
| Ring (right slot) | Shavronne's Revelation (available) | +(60-75) to Intelligence · Left ring slot: Regenerate 40 Mana per Second · Left ring slot: +250 to maximum Energy Shield · Left ring slot: You cannot Recharge or Regenerate Energy Shield · Right ring slot: Regenerate 6% of Energy Shield per second · **Right ring slot: +250 to maximum Mana** · Right ring slot: You cannot Regenerate Mana |
| Ring | Perandus Signet (available) | 3% chance for Slain monsters to drop an additional Scroll of Wisdom · 2% increased Experience gain · **2% increased Intelligence for each Unique Item Equipped** · +(25-30) to maximum Mana · (45-65)% increased Mana Regeneration Rate |
| Gem | **Viper Strike** (`gem:ViperStrike`, tags: attack, chaos) | **`skill_physical_damage_%_to_convert_to_chaos`** · **`hit_and_poison_damage_+%_per_poison_on_enemy`** · `base_chance_to_poison_on_hit_%` · `attack_damage_+%_per_frenzy_charge` · `skill_double_hits_when_dual_wielding` · `critical_strike_chance_+%` · `damage_+%` · `skill_effect_duration_+%` · `poison_duration_is_skill_duration` · `viper_strike_dual_wield_damage_+%_final` · `viper_strike_dual_wield_attack_speed_+%_final`. Restriction `['Claw','Dagger','One Hand Sword','Thrusting One Hand Sword','Two Hand Sword','Rune Dagger']` — satisfied by Claw |
| Ascendancy | Hierophant | Small node: Mana Regeneration, Mana (`passive:AscendancyHeirophant4_`) → `mana_regeneration_rate_+%`, `maximum_mana_+%` |
| Tree | Toxic Strikes (`passive:poison_notable2185`, notable) | `base_chance_to_poison_on_hit_%`, `poison_dot_multiplier_+` |
| Tree | Poison Damage and Chance (`passive:attack_poison2350`) | `chance_to_poison_on_hit_with_attacks_%`, `poison_dot_multiplier_+` |
| Tree | Claw Ailment Damage and Poison Chance (`passive:claw_attack_speed1813`) | `chance_to_poison_on_hit_with_attacks_%`, `claw_ailment_damage_+%` |
| Tree | Mana (`passive:mana1647`) | `maximum_mana_+%` |
| Tree | Energy Shield and Mana (`passive:energy_shield1631`) | `base_maximum_energy_shield`, `base_maximum_mana` |

**Why it works.** The seed deals added *chaos*, and Viper Strike is the one gem in this run that
converts its own physical damage to chaos (`skill_physical_damage_%_to_convert_to_chaos`, tag
`chaos`), so the whole hit is chaos and the seed's added chaos sits on top of it without a second
damage type. `hit_and_poison_damage_+%_per_poison_on_enemy` scales hit damage — the exact channel
the seed's added chaos occupies — by poison count, and The Wasp Nest adds a second block of chaos
only once five poisons are up, so each poison application raises the chaos that produces the next
one. `chaos_damage_chance_to_poison_%` ("Your Chaos Damage has 60% chance to Poison Enemies") would
be the strongest poison enabler and is the sole stat of The Consuming Dark, which the single-weapon
slot model cannot hold alongside The Wasp Nest, so poison application is taken from the gem and
tree instead. Snakebite supplies the frenzy-charge dimension (poison chance, attack speed and poison
DoT multiplier per charge) — which also matches the gem's own `attack_damage_+%_per_frenzy_charge`.

**Evidence**
- The Wasp Nest "…added Chaos Damage against Enemies affected by at least 5 Poisons" → `stat:maximum_added_chaos_damage_vs_enemies_with_5+_poisons` (sole carrier)
- Viper Strike → `stat:hit_and_poison_damage_+%_per_poison_on_enemy` (shared with Viper Strike of the Mamba)
- Viper Strike → `stat:base_chance_to_poison_on_hit_%` · `stat:skill_physical_damage_%_to_convert_to_chaos` · `gem_has_tag tag:chaos`
- Snakebite "Attacks have 60% chance to Poison while at maximum Frenzy Charges" → `stat:attacks_chance_to_poison_%_on_max_frenzy_charges` (sole carrier)
- The Consuming Dark → `stat:chaos_damage_chance_to_poison_%` (sole carrier) — **not equipped**: slot model has one weapon slot

**API gap 6:** the KB does not state whether the seed's added attack chaos counts as main-hand
chaos, so `maximum_poison_damage_to_deal_per_minute_from_main_hand_chaos_damage` was not used as
an edge.

---

## Build 4 — Chaos-shock self-shock loop

Same seed, opposite ailment: shock. Chaos is the shock carrier, and the shock is *yours* — the
belt reflects shocks you cause back onto you, which keeps the "while Shocked" damage window open
permanently without any self-damage management.

**VALIDATED** — status `valid`; availability `valid`; passive/ascendancy `valid`;
`gem:Bladestorm` support chain `valid`, weapon restriction `valid` ("Two Hand Sword is an allowed
weapon class").

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | **Whispers of Infinity** (available) | **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana** · (60-40)% reduced maximum Mana · (10-15)% faster start of Energy Shield Recharge · **Skills Cost Energy Shield instead of Mana or Life** |
| Weapon (Two Hand Sword, base Infernal Sword) | **Echoforge** (available) | **Your Chaos Damage can Shock** · Deal no Physical or Elemental Damage · (-40-40)% increased Area of Effect for Attacks · 30% increased Chaos Damage · +(-200-200) to maximum Life · **Adds (600-650) to (750-800) Chaos Damage** · (-16-16)% increased Attack Speed |
| Belt | **Maligaro's Restraint** (available) | Adds 1 to (30-50) Lightning Damage to Attacks · **60% increased Damage while Shocked** · +(9-20) to maximum Energy Shield · 15% increased Movement Speed while Shocked · 100% increased Shock Duration on you · **Shocks you cause are reflected back to you** |
| Body Armour | **Inpulsa's Broken Heart** (available) | **(20-50)% increased Damage if you have Shocked an Enemy Recently** · (15-25)% increased Effect of Shock · Shocked Enemies you Kill Explode, dealing 5% of their Life as Lightning Damage which cannot Shock |
| Ring (right slot) | Shavronne's Revelation (available) | +(60-75) to Intelligence · Left ring slot: Regenerate 40 Mana per Second · Left ring slot: +250 to maximum Energy Shield · Left ring slot: You cannot Recharge or Regenerate Energy Shield · Right ring slot: Regenerate 6% of Energy Shield per second · **Right ring slot: +250 to maximum Mana** · Right ring slot: You cannot Regenerate Mana |
| Ring | Perandus Signet (available) | 3% chance for Slain monsters to drop an additional Scroll of Wisdom · 2% increased Experience gain · **2% increased Intelligence for each Unique Item Equipped** · +(25-30) to maximum Mana · (45-65)% increased Mana Regeneration Rate |
| Gem | Bladestorm (gem, tag:attack) | no weapon restrictions — validated against Echoforge's Two Hand Sword |
| Ascendancy | Hierophant | Small node: Mana Regeneration, Mana (`passive:AscendancyHeirophant4_`) → `mana_regeneration_rate_+%`, `maximum_mana_+%` |
| Tree | Static Blows (`passive:static_blows221`, notable) | `damage_+%_if_you_have_shocked_recently`, `lightning_ailment_duration_+%`, `lightning_ailment_effect_+%` |
| Tree | Sword Critical Strike Chance (`passive:sword_damage1069`) | `sword_critical_strike_chance_+%` |
| Tree | Sword Critical Strike Chance and Multiplier (`passive:sword_critical_chance1702`) | `sword_critical_strike_chance_+%`, `sword_critical_strike_multiplier_+` |
| Tree | Mana (`passive:mana1647`) | `maximum_mana_+%` |
| Tree | Energy Shield and Mana (`passive:energy_shield1631`) | `base_maximum_energy_shield`, `base_maximum_mana` |

**Why it works.** Echoforge is a pure-chaos weapon ("Deal no Physical or Elemental Damage") and is
the sole carrier pairing "Your Chaos Damage can Shock" with a large flat chaos base — the exact
damage type the seed amplifies, so shock application scales with the pool for free. Maligaro's
Restraint closes the loop: shocks you cause are reflected back to you, and "60% increased Damage
while Shocked" plus 100% increased shock duration turns that reflection into permanent uptime.
Inpulsa's Broken Heart and the Static Blows notable grant the *same* stat
(`damage_+%_if_you_have_shocked_recently`), which keys off a second, independent window — "Shocked
an Enemy Recently" rather than being Shocked — so the two keep two separate multipliers alive
while the belt's reflection supplies the uptime.

**Evidence**
- Echoforge "Your Chaos Damage can Shock" → `stat:chaos_damage_can_shock` (shared with Voltaxic Rift, `mod:MutatedUniqueHelmetDexInt4ChaosDamageCanShock`)
- Maligaro's Restraint "60% increased Damage while Shocked" → `stat:damage_+%_per_shock`
- Inpulsa's Broken Heart "(20-50)% increased Damage if you have Shocked an Enemy Recently" → `stat:damage_+%_if_you_have_shocked_recently`
- Static Blows (`passive:static_blows221`) → the same `stat:damage_+%_if_you_have_shocked_recently` + `lightning_ailment_duration_+%` + `lightning_ailment_effect_+%`
- `weapon_check gem:HeavyStrikeAltY` / `gem:Boneshatter` vs Echoforge → `invalid`; `gem:Bladestorm` vs Echoforge → `valid` ("Two Hand Sword is an allowed weapon class")

---

## Build 5 — Dual flat max-mana channel (wand burst)

Maximum Mana buys **two independent flat added-damage lines** on the same wand attack — the
seed's chaos and the gem's own physical-as-percent-of-mana — plus the gem's own spell→attack
bridge for the multiplier layer.

**VALIDATED** — status `valid`; availability `valid`; passive/ascendancy `valid`;
`gem:KineticBlastAltX` support chain `valid`, weapon restriction `valid` ("Wand is an allowed
weapon class").

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | **Whispers of Infinity** (available) | **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana** · (60-40)% reduced maximum Mana · (10-15)% faster start of Energy Shield Recharge · **Skills Cost Energy Shield instead of Mana or Life** |
| Helmet | **Crown of Eyes** (available) | -30% to Fire Resistance · +(300-350) to Accuracy Rating · (0.4-0.8)% of Attack Damage Leeched as Life · (120-150)% increased Energy Shield · (0.2-0.4)% of Attack Damage Leeched as Mana · **Attacks have 150% Arcane Might** |
| Weapon (Wand) | **Void Battery** (available) | (50-65)% increased Global Critical Strike Chance · (10-20)% increased Cast Speed · **+(100-120) to maximum Mana** · +1 to Maximum Power Charges · (10-15)% increased Spell Damage per Power Charge · (36-40)% increased Spell Damage · 50% reduced Spell Damage |
| Ring (right slot) | Shavronne's Revelation (available) | +(60-75) to Intelligence · Left ring slot: Regenerate 40 Mana per Second · Left ring slot: +250 to maximum Energy Shield · Left ring slot: You cannot Recharge or Regenerate Energy Shield · Right ring slot: Regenerate 6% of Energy Shield per second · **Right ring slot: +250 to maximum Mana** · Right ring slot: You cannot Regenerate Mana |
| Ring | Perandus Signet (available) | 3% chance for Slain monsters to drop an additional Scroll of Wisdom · 2% increased Experience gain · **2% increased Intelligence for each Unique Item Equipped** · +(25-30) to maximum Mana · (45-65)% increased Mana Regeneration Rate |
| Gem | **Kinetic Blast of Clustering** (gem, tags: attack, physical) | **added_physical_damage_to_attacks_equal_to_%_maximum_mana** · `active_skill_additive_spell_damage_modifiers_apply_to_attack_damage_at_%_value` · `cluster_burst_spawn_amount` · `kinetic_blast_modifiers_to_number_of_projectiles_instead_apply_to_number_of_clusters` · `skill_can_fire_wand_projectiles` · `projectiles_cannot_split` · `chance_to_double_stun_duration_%` · `base_stun_threshold_reduction_+%`. Restriction `['Wand']` — satisfied by Void Battery |
| Ascendancy | Hierophant | Small node: Mana Regeneration, Mana (`passive:AscendancyHeirophant4_`) → `mana_regeneration_rate_+%`, `maximum_mana_+%` |
| Tree | **Prodigal Perfection** (`passive:mana_spell_damage_notable2609`, notable) | `spell_damage_+%_per_100_maximum_mana_up_to_60%` · `maximum_mana_+%` |
| Tree | Spell Damage and Mana (`passive:spell_damage721`) | `base_maximum_mana`, `spell_damage_+%` |
| Tree | Mana (`passive:mana1647`) | `maximum_mana_+%` |
| Tree | Energy Shield and Mana (`passive:energy_shield1631`) | `base_maximum_energy_shield`, `base_maximum_mana` |

**Why it works.** Kinetic Blast of Clustering is the sole carrier in the KB of
`added_physical_damage_to_attacks_equal_to_%_maximum_mana`, so it adds a second *flat* per-pool
damage line on top of the seed's flat chaos rather than a third multiplier — the two added values
sum before any multiplier, and the cluster/statistics layer (`cluster_burst_spawn_amount`, the
"modifiers to number of projectiles instead apply to number of clusters" override) determines how
many times each sum is applied. The same gem also carries the spell→attack bridge, so the pool can
additionally feed the multiplier channel.

**Evidence**
- Kinetic Blast of Clustering → `stat:added_physical_damage_to_attacks_equal_to_%_maximum_mana` (sole carrier)
- Kinetic Blast of Clustering → `stat:active_skill_additive_spell_damage_modifiers_apply_to_attack_damage_at_%_value`
- Void Battery → `+(100-120) to maximum Mana`; `weapon_check gem:KineticBlastAltX` vs Void Battery → `valid` ("Wand is an allowed weapon class")

---

## Build 6 — Mana as lightning buffer, and mana as throughput

Two *different* max-mana consumers that are not damage multipliers: one adds a second damage type
proportional to the pool, the other multiplies how often the attack happens. The pool is also the
lightning damage buffer, so it is offense, throughput and defense at once.

**VALIDATED** — status `valid`; availability `valid`; passive/ascendancy `valid`;
`gem:BladefallAltZ` support chain `valid`, weapon restriction `valid` ("no weapon restrictions").

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | **Whispers of Infinity** (available) | **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana** · (60-40)% reduced maximum Mana · (10-15)% faster start of Energy Shield Recharge · **Skills Cost Energy Shield instead of Mana or Life** |
| Helmet | **Mind of the Council** (available) | **Attack Skills have Added Lightning Damage equal to 6% of maximum Mana** · +20% chance to be Shocked · +(15-20) to maximum Energy Shield · (230-260)% increased Evasion and Energy Shield · Lose 3% of Mana when you use an Attack Skill · **30% of Lightning Damage is taken from Mana before Life** |
| Body Armour | Shroud of the Lightless (available) | Penetrate 4% Elemental Resistances per Abyss Jewel affecting you · 3% increased Maximum Life per Abyss Jewel affecting you · **3% increased Maximum Mana per Abyss Jewel affecting you** · 20% chance to Trigger Level 20 Shade Form when you Use a Socketed Skill · (160-180)% increased Evasion and Energy Shield |
| Ring (right slot) | Shavronne's Revelation (available) | +(60-75) to Intelligence · Left ring slot: Regenerate 40 Mana per Second · Left ring slot: +250 to maximum Energy Shield · Left ring slot: You cannot Recharge or Regenerate Energy Shield · Right ring slot: Regenerate 6% of Energy Shield per second · **Right ring slot: +250 to maximum Mana** · Right ring slot: You cannot Regenerate Mana |
| Ring | Perandus Signet (available) | 3% chance for Slain monsters to drop an additional Scroll of Wisdom · 2% increased Experience gain · **2% increased Intelligence for each Unique Item Equipped** · +(25-30) to maximum Mana · (45-65)% increased Mana Regeneration Rate |
| Weapon | Cane of Kulemak (available, Staff) | (60-90)% increased Unveiled Modifier magnitudes |
| Gem | **Bladefall of Trarthus** (gem, tag:physical) | **bladefall_volley_frequency_+%_per_100_maximum_mana** · `bladefall_base_volley_frequency_ms` · `bladefall_create_X_lingering_blades_per_volley` · `maximum_number_of_blades_left_in_ground` · `base_skill_area_of_effect_+%` · `critical_strike_chance_+%` · `damage_+%` · `is_area_damage`. No weapon restrictions |
| Ascendancy | Hierophant | Small node: Mana Regeneration, Mana (`passive:AscendancyHeirophant4_`) → `mana_regeneration_rate_+%`, `maximum_mana_+%` |
| Tree | Spell Damage and Mana (`passive:spell_damage721`) | `base_maximum_mana`, `spell_damage_+%` |
| Tree | Mana (`passive:mana1647`) | `maximum_mana_+%` |
| Tree | Energy Shield and Mana (`passive:energy_shield1631`) | `base_maximum_energy_shield`, `base_maximum_mana` |
| Tree | Heart and Soul (`passive:life_mana_notable1638`, notable) | `maximum_life_+%`, `maximum_mana_+%` |

**Why it works.** Mind of the Council is the sole carrier of
`attack_skills_have_added_lightning_damage_equal_to_%_of_maximum_mana` on a helmet, so it turns the
pool into a *second* flat added-damage type; Bladefall of Trarthus is the sole carrier of
`bladefall_volley_frequency_+%_per_100_maximum_mana`, so the same pool raises how often the attack
lands. Because the seed removes Mana as a skill cost, "30% of Lightning Damage is taken from Mana
before Life" turns the damage pool into a lightning buffer — the pool is simultaneously the source
of the added lightning, the multiplier on hit count, and the pool absorbing the retaliation.

**Evidence**
- Mind of the Council → `stat:attack_skills_have_added_lightning_damage_equal_to_%_of_maximum_mana` (sole carrier of the 6% roll)
- Mind of the Council → `stat:base_damage_removed_from_mana_before_life_%`
- Bladefall of Trarthus → `stat:bladefall_volley_frequency_+%_per_100_maximum_mana` (sole carrier)

---

## Build 7 — Abyssal-jewel quantity: one investment, three outputs

The scaling axis is *item quantity*, not attributes or passives. Each abyss jewel affecting you
raises maximum Mana, elemental penetration and maximum Life at once, and the mana raise feeds the
seed. Nothing else in this run scales on a count you can buy directly.

**VALIDATED on the unique / weapon / gem / ascendancy / availability layers** — status `valid`
with the influenced-rare declaration omitted. With the abyss-jewel declaration included the build
is **`unknown`**, reason `influence: no influence_tags on item_class: 'AbyssJewel'` — a
`validate_build` coverage gap, not a build defect (see API gap 4).

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | **Whispers of Infinity** (available) | **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana** · (60-40)% reduced maximum Mana · (10-15)% faster start of Energy Shield Recharge · **Skills Cost Energy Shield instead of Mana or Life** |
| Helmet | **Crown of the Inward Eye** (available) | 333% increased Armour and Energy Shield · **(9-21)% increased maximum Life, Mana and Global Energy Shield** · **Transfiguration of Body** · **Transfiguration of Mind** · Transfiguration of Soul |
| Body Armour | **Shroud of the Lightless** (available) | **Penetrate 4% Elemental Resistances per Abyss Jewel affecting you** · 3% increased Maximum Life per Abyss Jewel affecting you · **3% increased Maximum Mana per Abyss Jewel affecting you** · 20% chance to Trigger Level 20 Shade Form when you Use a Socketed Skill · (160-180)% increased Evasion and Energy Shield |
| Ring (right slot) | Shavronne's Revelation (available) | +(60-75) to Intelligence · Left ring slot: Regenerate 40 Mana per Second · Left ring slot: +250 to maximum Energy Shield · Left ring slot: You cannot Recharge or Regenerate Energy Shield · Right ring slot: Regenerate 6% of Energy Shield per second · **Right ring slot: +250 to maximum Mana** · Right ring slot: You cannot Regenerate Mana |
| Ring | Perandus Signet (available) | 3% chance for Slain monsters to drop an additional Scroll of Wisdom · 2% increased Experience gain · **2% increased Intelligence for each Unique Item Equipped** · +(25-30) to maximum Mana · (45-65)% increased Mana Regeneration Rate |
| Weapon | Cane of Kulemak (available, Staff) | (60-90)% increased Unveiled Modifier magnitudes |
| Gem | Heavy Strike of Trarthus (gem, tag:attack) | `chance_to_deal_double_damage_%_per_10_intelligence` · `active_skill_additive_spell_damage_modifiers_apply_to_attack_damage_at_%_value` · `attack_speed_+%` · `damage_+%` · `trigger_level_20_bone_corpses_on_stun`. Restriction `['Staff','Warstaff']` — satisfied |
| Ascendancy | Hierophant | Notable: **Divine Guidance** (`passive:AscendancyHeirophant7`) → `additive_mana_modifiers_apply_to_damage_at_30%_value` + `base_damage_removed_from_mana_before_life_%` + `maximum_mana_+%` |
| Tree | Energy Shield and Mana (`passive:energy_shield1631`) | `base_maximum_energy_shield`, `base_maximum_mana` |
| Tree | Mana (`passive:mana1647`) | `maximum_mana_+%` |
| Tree | Heart and Soul (`passive:life_mana_notable1638`, notable) | `maximum_life_+%`, `maximum_mana_+%` |
| Abyss Jewel | **influenced-rare declaration** (`item_class:AbyssJewel`) | `mod:IncreasedManaPerAbyssalJewelUnique__2` — "3% increased Maximum Mana per Abyss Jewel affecting you". **Influence validation: UNKNOWN** |

**Why it works.** Shroud of the Lightless makes a *count* (abyss jewels affecting you) the single
purchase that raises three different things at once. Mana feeds the seed's chaos directly, and it
is also an additive mana modifier, which Transfiguration of Mind and Divine Guidance convert into
30% of their value as damage — so a single jewel purchase pays into three separate damage
conversions. Elemental penetration rides the same counter, which matters because the seed's chaos
is resisted rather than reduced.

**Evidence**
- Shroud of the Lightless → `stat:maximum_mana_+%_per_abyssal_jewel_affecting_you` (3% roll, sole carrier)
- Shroud of the Lightless → `stat:penetrate_elemental_resistance_%_per_abyssal_jewel_affecting_you` (4% roll)
- Shroud of the Lightless → `stat:maximum_life_+%_per_abyssal_jewel_affecting_you` (3% roll)
- Crown of the Inward Eye "Transfiguration of Mind" + Divine Guidance → `stat:additive_mana_modifiers_apply_to_damage_at_30%_value`

**Distinctness note:** this build shares its helmet, weapon, gem and passives with Build 1 on
purpose — the *engine* differs (a per-jewel counter vs. the tree/item modifier pool), and the
difference is in the investment axis, not in the item list.

---

## Build 8 — Pool-gated speed loop

The pool is not spent on a second damage line at all: it is a **sustain budget**. Pool size decides
whether you stay off Low Mana, which unlocks a permanent speed buff, and the extra hits from that
speed refill the pool. Damage per hit stays exactly what Whispers of Infinity gives.

**VALIDATED on the unique / weapon / gem / ascendancy / availability layers** — status `valid`
with the influenced-rare declaration omitted. With it included the build is **`unknown`**, reason
`influence: modifier carries no influence` for `mod:ManaGainPerTargetInfluenceMaven` — a
`validate_build` coverage gap (API gap 4).

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | **Whispers of Infinity** (available) | **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana** · (60-40)% reduced maximum Mana · (10-15)% faster start of Energy Shield Recharge · **Skills Cost Energy Shield instead of Mana or Life** |
| Boots | **Omeyocan** (available) | **20% increased Evasion Rating per 500 Maximum Mana** · Lose 7% of Mana per Second · **(15-20)% increased maximum Mana** · **You have Onslaught while not on Low Mana** |
| Helmet | Crown of Eyes (available) | -30% to Fire Resistance · +(300-350) to Accuracy Rating · (0.4-0.8)% of Attack Damage Leeched as Life · (120-150)% increased Energy Shield · (0.2-0.4)% of Attack Damage Leeched as Mana · **Attacks have 150% Arcane Might** |
| Ring (right slot) | Shavronne's Revelation (available) | +(60-75) to Intelligence · Left ring slot: Regenerate 40 Mana per Second · Left ring slot: +250 to maximum Energy Shield · Left ring slot: You cannot Recharge or Regenerate Energy Shield · Right ring slot: Regenerate 6% of Energy Shield per second · **Right ring slot: +250 to maximum Mana** · Right ring slot: You cannot Regenerate Mana |
| Ring | Perandus Signet (available) | 3% chance for Slain monsters to drop an additional Scroll of Wisdom · 2% increased Experience gain · **2% increased Intelligence for each Unique Item Equipped** · +(25-30) to maximum Mana · (45-65)% increased Mana Regeneration Rate |
| Weapon | Cane of Kulemak (available, Staff) | (60-90)% increased Unveiled Modifier magnitudes |
| Gem | Boneshatter (gem, tag:attack) | restriction `['One Hand Axe','One Hand Mace','Sceptre','Staff','Two Hand Axe','Two Hand Mace','Warstaff']` — satisfied by Cane of Kulemak |
| Gloves | **influenced-rare declaration** | `mod:ManaGainPerTargetInfluenceMaven` — "Gain (3-5) Mana per Enemy Hit with Attacks" + "(10-20)% increased Attack Speed while not on Low Mana". **Influence validation: UNKNOWN** |
| Ascendancy | Hierophant | Small node: Mana Regeneration, Mana (`passive:AscendancyHeirophant4_`) → `mana_regeneration_rate_+%`, `maximum_mana_+%` |
| Tree | Spell Damage and Mana (`passive:spell_damage721`) | `base_maximum_mana`, `spell_damage_+%` |
| Tree | Mana (`passive:mana1647`) | `maximum_mana_+%` |
| Tree | Energy Shield and Mana (`passive:energy_shield1631`) | `base_maximum_energy_shield`, `base_maximum_mana` |

**Why it works.** Two independent KB facts close a loop on the pool itself:
`stat:attack_speed_+%_while_not_on_low_mana` and `stat:mana_gain_per_target` are granted by the same
modifier ("Gain (3-5) Mana per Enemy Hit with Attacks" + "(10-20)% increased Attack Speed while not
on Low Mana"), so more hits per second refuel the resource that buys more hits per second. Omeyocan
expresses the same threshold as a *permanent buff* instead of a speed line —
`stat:gain_onslaught_while_not_on_low_mana` — and adds a third max-mana consumer, "20% increased
Evasion Rating per 500 Maximum Mana", which is the pool paying for survival instead of damage.
Because the seed removes Mana as a skill cost, the pool is never drained by skills and the Onslaught
window is not interrupted by casting.

**Evidence**
- `mod:ManaGainPerTargetInfluenceMaven` → `stat:attack_speed_+%_while_not_on_low_mana` + `stat:mana_gain_per_target`
- Omeyocan "You have Onslaught while not on Low Mana" → `stat:gain_onslaught_while_not_on_low_mana` (a distinct stat from the attack-speed one above)
- Omeyocan "20% increased Evasion Rating per 500 Maximum Mana" → `stat:evasion_rating_+%_per_500_maximum_mana` (sole carrier, shared with a Divergent variant)

---

## Rejected / not proposed

- **Minion architecture** — no minion edge on the seed's modifier; whether the seed's added chaos
  reaches minion attacks is UNKNOWN (API gap 7). Not proposed.
- **Dual-wield poison (The Consuming Dark + The Wasp Nest)** — the richest chaos→poison pairing
  (`chaos_damage_chance_to_poison_%` is The Consuming Dark's sole stat) but the slot model has a
  single `weapon` slot, so it is `invalid: capacity 1 exceeded`. Recorded, not rendered.
- **Mana → Energy Shield as a named engine** — `mod:ClarityManaAddedAsEnergyShield` ("Gain (6-10)%
  of Maximum Mana as Extra Maximum Energy Shield while affected by Clarity") is the only mana→ES
  conversion in the KB and has **0 unique carriers**. No build was built on it.
- **Flat mana per Intelligence as a named engine** — `stat:maximum_mana_+_per_2_intelligence` has
  two modifier carriers and **0 unique carriers**; with no evidenced inherent int→Mana edge
  (API gap 1) this run does not claim int scales the pool.