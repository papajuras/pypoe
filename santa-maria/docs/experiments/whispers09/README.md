# whispers09 — Whispers of Infinity architecture discovery

Run date: 2026-10-06. Clean slate: no prior `whispersNN` run was read, evaluated or reused.
All facts below come from the public Research API only
(`phase8_research.resolve` / `phase8_research.carriers`, `phase6_api.get_neighbour`,
`phase7_build_validity.validate_build`, `phase7_build_feasibility.slot_check` / `weapon_check`).
Nothing is filled in from prior knowledge; gaps are labelled as such.

## Seed

`resolve "Whispers of Infinity" --type UniqueItem` → exactly one hit:

| Field | Value |
| ----- | ----- |
| Node | `unique:1461` |
| Class | Amulet (`item_class:Amulet`) |
| Availability | available |

Four modifiers (`neighbour unique:1461 --depth 1`), each **sole-carrier** — `carriers` on each
modifier returns `unique_modifier_association: 1` and every other edge type 0:

| Modifier text | Sole carrier |
| ------------- | ------------ |
| **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana** | Whispers of Infinity |
| (60-40)% reduced maximum Mana | Whispers of Infinity |
| (10-15)% faster start of Energy Shield Recharge | Whispers of Infinity |
| Skills Cost Energy Shield instead of Mana or Life | Whispers of Infinity |

**Load-bearing fact:** `carriers mod:AttacksGainMinMaxAddedChaosDamageBasedOnManaUnique__1`
reports `modifier_grants_stat: 0`. The seed's damage scaling has **no stat node** — it is prose
only. It is therefore also *invisible* to every stat-level mechanic probe in this run; it can only
be reached through `resolve` on its text and its unique's association edge.

Consequence for every architecture below: the seed pays **flat added chaos per attack hit** as a
function of **maximum Mana**, and it *removes* Mana/Life as a skill cost, so Mana becomes a
damage-only pool and **Energy Shield becomes the mandatory spendable pool** in all of them.

## Max-Mana consumer census

`resolve "<substring>_maximum_mana" --type Stat` returns 65 stat nodes. Every one with a real
carrier set, with its carrier census (`carriers stat:<id>`):

| Max-Mana consumer stat | Carriers |
| ---------------------- | -------- |
| `attack_skills_have_added_lightning_damage_equal_to_%_of_maximum_mana` | Mind of the Council (6% of max mana), a Divergent variant, Power Siphon of the Archmage (gem) |
| `skill_has_added_lightning_damage_equal_to_%_of_maximum_mana` | Mana-Infused Staff (gem) |
| `added_physical_damage_to_attacks_equal_to_%_maximum_mana` | Kinetic Blast of Clustering (gem) |
| `bladefall_volley_frequency_+%_per_100_maximum_mana` | Bladefall of Trarthus (gem) |
| `spell_damage_+%_per_100_maximum_mana_up_to_60%` | Prodigal Perfection (passive notable) |
| `evasion_rating_+%_per_500_maximum_mana` | Omeyocan (+ Divergent variant) |
| `attacks_with_this_weapon_maximum_mana_%_to_add_as_fire_damage` | `mod:VillageAttackFireDamageMaximumMana` (0 unique carriers) |
| `maximum_mana_%_to_add_to_energy_shield_while_affected_by_clarity` | `mod:ClarityManaAddedAsEnergyShield` (0 unique carriers) |
| `maximum_mana_+%_per_abyssal_jewel_affecting_you` | Shroud of the Lightless (3% per abyss jewel) |
| `maximum_mana_+_per_2_intelligence` | `mod:GainManaPer2IntelligenceUnique_1`, `mod:Haunted` — **0 unique carriers** |
| `local_right_ring_slot_maximum_mana` | Shavronne's Revelation (+250) |
| `maximum_mana_+%_and_cold_resistance_-%` | Glimpse of Chaos |
| `maximum_mana_+%_per_2%_spell_block_chance` | `mod:IncreasedManaPerSpellBlockChanceUnique__1` — 0 unique carriers |
| `maximum_mana_+_per_empty_blue_socket` | `mod:IncreasedManaEmptyBlueSocketUnique__1` — 0 unique carriers |
| `base_maximum_mana_per_green_socket_on_item` | `mod:ManaPerGreenSocket`, `mod:ManaPerGreenSocketUniqueRing39` — 0 unique carriers |
| `local_affliction_jewel_small_nodes_grant_maximum_mana` | Beryl / Cobalt / Azure / Sapphire / Cerulean jewel mods (+2…+16 mana per added small passive) |
| `local_unique_jewel_maximum_mana_+_per_10_dex_unallocated_in_radius` | `mod:FlatManaPerUnallocatedDexterityJewelUnique__1` (+15 per 10 **unallocated** dex) — 0 unique carriers |
| `local_unique_jewel_passives_in_radius_grant_base_maximum_mana` | `mod:UniqueJewelNodeIncreasedManaUnique__1` (+5 base mana per radius passive) — 0 unique carriers |
| `attack_damage_+%_per_500_maximum_mana` | **0 carriers** |
| `spell_damage_+%_per_500_maximum_mana` | **0 carriers** |
| `armour_+_per_10_unreserved_max_mana` | **0 carriers** |
| `maximum_mana_%_to_convert_to_armour_at_doubled_value` | **0 carriers** |
| `local_left_ring_slot_maximum_mana` / `maximum_mana_per_honoured_mind_tattoo_allocated` | **0 carriers** |

`stat:maximum_mana` and `stat:maximum_mana_+%` carry no `attribute_grants_stat` edge. See gaps.

## Max-Mana producer census

`carriers stat:maximum_mana_+%` → 150 carriers (78 modifiers, 72 passives), of which 9 are
alternate-ascendancy nodes suppressed by default (`meta.excluded_alternate_ascendancies: 9` —
suppression reported, never read as absence). Notable named producers:

- Items: Omeyocan "(15-20)% increased maximum Mana"; Crown of the Inward Eye
  "(9-21)% increased maximum Life, Mana and Global Energy Shield"; Glimpse of Chaos
  "(30-40)% increased maximum Mana and reduced Cold Resistance"; Perandus Signet "+(25-30) to
  maximum Mana"; Shavronne's Revelation "Right ring slot: +250 to maximum Mana"; Void Battery
  "+(100-120) to maximum Mana"; Shroud of the Lightless "3% increased Maximum Mana per Abyss
  Jewel affecting you"; `mod:MaximumManaIncreasePercent2ShaperItemsUnique__1` "(10-15)% increased
  maximum Mana if 2 Shaper Items are Equipped" (0 unique carriers).
- Passives: Divine Guidance (Hierophant), Prodigal Perfection, Heart and Soul, Mana Flows,
  Soul Siphon, Arcane Will, Arcane Chemistry, Arcane Capacitor, Mana Flows, Dynamo,
  Battle Rouse, Revelry, Thrill Killer, Mystic Bulwark, Righteous Decree, Druidic Rite,
  Sharp Intellect, Arcane Surge notables, and ~60 small "Mana" / "Mana and …" nodes.

## Bridge mechanics (stat_mechanic family)

`neighbour` on the mechanic ids gives the operand/variant structure:

| Mechanic | Operands (both sides) | Variants / carriers |
| -------- | ---------------------- | ------------------- |
| `stat:additive_spell_damage_modifiers_apply_to_attack_damage` | `attack_damage_+%`, `spell_damage_+%` | `..._at_%_value` (15 attack gems: Kinetic family, Power Siphon family, Heavy Strike of Trarthus, Somatic Shell), `..._at_150%_value` (**Crown of Eyes** "Attacks have 150% Arcane Might"), `..._at_%_value_while_wielding_wand`, `..._to_retaliation_attack_damage_at_%_value` |
| `stat:additive_mana_modifiers_apply_to_damage` (via `_at_30%_value`) | — (no operand edges returned) | Crown of the Inward Eye "Transfiguration of Mind", `mod:TransfigurationOfMindUnique__1` + Divergent variant, Divine Guidance, `passive:blight_special_notable9` (display name "Crusader") |
| `stat:additive_energy_shield_modifiers_apply_to_spell_damage_at_30%_value` | — | Crown of the Inward Eye "Transfiguration of Soul" + Divergent, `Passive:Tranquility` |
| `stat:additive_life_modifiers_apply_to_attack_damage_at_30%_value` | — | Crown of the Inward Eye "Transfiguration of Body" + Divergent, `Passive:Tenacity` |
| `stat:additive_mana_modifiers_apply_to_shock_effect_at_30%_value` | — | **0 carriers** — there is no mana→shock bridge in the KB |

`DivergentSpellDamageModifiersApplyToAttackDamageUniqueHelmetInt7` ("Attacks have 100% Arcane
Might") and `mod:MaximumManaUberMaven` ("(12-15)% increased maximum Mana / Transfiguration of
Mind") exist as modifier nodes; both return **0 unique carriers**.

## Chaos as the seed's damage type — carrier census

Because the seed is *added attack chaos*, every chaos-specific consumer is a second-order
candidate. All verified:

| Modifier text | Unique carrier | Class |
| ------------- | -------------- | ----- |
| Your Chaos Damage has 60% chance to Poison Enemies | The Consuming Dark | Dagger |
| Your Chaos Damage can Shock | Echoforge | Sword (2H, base Infernal Sword) |
| Your Chaos Damage can Shock | Voltaxic Rift | Bow |
| Chaos Damage can Ignite, Chill and Shock | Zerphi's Heart | Amulet (conflicts with the seed) |
| Attacks with this Weapon deal 80 to 120 added Chaos Damage against Enemies affected by at least 5 Poisons | The Wasp Nest | Claw |
| 60% increased Damage while Shocked (+ "Shocks you cause are reflected back to you") | Maligaro's Restraint | Belt |
| (20-50)% increased Damage if you have Shocked an Enemy Recently | Inpulsa's Broken Heart | Body Armour |
| 20% increased Evasion Rating per 500 Maximum Mana (+ "You have Onslaught while not on Low Mana") | Omeyocan | Boots |
| 2% increased Intelligence for each Unique Item Equipped | Perandus Signet | Ring |
| +20% chance to be Shocked + "30% of Lightning Damage is taken from Mana before Life" | Mind of the Council | Helmet |
| Attacks have 60% chance to Poison while at maximum Frenzy Charges | Snakebite | Gloves |
| Your Chaos Damage can Shock | `mod:MutatedUniqueHelmetDexInt4ChaosDamageCanShock` — 0 unique carriers | — |

Support-level poison stats confirmed: `hit_and_poison_damage_+%_per_poison_on_enemy` ←
Viper Strike / Viper Strike of the Mamba; `base_chance_to_poison_on_hit_%` ← 13 gems incl.
Viper Strike; `chance_to_poison_on_hit_with_attacks_%` ← 2 mods + 7 passives (Claw, Dagger,
Assassin and generic poison nodes).

One further chaos-shape fact, load-bearing for A3: `gem:ViperStrike` grants
`stat:skill_physical_damage_%_to_convert_to_chaos` and carries `gem_has_tag tag:chaos`, i.e. it is
the only attack in this run whose *own* base damage is already chaos, so the seed's added chaos
lands on a single-damage-type hit rather than sharing with a second type.

## Distinct architectures found

Eight, each with a different **engine** (what converts the mana investment into output), not a
different item on the same engine. Full sheets in [`builds.md`](builds.md).

| # | Architecture | Engine (the conversion) | Order | Validator |
| - | ------------ | ---------------------- | ----- | --------- |
| A1 | Pool-Transfiguration Multiplier | mana/life **modifiers** → damage at 30% of value (Transfiguration of Mind + Divine Guidance), on top of mana→seed chaos | 3rd | VALID |
| A2 | Arcane Might spell→attack feedback | max mana → **spell damage %** → (150% Arcane Might) → attack damage %, *plus* max mana → seed chaos | 2nd | VALID |
| A3 | Chaos-poison feedback loop | gem converts its own hits to chaos so the seed's added chaos is the only added type; poison count multiplies **hit** damage (Viper Strike) and unlocks The Wasp Nest's extra added chaos | 2nd + self-reinforcing | VALID |
| A4 | Chaos-shock self-shock loop | seed chaos → can shock (Echoforge) → reflected shock keeps you Shocked → 60% damage while Shocked | 2nd + self-reinforcing | VALID |
| A5 | Dual flat max-mana channel (wand burst) | max mana → **added physical** to attacks (Kinetic Blast of Clustering) alongside the seed's added chaos, plus the gem's own spell→attack bridge | 2nd | VALID |
| A6 | Mana-as-lightning-buffer throughput | max mana → attack **added lightning** (Mind of the Council) and → volley frequency (Bladefall of Trarthus); mana pool is also the lightning EHP buffer | 2nd (3 channels) | VALID |
| A7 | Abyssal-jewel quantity | one investment (abyss jewel count) → mana % (→ seed chaos) **and** elemental penetration **and** life % | 2nd | VALID on unique/gem/passive layers; UNKNOWN on the influenced-rare layer |
| A8 | Pool-gated speed loop | mana pool size gates "not on Low Mana" → Onslaught / attack speed, refuelled by mana per hit with attacks | 2nd + closed loop | VALID on unique/gem/passive layers; UNKNOWN on the influenced-rare layer |

Anti-duplication argument (why these are not cosmetic variants of one another): A1's conversion is
*additive pool modifiers → damage*; A2's is *spell damage % → attack damage %*; A5's is a second
*flat added-damage* channel; A6's is *added lightning + hit frequency*; A7's investment axis is
*jewel quantity*; A8's is *time/speed uptime*; A3's and A4's outputs are *ailment state*
(poison stacks vs. shock), which are the only two architectures where the seed's damage type
feeds a state machine rather than a multiplier.

## Hard negatives (complete, empty results)

| Query | Result |
| ----- | ------ |
| `carriers stat:attack_damage_+%_per_500_maximum_mana` | 0 |
| `carriers stat:spell_damage_+%_per_500_maximum_mana` | 0 |
| `carriers stat:armour_+_per_10_unreserved_max_mana` | 0 |
| `carriers stat:maximum_mana_%_to_convert_to_armour_at_doubled_value` | 0 |
| `carriers stat:additive_mana_modifiers_apply_to_shock_effect_at_30%_value` | 0 |
| `carriers stat:damage_+%_per_poison_stack` | 0 |
| `carriers stat:maximum_mana` | 0 |
| `carriers mod:ClarityManaAddedAsEnergyShield` | 0 (mana→ES conversion has **no named unique**) |
| `carriers mod:GainManaPer2IntelligenceUnique_1` | 0 (flat mana-per-int has **no named unique**) |
| `carriers mod:DivergentSpellDamageModifiersApplyToAttackDamageUniqueHelmetInt7` | 0 |

## API gaps (fail-closed, not guessed)

1. **No inherent int→Mana edge.** `carriers stat:maximum_mana` and `stat:maximum_mana_+%` return
   no `attribute_grants_stat` row, yet `stat:gain_no_maximum_mana_from_intelligence`
   ("Intelligence provides no inherent bonus to Maximum Mana", Mask of the Stitched Demon)
   exists as a negation. The positive conversion is therefore **UNKNOWN** from the API; this run
   does not claim int grants Mana. The only evidenced int→Mana path is the flat modifier
   `mod:GainManaPer2IntelligenceUnique_1` / `mod:Haunted`, which has **no unique carrier**.
2. **Numbers on passive-granted stats are not exposed.** Passive nodes carry a generated
   descriptive `name` ("Mana", "Energy Shield and Mana", "Prodigal Perfection") and a
   `passive_grants_stat` edge, but no numeric text. Every tree contribution in `builds.md` is
   rendered as its stat name, not as a number.
3. **Numbers on unique modifiers are roll-ranges, and `resolve` can return a low-roll variant.**
   e.g. Echoforge renders "+(-200-200) to maximum Life" and "(-16-16)% increased Attack Speed" for
   the nodes associated with that unique. Rendered verbatim; no roll was chosen.
4. **Influenced-rare declarations do not validate in this KB build.** `influence_check` returns
   `modifier carries no influence` for the influence-family modifiers tested (including
   `mod:DamagePer100INTEldritchImplicit1` and `mod:ManaGainPerTargetInfluenceMaven`) and
   `no influence_tags on item_class: 'AbyssJewel'`. The layer is *not* broken — it returned a
   real `invalid` for `mod:SpellBlockAmuletInfluence1` on Gloves ("influence Crusader's cannot roll
   on Gloves") — it is a coverage gap. A7 and A8 are therefore `unknown` on that one layer and
   `valid` on slot / weapon / gem / ascendancy / availability.
5. **Whether Arcane Might converts `spell_damage_+%_per_100_maximum_mana_up_to_60%`** (Prodigal
   Perfection) is **UNKNOWN**: the mechanic's declared operands are the generic
   `stat:spell_damage_+%` and `stat:attack_damage_+%` nodes, and Prodigal Perfection grants a
   *different* stat id. A2 records the chain as a hypothesis, not as a fact.
6. **Whether the seed's "Added Attack Chaos Damage" is main-hand chaos** is not stated anywhere in
   the KB, so `maximum_poison_damage_to_deal_per_minute_from_main_hand_chaos_damage` was **not**
   used as an edge for A3.
7. **Whether the seed affects minion attacks** is not modelled (no minion edge on
   `mod:AttacksGainMinMaxAddedChaosDamageBasedOnManaUnique__1`); no minion architecture was
   proposed.

## Slot-model facts that shaped the builds

- Single `weapon` slot → dual-wield pairs are not validatable (The Consuming Dark + The Wasp Nest
  is `invalid: capacity 1 exceeded`), which is why A3 runs The Wasp Nest alone with Snakebite
  (Gloves) supplying the frenzy-charge poison channel instead of a second weapon.
- **Glimpse of Chaos is a Helmet**, so it conflicts with Crown of Eyes / Crown of the Inward Eye /
  Mind of the Council (`head: capacity 1 exceeded`). It was removed from every build that uses a
  Crown; that is a real discovery constraint, not a build-quality choice.
- **Zerphi's Heart is an Amulet** → competes with the seed itself.
- Weapon restrictions that decided gem choice: Heavy Strike of Trarthus = `['Staff','Warstaff']`,
  Kinetic Blast of Clustering / Power Siphon of the Archmage = `['Wand']`, Viper Strike =
  `['Claw','Dagger','One Hand Sword','Thrusting One Hand Sword','Two Hand Sword','Rune Dagger']`,
  Bladestorm = valid on `Two Hand Sword`, Boneshatter = `['One Hand Axe','One Hand Mace','Sceptre',
  'Staff','Two Hand Axe','Two Hand Mace','Warstaff']` (**not** a sword), Bladefall of Trarthus =
  no restrictions. Echoforge is a Two Hand Sword, so Boneshatter is INVALID with it — A4 uses
  Bladestorm.
- `item_class:Warstaff` has 0 uniques in the KB; every staff build uses `item_class:Staff`.

## Reproduce

```
uv run python santa-maria/tools/research.py resolve "Whispers of Infinity" --type UniqueItem
uv run python santa-maria/tools/research.py carriers mod:AttacksGainMinMaxAddedChaosDamageBasedOnManaUnique__1
uv run python santa-maria/tools/research.py resolve "per 100 maximum mana"
uv run python santa-maria/tools/research.py carriers stat:maximum_mana_+%
uv run python santa-maria/tools/research.py resolve "maximum_mana" --type Stat
uv run python santa-maria/tools/research.py neighbour unique:1461 --depth 1
uv run python santa-maria/tools/research.py validate '<build-state json>'
```