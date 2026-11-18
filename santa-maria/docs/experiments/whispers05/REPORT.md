# whispers05 — Whispers of Infinity: distinct build architectures

Run date: 2026-09-18. Clean slate: no prior run consulted, no pretraining knowledge used for
mechanics claims. Everything below is derived from the public Research API
(`phase8_research.resolve/carriers`, `phase6_api.get_neighbour`, `phase7_build_validity`,
`phase7_build_feasibility`). Gem display names are not exposed by the API (see Gaps); gem names
below are the id's de-camelized form.

## Seed

**Whispers of Infinity** (`unique:1461`, Amulet, availability: `available`). Complete modifier
list (via `neighbour unique:1461` → `resolve` text):

- **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana**
- **(60-40)% reduced maximum Mana**
- (10-15)% faster start of Energy Shield Recharge
- **Skills Cost Energy Shield instead of Mana or Life**

API verdicts that shape everything below:

- `stat:base_skills_cost_es_instead_of_mana_life` — carriers = **only this mod**. The
  ES-cost conversion is unique-item-exclusive; no keystone/passive/gem duplicate exists.
- `stat:max_attack_added_chaos_damage_per_100_mana` (+ min) — carriers = **only this mod**.
- The two defining mods therefore coexist only on this amulet; every architecture below is a
  different way to build the system around them.
- `(60-40)% reduced maximum Mana` is a real anti-synergy to mana stacking; mana% must be
  out-stacked elsewhere (passives/gear verified below).

## Resource map (all API-verified)

| Resource | Generators found | Consumers found |
| --- | --- | --- |
| **Maximum Mana** (axis X) | Void Battery +(100-120); Mindspiral +(100-120); Omeyocan (15-20)%; Hierophant notables (Divine Guidance, 3× "Mana Regeneration, Mana"); tree notables (Arcane Will, Mana Flows, Deep Thoughts, …) | Added attack chaos per 100 mana (seed); added phys per mana (KineticBlastAltX); added lightning % max mana (Mind of the Council, PowerSiphonAltX, ManaInfusedStaff); +spell dmg per 100 mana up to 60% (Prodigal Perfection); volley frequency per 100 mana (BladefallAltZ); evasion per 500 mana (Omeyocan); AoE per 50 unreserved mana (Sanctuary of Thought); `stat_scales_with(maximum_mana→)` edges confirmed for attack-dmg-per-500, spell-dmg-per-500, volley-freq-per-100, evasion-per-500 |
| **Unreserved mana state** | mana never *spent* under the seed (costs go to ES); drains: Apep's Rage −40/skill, MotC −3%/attack, Omeyocan −7%/s | Archmage: added lightning % of max unreserved mana; Manabond: base lightning % of **missing** unreserved mana + low-mana lightning pen |
| **Reserved mana** | Clarity aura (`base_reservation_%`, mana reservation efficiency) | Frostmage: added cold % of max **reserved** mana (+ cost % of reserved) |
| **Energy Shield** | ES% notables/items (Sudden Dawn 300-350% ES, MotC ES, Occultist 13/17) | cost pool for **all** skills (seed); FR: chaos dmg % of max ES + self-damage % max ES; ES→life regen mod exists (Mask of the Stitched Demon — but incompatible, see Absences) |
| **Ward** | Nightgrip (33-48)% Ward; Svalinn +(100-150) Ward | Nightgrip: **added chaos = 10% of Ward**; SupportCastOnWardBreak triggers a supported spell on ward break |

## Scaling classification (ladder, per skill §9)

- **Quadratic candidate (strongest finding)** — B3: mana → added lightning (Archmage, linear in
  unreserved mana) **×** mana → increased spell damage (Prodigal Perfection, linear in mana) →
  same output (spell damage). Both paths confirmed by carriers; the multiplicative combination
  itself is standard damage math, not KB-verifiable → **candidate, not confirmed**.
- **B8** is the attack-side analog: mana → added lightning twice (helmet 6% + gem %, gem value
  unexposed) and mana → increased **spell** damage applied **to attacks** via the gem's
  `additive_spell_damage_modifiers_apply_to_attack_damage_at_%_value` (bridge % unexposed) →
  quadratic candidate with two unknown coefficients → **hypothesis**.
- Everything else is **multi-use** (mana simultaneously buys added damage lines, a second
  damage-bridge, AoE, evasion, and the ES pool via Sanctuary/Mindspiral) — independent
  consumers, no interaction evidence.

---

## Build 1 — Kinetic Blast mana battery (attack, added-damage stacking)

| Slot | Item / Gem / Passive | Details |
| --- | --- | --- |
| Amulet | Whispers of Infinity (`unique:1461`, available) | **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana**; **(60-40)% reduced maximum Mana**; (10-15)% faster start of Energy Shield Recharge; **Skills Cost Energy Shield instead of Mana or Life** |
| Weapon | Void Battery (`unique:147`, available) | (50-65)% increased Global Critical Strike Chance; (10-20)% increased Cast Speed; **+(100-120) to maximum Mana**; +1 to Maximum Power Charges; (10-15)% increased Spell Damage per Power Charge; (36-40)% increased Spell Damage; 50% reduced Spell Damage *(spell-side drawback, irrelevant to the attack engine)* |
| Helmet | Crown of the Inward Eye (`unique:1083`, available) | 333% increased Armour and Energy Shield; (9-21)% increased maximum Life, Mana and Global Energy Shield; **Transfiguration of Mind**; Transfiguration of Body *(no text exposed — UNKNOWN)*; Transfiguration of Soul *(no text exposed — UNKNOWN)* |
| Gem (attack) | KineticBlastAltX + SupportAddedChaosDamage | Gem stats include: **added physical damage to attacks equal to % of maximum mana** (% value unexposed); spell damage modifiers apply to attack damage at % value (unexposed); cluster-burst projectile mechanics |
| Ascendancy | Hierophant | Divine Guidance, Sanctuary of Thought |
| Passives | Arcane Will, Mana Flows | maximum_mana_+% / mana regen notables (stat sets verified) |

**Status: VALIDATED** (validator scope: slot occupancy, weapon configuration, gem supportability, ascendancy composition, item availability).

**Why it works** — The seed converts every skill cost to ES, so the mana pool is a pure stat.
Mana feeds three additive damage paths into one attack hit: the amulet's added chaos per 100
mana, KineticBlastAltX's added physical per mana, and the 30%-value additive-mana→damage bridge
(Crown's Transfiguration of Mind / Divine Guidance). Wand context confirmed (`weapon_check`:
"Wand is an allowed weapon class").

**Evidence** — `stat:max_attack_added_chaos_damage_per_100_mana` → carried only by the seed ·
`stat:added_physical_damage_to_attacks_equal_to_%_maximum_mana` → gem:KineticBlastAltX ·
`stat:additive_mana_modifiers_apply_to_damage_at_30%_value` → mod:TransfigurationOfMindUnique__1
(unique:1083) + passive:AscendancyHeirophant7 · `stat:maximum_mana_+%` → 72 passive + 81
modifier carriers.

**Scaling class:** multi-use (no interaction evidence between the three added-damage lines).

---

## Build 2 — Mind of the Council lightning-chaos battery (attack, self-draining)

| Slot | Item / Gem / Passive | Details |
| --- | --- | --- |
| Amulet | Whispers of Infinity (`unique:1461`, available) | same four mods as Build 1 |
| Helmet | Mind of the Council (`unique:533`, available) | **Attack Skills have Added Lightning Damage equal to 6% of maximum Mana**; **Lose 3% of Mana when you use an Attack Skill**; **30% of Lightning Damage is taken from Mana before Life**; +20% chance to be Shocked; +(15-20) to maximum Energy Shield; (230-260)% increased Evasion and Energy Shield |
| Weapon | Mortem Morsu (`unique:106`, available) | Grants 20 Life per Enemy Hit; 60% chance to Poison on Hit; +40% to Global Critical Strike Multiplier; 25% increased Critical Strike Chance; 20% increased Attack Speed; (75-100)% increased Physical Damage; (10-20)% of Physical Damage Converted to Chaos Damage; 25% reduced Enemy Stun Threshold with this Weapon |
| Gem (attack) | SerpentStrike + SupportAddedChaosDamage | Gem stats include: physical→chaos conversion (% unexposed), added attack chaos, maximum snakes (melee spawn mechanic) |
| Ascendancy | Hierophant | start node only (no notables committed) |
| Passives | Arcane Will, Mana Flows | maximum_mana_+% / mana regen notables |

**Status: VALIDATED** (same validator scope).

**Why it works** — The helmet turns attack skill use into a mana drain and gives the attack a
second mana-scaled added line (lightning), while the amulet adds chaos per mana to the same
hits; the claw already converts physical to chaos, so poison/chaos crit scaling rides along.
Attacks cost ES (seed), mana drains only via the helmet's explicit loss mechanics.

**Evidence** — `stat:attack_skills_have_added_lightning_damage_equal_to_%_of_maximum_mana` →
gem:PowerSiphonAltX + mod carried by unique:533 · `stat:lose_%_mana` family → MotC/Omeyocan mods ·
`stat:skill_physical_damage_%_to_convert_to_chaos` → gem:SerpentStrike.

**Scaling class:** multi-use + a drain loop (drain caps the battery; no KB edge turns the drain
itself into damage — that would be Manabond territory, Build 7).

---

## Build 3 — Archmage × Prodigal Perfection mana-multiplication (spell, quadratic candidate)

| Slot | Item / Gem / Passive | Details |
| --- | --- | --- |
| Amulet | Whispers of Infinity (`unique:1461`, available) | same four mods as Build 1 |
| Weapon | Lifesprig (`unique:205`, available) | (5-8)% increased Cast Speed; +(15-20) to maximum Life; +(15-20) to maximum Mana; **+1 to Level of Socketed Spell Gems**; (20-28)% increased Spell Damage |
| Helmet | Crown of the Inward Eye (`unique:1083`, available) | as Build 1 (**Transfiguration of Mind** = third mana→damage path) |
| Gem (spell) | Spark + SupportArchmage | Archmage gem stats: **gain lightning damage equal to % of max unreserved mana** (% unexposed); skill cost equals % of unreserved mana |
| Ascendancy | Hierophant | Divine Guidance, Sanctuary of Thought |
| Passives | **Prodigal Perfection**, Arcane Will | Prodigal Perfection grants **+spell damage % per 100 maximum mana, up to 60%** (verified via `passive_grants_stat`) |

**Status: VALIDATED** (same validator scope).

**Why it works** — Under the seed, mana is never spent, so *unreserved* mana stays at maximum:
Archmage's added lightning sits at full value permanently, Prodigal Perfection's increased
spell damage scales linearly with the same pool, and the two multiply inside one output —
the run's strongest quadratic candidate. Sanctuary of Thought adds "Mana % as extra maximum
Energy Shield", tying the same pool to the ES cost pool. Support chain `SupportArchmage +
Spark` validated (`allowed/excluded checks passed`).

**Evidence** — `stat:archmage_gain_lightning_damage_%_of_max_unreserved_mana` → gem:SupportArchmage ·
`stat:spell_damage_+%_per_100_maximum_mana_up_to_60%` → passive:mana_spell_damage_notable2609 ·
`stat:mana_%_to_add_as_energy_shield` → Sanctuary of Thought (+ Mindspiral mod, itemized in
Build 7) · `stat:additive_mana_modifiers_apply_to_damage_at_30%_value` → Divine Guidance +
Crown of the Inward Eye.

**Scaling class:** **quadratic candidate** (X→A, X→B, A×B→output; A and B both confirmed
carriers; multiplication itself is standard damage math, not KB-verified).

---

## Build 4 — Forbidden Rite ES-pool caster (self-damage + ES churn)

| Slot | Item / Gem / Passive | Details |
| --- | --- | --- |
| Amulet | Whispers of Infinity (`unique:1461`, available) | same four mods as Build 1 |
| Helmet | Sudden Dawn (`unique:1332`, available) | **(10-20)% chance for Energy Shield Recharge to start when you Kill an Enemy**; (40-30)% less Energy Shield Recharge Rate; (300-350)% increased Energy Shield |
| Weapon | Lifesprig (`unique:205`, available) | as Build 3 |
| Gem (spell) | ForbiddenRite + SupportAddedChaosDamage | Gem stats include: **added chaos damage equal to % of mana cost, if payable**; **base chaos damage % of maximum Energy Shield**; base chaos damage % of maximum Life; take % of max ES / max Life as chaos damage (soulfeast stats) |
| Ascendancy | Occultist | Energy Shield, Chaos Damage; Energy Shield, Energy Shield Recharge Rate |
| Passives | — (ascendancy nodes only) | Occultist13: chaos_damage_+% + maximum_energy_shield_+%; Occultist17: ES recharge + ES% (stat sets verified) |

**Status: VALIDATED** (same validator scope).

**Why it works** — The seed turns Forbidden Rite's cost into an ES cost, so the build's damage
stat (max ES, via FR's % of max ES chaos scaling) and its fuel (the same ES pool) are the same
resource; recharge-on-kill (Sudden Dawn) plus Occultist recharge/ES% notables cycle the pool.
FR's "% of mana cost if payable" damage under ES-cost replacement is **UNKNOWN** (see Gaps).

**Evidence** — `stat:added_chaos_damage_%_mana_cost_if_payable` → gem:ForbiddenRite (+DarkPact
family) · `stat:skill_base_chaos_damage_%_maximum_energy_shield` → gem:ForbiddenRite ·
`stat:energy_shield_recharges_on_kill_%` → unique:1332 · seed's own
`stat:base_skills_cost_es_instead_of_mana_life` (exclusive carrier).

**Scaling class:** multi-use (ES → damage and ES → fuel are independent outputs).

---

## Build 5 — Nightgrip Ward→Chaos (Ward economy)

| Slot | Item / Gem / Passive | Details |
| --- | --- | --- |
| Amulet | Whispers of Infinity (`unique:1461`, available) | same four mods as Build 1 |
| Gloves | Nightgrip (`unique:1308`, available) | **Gain Added Chaos Damage equal to 10% of Ward**; (33-48)% increased Ward; **75% of Damage taken bypasses Ward** |
| Weapon | Apep's Rage (`unique:261`, available) | **Adds (90-130) to (140-190) Chaos Damage to Spells**; **Lose 40 Mana when you use a Skill**; (25-30)% increased Cast Speed; (27-31)% increased Spell Damage; Poisons you inflict deal Damage (30-50)% faster; +(5-10)% to Chaos Resistance |
| Shield | Svalinn (`unique:1453`, available) | Chance to Block is Lucky; +(10-20) to maximum Life; **+(100-150) to Ward**; -10% to maximum Chance to Block Spell Damage; **Trigger a Socketed Elemental Spell on Block, with a 0.25 second Cooldown** |
| Gem (spell) | DarkPact + SupportAddedChaosDamage + SupportCastOnWardBreak | DarkPact stats: added chaos % of mana cost if payable; chains; no-minion self-target/% health chaos stats |
| Ascendancy | Occultist | Energy Shield, Chaos Damage |
| Passives | — (ascendancy nodes only) | Occultist13: chaos + ES% |

**Status: VALIDATED** (same validator scope).

**Why it works** — Ward stops being purely defensive: Nightgrip converts 10% of the Ward pool
into a global added-chaos line, Svalinn stacks the pool and converts blocks into spell
triggers, and SupportCastOnWardBreak (validated supportable on DarkPact) turns a ward break
into an extra cast. The seed keeps skill costs on ES so mana loss (Apep's per-skill drain)
stays irrelevant to casting.

**Evidence** — `stat:global_added_chaos_damage_%_of_ward` → mod carried only by unique:1308 ·
`stat:local_ward` → unique carriers include unique:1453 (Svalinn) ·
`stat:trigger_on_ward_break_%_chance` family → SupportCastOnWardBreak (`gem_grants_stat`).

**Scaling class:** multi-use (Ward → offense + defense; no interaction evidence).

---

## Build 6 — BladefallAltZ volley-rate engine (spell, rate axis)

| Slot | Item / Gem / Passive | Details |
| --- | --- | --- |
| Amulet | Whispers of Infinity (`unique:1461`, available) | same four mods as Build 1 |
| Weapon | Void Battery (`unique:147`, available) | as Build 1 (+100-120 mana; note its 50% reduced Spell Damage applies to the spell side — the engine's damage multiplier, a real tension) |
| Helmet | Crown of the Inward Eye (`unique:1083`, available) | as Build 1 |
| Gem (spell) | BladefallAltZ + SupportAddedChaosDamage | Gem stats include: **bladefall volley frequency +% per 100 maximum mana**; base volley frequency (ms, value unexposed); lingering blades per volley; max blades left in ground |
| Ascendancy | Hierophant | Divine Guidance, Sanctuary of Thought |
| Passives | Arcane Will, Mana Flows | maximum_mana_+% notables |

**Status: VALIDATED** (same validator scope).

**Why it works** — This is the **rate** axis: mana buys volley frequency (more volleys per
second), not damage. A `stat_scales_with` edge (`stat:maximum_mana →
stat:bladefall_volley_frequency_+%_per_100_maximum_mana`) is the only explicit dependency edge
of this kind found in the whole mana family. Divine Guidance/Crown convert the same mana into
added damage at 30% value. Archmage is NOT supportable here (BladefallAltZ is Arcane-typed —
validated rejection).

**Evidence** — `stat:bladefall_volley_frequency_+%_per_100_maximum_mana` → gem:BladefallAltZ ·
`stat_scales_with(maximum_mana → volley_frequency)` ·
`stat:additive_mana_modifiers_apply_to_damage_at_30%_value` → Divine Guidance + Crown.

**Scaling class:** multi-use across rate + damage.

---

## Build 7 — Manabond depletion engine (depletion axis)

| Slot | Item / Gem / Passive | Details |
| --- | --- | --- |
| Amulet | Whispers of Infinity (`unique:1461`, available) | same four mods as Build 1 |
| Weapon | Apep's Rage (`unique:261`, available) | **Lose 40 Mana when you use a Skill** + big spell-chaos adds (full list in Build 5) |
| Helmet | Mindspiral (`unique:176`, available) | **Gain (10-15)% of Maximum Mana as Extra Maximum Energy Shield**; **+(100-120) to maximum Mana**; Enemies Cannot Leech Mana From you; (10-20)% of Damage taken Recouped as Mana |
| Boots | Omeyocan (`unique:795`, available) | **20% increased Evasion Rating per 500 Maximum Mana**; **Lose 7% of Mana per Second**; (15-20)% increased maximum Mana; You have Onslaught while not on Low Mana |
| Gem (spell) | Manabond + SupportAddedChaosDamage | Gem stats include: **gain % of missing unreserved mana as base lightning damage** (% unexposed); lightning→cold conversion; lightning penetration while on low mana; area damage |
| Ascendancy | Hierophant | start node only |
| Passives | Arcane Will, Mana Flows | maximum_mana_+% notables |

**Status: VALIDATED** (same validator scope).

**Why it works** — Manabond scales with *missing* unreserved mana. Under the seed no skill
spends mana, so depletion must come from explicit drains: Apep's Rage (−40/cast) and Omeyocan
(−7%/s) manufacture the missing-mana state that Manabond pays out. A big max-mana pool
(Mindspiral + passives) is simultaneously the depletion headroom, the Archmage-style payout
denominator, the seed's chaos-per-100-mana stat, and (via Mindspiral) extra ES. This is the
only architecture where **draining** the resource is the offense.

**Evidence** — `stat:mana_void_gain_%_missing_unreserved_mana_as_base_lightning_damage` →
gem:Manabond · drains: mods on unique:261 / unique:795 ·
`stat:mana_%_to_add_as_energy_shield` → unique:176.

**Scaling class:** multi-use (drain rate × pool size feed one output additively; no
interaction edge).

---

## Build 8 — Power Siphon spell-bridge attack (attack scaled through spell modifiers)

| Slot | Item / Gem / Passive | Details |
| --- | --- | --- |
| Amulet | Whispers of Infinity (`unique:1461`, available) | same four mods as Build 1 |
| Helmet | Mind of the Council (`unique:533`, available) | as Build 2 (added lightning = 6% max mana on attacks) |
| Weapon | Void Battery (`unique:147`, available) | as Build 1 (+mana, power charges) |
| Gem (attack) | PowerSiphonAltX + SupportAddedChaosDamage | Gem stats include: **attack skills have added lightning damage equal to % of maximum mana** (% unexposed); **spell damage modifiers apply to attack damage at % value** (% unexposed); power charge generation on rare/unique hit and on kill |
| Ascendancy | Hierophant | Divine Guidance, Sanctuary of Thought |
| Passives | Arcane Will, Mana Flows | maximum_mana_+% notables |

**Status: VALIDATED** (same validator scope).

**Why it works** — PowerSiphonAltX carries its own mana→lightning line **and** the only
KB-visible bridge that lets spell-damage scaling (the Prodigal-Perfection family) reach attack
damage; combined with the helmet's 6% line, mana enters the attack through duplicated paths.
Power charges from the gem pair with Void Battery's +1 max charges / spell-damage-per-charge.
The bridge % values are not exposed by the API → the quadratic claim stays a hypothesis.

**Evidence** — `stat:attack_skills_have_added_lightning_damage_equal_to_%_of_maximum_mana` →
gem:PowerSiphonAltX + unique:533's mod ·
`stat:active_skill_additive_spell_damage_modifiers_apply_to_attack_damage_at_%_value` →
gem:PowerSiphonAltX and gem:KineticBlastAltX · `stat:maximum_energy_shield_+%`/power-charge
stats on unique:147.

**Scaling class:** quadratic candidate → **hypothesis** (two unknown coefficients).

---

## Build 9 — Frostmage reserved-mana cold engine (reserved-mana axis)

| Slot | Item / Gem / Passive | Details |
| --- | --- | --- |
| Amulet | Whispers of Infinity (`unique:1461`, available) | same four mods as Build 1 |
| Weapon | Void Battery (`unique:147`, available) | as Build 1 |
| Helmet | Crown of the Inward Eye (`unique:1083`, available) | as Build 1 |
| Gem (spell) | IceNova + SupportFrostmage | Frostmage stats: **gain cold damage equal to % of max reserved mana** (% unexposed); **skill cost equals % of reserved mana** |
| Gem (aura) | Clarity | grants `base_reservation_%` / mana-reservation-efficiency / mana-regen stats (verified via `gem_grants_stat`) |
| Ascendancy | Hierophant | Divine Guidance, Sanctuary of Thought |
| Passives | Arcane Will, Mana Flows | maximum_mana_+% notables |

**Status: VALIDATED** (same validator scope).

**Why it works** — Fourth mana state: **reserved** mana. Clarity reserves a slice of the pool;
Frostmage pays cold damage per point reserved and prices the supported skill as a % of that
reserve. The seed leaves reservation untouched (costs go to ES), so the reserved pool is a
stable damage stat, while unreserved mana still feeds the seed's chaos-per-mana line on any
attacks used.

**Evidence** — `stat:frostmage_gain_cold_damage_%_of_max_reserved_mana` → gem:SupportFrostmage ·
`stat:frostmage_cost_equals_%_reserved_mana` → gem:SupportFrostmage · Clarity reservation stats
via `neighbour gem:Clarity`.

**Scaling class:** multi-use (reserved vs unreserved mana split into independent consumers).

---

## Verified absences (zero carriers — true absences, live-only KB)

- `stat:attack_damage_+%_per_500_maximum_mana` / `stat:spell_damage_+%_per_500_maximum_mana`
  (SynthesisImplicit Attack/SpellDamagePerMana 1/2): mods exist, **zero uniques carry them** →
  increased-damage-per-mana via items is unavailable in this KB.
- `stat:maximum_mana_%_to_convert_to_armour_at_doubled_value` — zero carriers.
- `stat:additional_critical_strike_chance_per_10_shield_maximum_energy_shield_permyriad`
  (ES→crit) — zero carriers.
- `mod:ClarityManaAddedAsEnergyShield` ("Gain (6-10)% of Maximum Mana as Extra Maximum Energy
  Shield while affected by Clarity") — zero carriers.
- `stat:maximum_mana_%_to_add_to_energy_shield_while_affected_by_clarity` — zero carriers.
- Strength→added-chaos attack mod ("Adds 1 to 80 Chaos Damage to Attacks per 80 Strength") —
  zero carriers.
- `mod:EnergyShieldCostAsManaCostUnique__1` ("Skills gain a Base Energy Shield Cost equal to
  200% of Base Mana Cost") — zero carriers → **no obtainable ES-cost scaling**; cost-side
  investment is a dead end.
- `[DNT] Energy Shield Recharge instead applies to Mana` — zero carriers.
- Ward→spell physical damage (`spell_max/min_base_physical_damage_%_of_ward`) — zero carriers.
- Ward-per-ES boots (`gain_x_ward_per_10_energy_shield_on_boots`) — zero carriers.
- Mutated amulet missing-mana-on-hit mod — zero carriers (would have fed Build 7).
- **Mask of the Stitched Demon** (`unique:779`): "Cannot gain Energy Shield / Your Energy Shield
  starts at zero / Regenerate 1% of Life per second per 500 Player Maximum Energy Shield" —
  its ES never fills, so seed skills costing ES are unpayable → rejected interaction, not a build.

## API gaps (protocol per skill)

1. **Gem numeric values unexposed**: every `%` in gem-granted mana mechanics (Archmage %,
   Frostmage %, KineticBlast/PowerSiphon per-mana %, bridge %-value, Manabond %, Bladefall
   volley-frequency ms) is carried only as stat ids. `resolve`/`carriers` return no text for
   gem stats.
2. **Gem display names unexposed** (`name` empty on gem nodes).
3. **Cost-replacement semantics**: whether "% of Mana Cost" damage (Forbidden Rite / Dark Pact)
   and "% of unreserved/reserved mana" costs survive "Skills Cost Energy Shield instead of Mana
   or Life" is not represented anywhere in the API. Marked UNKNOWN wherever used.
4. **Unique→mods has no forward op**: enumerated via `get_neighbour(unique, depth=1)` — works,
   but there is no direct "mods of X" projection (documented; neighbour used throughout).
5. **Transfiguration of Body / of Soul**: name-only, no mechanics text.

## Sweep log & fixed point

- **Sweep 0 (seed)**: resolve seed → neighbour → 4 mods → 5 stats (ES-cost, chaos-per-100-mana
  ×2, mana%, ES-delay). Carriers: both defining stats exclusive to the seed.
- **Sweep 1 (stat space)**: keyword sweeps over Stat ids (maximum_mana 65 hits,
  mana_cost 107, reserved_mana 10, low_mana 11, energy_shield_recharge 27, added_chaos 97,
  ward 350 sampled); carrier probes identified the consumer set (gems: Archmage, Frostmage,
  Manabond, ForbiddenRite, DarkPact, KineticBlastAltX, PowerSiphonAltX, ManaInfusedStaff,
  BladefallAltZ, AddedChaos supports; passives: Prodigal Perfection + mana notables +
  Hierophant/Occultist nodes; uniques: MotC, Omeyocan, Nightgrip, Sudden Dawn, Crown,
  Mindspiral, Apep's Rage, Void Battery, Lifesprig, Mortem Morsu, Svalinn).
- **Sweep 2 (support/weapon validation)**: `can_support` matrix for all engines; weapon class
  checks (KB/PowerSiphon→Wand, SerpentStrike→Claw; spells unrestricted); build-state
  validation for all 9 architectures → 9/9 VALID.
- **Sweep 3 (absence check)**: every parked "possible second path" probed and killed (list
  above). Remaining parked items: `gem:ManaInfusedStaff` (staff trigger engine, no unique staff
  probed), Mind Drinker / Arcane Capacitor notables (mana-spent triggers — anti-synergy with
  the seed, dropped).
- **Fixed point**: the last full sweep over all committed nodes produced no new node/edge
  class and no reclassifications → loop stopped. No axis re-anchoring occurred (X = Maximum
  Mana throughout; Builds 4/7 shift the *working* resource to ES/missing-mana but the seed
  keeps its live edge in every subgraph via the exclusive cost-conversion stat).
