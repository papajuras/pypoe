# whispers07 — Whispers of Infinity build discovery (clean slate)

- Date: 2026-09-21
- Seed: `unique:1461` **Whispers of Infinity** (Amulet, availability: available)
- Method: public Research API only (`resolve` / `carriers` / `neighbour` / phase7 validator). No previous-run reuse, no pretraining-derived claims. Every relationship below is backed by a listed API query; anything not derivable is marked UNKNOWN / hypothesis / API GAP.
- Discovery skills applied: `discovery-api-usage`, `scaling-discovery` (growth loop to fixed point), `build-output` (sheets).

---

## Seed analysis — Whispers of Infinity (unique:1461)

| Slot | Item | Details |
| ---- | ---- | ------- |
| Amulet | Whispers of Infinity *(available)* | implicit: **(10-15)% faster start of Energy Shield Recharge** · explicit: **(60-40)% reduced maximum Mana** · **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana** · **Skills Cost Energy Shield instead of Mana or Life** |

API facts about the seed's mods (sweep 1):

- `stat:min/max_attack_added_chaos_damage_per_100_mana`: **sole carrier = this amulet** (carriers → 1 unique).
- `stat:base_skills_cost_es_instead_of_mana_life`: **sole carrier = this amulet** — the ES-cost engine is exclusive to it.
- `stat:maximum_mana_+%` (the −% side): generator surface for the *other* direction is huge — 78 mods + 72 passives grant `maximum_mana_+%`; `stat:base_maximum_mana` has 228 mods + 11 passives + `attribute_grants_stat` from `stat:intelligence`.
- `stat:energy_shield_delay_-%` family: 32 mods + 4 passives (incl. `passive:energy_shield_delay_notable1688` Essence Surge).
- Tension: the amulet shrinks the mana pool that feeds its own added-chaos stat.

Intrinsic rules surfaced around the seed's stats (probe `carriers stat:intelligence`, `carriers stat:base_maximum_mana`):

- `rule:intelligence_mana` — "1 Mana per 2 Intelligence" (`rule_applies_to` both stats)
- `rule:intelligence_energy_shield` — "1% increased maximum Energy Shield per 10 Intelligence"

---

## Scaling analysis

**No KB evidence of a mana→multiplier stat.** `resolve "per mana"` returns only Tincture Mana-Burn mods; mana's consumers are flat-added-damage stats (`per 100 maximum mana` family: the seed's chaos; `unique:1306 The Scales of Justice` fire per 100 of Life-or-Mana — but that shield also carries **no Energy Shield** and is therefore incompatible with the seed's ES-cost engine; rejected below).

**The usable shared axis is Intelligence** (generates mana AND ES per the two rules above, and has per-int damage/carrier families found via `resolve "per 10 intelligence"`, `resolve "per 100"`).

Quadratic candidate (Build 2): X=Intelligence →
- path A (confirmed chain): int →(`rule:intelligence_mana`)→ mana →(seed mod)→ added attack chaos → hit chaos
- path B (confirmed edges): int on **unallocated passives in radius** (jewel `unique:790`) → +3% DoT multiplier per 10 int
- interaction (hypothesis, see API gaps): poison output = hit-base × DoT-multiplier, so A × B → poison ⇒ X².

Sweeps 2-4 checked the remaining directions and found: elemental→chaos conversion family (large, several *available* carriers), frenzy/power charge engines, ES-recovery triggers, and the applies-to bridge family. Fixed point reached: the final sweep added no new node classes — only influenced-only mods (validator gap, parked).

---

## Build 1 — Infinity Claw (int-stacked attack chaos, multi-use) — VALIDATED

| Slot | Item | Details |
| ---- | ---- | ------- |
| Amulet | Whispers of Infinity *(available)* | **Skills Cost Energy Shield instead of Mana or Life** · **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana** · (60-40)% reduced maximum Mana · (10-15)% faster start of Energy Shield Recharge |
| Weapon | Hand of Wisdom and Action *(Claw, available)* | **Adds 1 to 12 Lightning Damage to Attacks with this Weapon per 10 Intelligence** · (8-12)% increased Intelligence · (8-12)% increased Dexterity · 1% of Attack Damage Leeched as Life |
| Helmet | Wilma's Requital *(available)* | **Increases and Reductions to Cast Speed apply to Attack Speed** · (20-30)% increased Elemental Damage with Attack Skills · +(300-500) to Accuracy Rating |
| Ring | Ming's Heart *(available)* | **Gain (40-60)% of Physical Damage as Extra Chaos Damage** · +(40-50)% to Chaos Resistance · 25% reduced maximum Life · 25% reduced maximum Energy Shield |
| Flask (unknown-check) | Atziri's Promise *(available)* | **Gain (5-8)% of Elemental Damage as Extra Chaos Damage during effect** — validator: no slot model for flasks, not checked |

Validation: `validate_build(seed, HoWA, Ming's Heart, Wilma's Requital)` = **VALID** (slot occupancy, weapon configuration, availability). Flask surfaced `unknown — not checked` (documented validator limitation).

**Why it works** — Skills cost ES, so mana becomes a pure damage pool; the claw turns Intelligence directly into flat lightning on attacks while the intelligence→mana rule feeds the amulet's flat attack chaos; Ming's Heart and the flask funnel physical/elemental slices into the same chaos pool. Ladder: multi-use (two flat paths + conversions into one output; no multiplier path from X=mana/int with an available carrier).

**Evidence** —
- `stat:intelligence` → `rule_applies_to` → `rule:intelligence_mana` (1 Mana per 2 Int)
- `stat:intelligence` → `attribute_grants_stat` → `stat:base_maximum_mana`
- `stat:base_maximum_mana` → (seed mod) → `stat:min/max_attack_added_chaos_damage_per_100_mana` (sole carrier: seed)
- `mod:AddedLightningDamagePerIntelligenceUnique__1` → unique:597 (claw)
- `mod:ChaosDamageAsPortionOfDamageUniqueRing16` → unique:189/975 Ming's Heart
- `mod:CastSpeedAppliesToAttackSpeedUnique__1` → unique:1378 (only "apply to attacks" hit in KB prose)

---

## Build 2 — Poison Infinity (int-fed poison chaos, quadratic CANDIDATE) — VALIDATED (core)

| Slot | Item | Details |
| ---- | ---- | ------- |
| Amulet | Whispers of Infinity *(available)* | **Skills Cost Energy Shield instead of Mana or Life** · **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana** · (60-40)% reduced maximum Mana · (10-15)% faster start of Energy Shield Recharge |
| Weapon | The Consuming Dark *(Dagger, available)* | **Your Chaos Damage has 60% chance to Poison Enemies** · 30% of Fire Damage Converted to Chaos Damage · 10% chance to gain a Frenzy Charge on Hit · (40-60)% increased Fire Damage · +1 to Level of all Fire Spell Skill Gems · +(20-40) to Intelligence (from `carriers stat:additional_intelligence` family) |
| Gloves | Snakebite *(available)* | **Attacks have 60% chance to Poison while at maximum Frenzy Charges** · +5% to Damage over Time Multiplier for Poison per Frenzy Charge · 2% increased Attack Speed per Frenzy Charge · 6% increased Accuracy Rating per Frenzy Charge · 10% reduced Frenzy Charge Duration per Frenzy Charge · +(60-70) to maximum Life · (150-180)% increased Evasion Rating |
| Helmet | Fenumus' Toxins *(available)* | **(6-10)% chance to Poison per Power Charge** · **(15-20)% increased Damage with Poison per Power Charge** · **10% chance to gain a Power Charge on hitting an Enemy affected by a Spider's Web** · Aspect of the Spider inflicts Spider's Webs and Hinder every 0.5 Seconds instead · Adds (16-21) to (31-36) Chaos Damage to Spells |
| Ring | Ming's Heart *(available)* | **Gain (40-60)% of Physical Damage as Extra Chaos Damage** · +(40-50)% to Chaos Resistance · 25% reduced maximum Life · 25% reduced maximum Energy Shield |
| Jewel (unknown-check) | Transcendent Mind *(available)* | **+3% to Damage over Time Multiplier per 10 Intelligence on Unallocated Passives in Radius** · −1 Intelligence per 1 Intelligence on Allocated Passives in Radius · 3% increased Mana Recovery Rate per 10 Intelligence on Allocated Passives in Radius · 2% reduced Mana Recovery Rate per 10 Intelligence on Unallocated Passives in Radius — validator: no slot model for jewels, not checked |

Validation: `validate_build(seed, Consuming Dark, Snakebite, Fenumus' Toxins, Ming's Heart)` = **VALID**; jewel = unknown/not checked.

**Why it works** — Intelligence is the shared axis: the rule converts it to mana, the amulet converts that mana into flat attack chaos, and the jewel converts unallocated tree Intelligence into poison DoT multiplier. Hit chaos poisons (dagger 60% / gloves 60% at max frenzy / helmet per power charge), so the flat path grows the poison base while the jewel path grows its multiplier — both from X=Int ⇒ X² **candidate**. The helmet's web→power-charge loop and the dagger's frenzy-on-hit keep both charge multipliers live without extra engines.

**Evidence** —
- int → `rule:intelligence_mana` → mana → seed stat (as Build 1)
- `mod:DamageOverTimeMultiplierPerUnallocatedIntelligenceUnique__1___` → unique:790 Transcendent Mind
- `mod:ChaosDamageChanceToPoisonUnique__1` → unique:312; `mod:AtMaximumFrenzyChargesChanceToPoisonUnique_1_` → unique:221; `mod:PoisonChancePerPowerChargeUnique__1`, `mod:PoisonDamagePerPowerChargeUnique__1`, `mod:PowerChargeOnHitWebbedEnemyUnique__1` → unique:768
- `mod:ChargeBonusFrenzyChargeOnHit__` (10% frenzy on hit) → unique:312
- poison×hit interaction and unallocated-int mechanics: **hypothesis** (see API gaps)

---

## Build 3 — ES-Battery Icestorm (resource-loop spellcaster) — VALIDATED

| Slot | Item | Details |
| ---- | ---- | ------- |
| Amulet | Whispers of Infinity *(available)* | **Skills Cost Energy Shield instead of Mana or Life** · (5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana *(unusable by spells — attacks only)* · (60-40)% reduced maximum Mana · **(10-15)% faster start of Energy Shield Recharge** |
| Weapon | The Whispering Ice *(Staff, available)* | **Grants Level 1 Icestorm Skill** · **1% increased Spell Damage per 10 Intelligence** · (14-18)% increased Intelligence · (8-12)% increased Cast Speed · +1 to Level of Socketed Support Gems |
| Body | Crown of the Inward Eye *(available)* | **Transfiguration of Soul** (stat: `additive_energy_shield_modifiers_apply_to_spell_damage_at_30%_value`) · Transfiguration of Mind · Transfiguration of Body · (+ to Life/Mana/ES — mod family `MaximumLifeManaEnergyShieldUnique__1`, value ranges not returned by API) |
| Gloves | Demon Stitcher *(available)* | **Sacrifice (5-25)% of Life to gain that much Energy Shield when you Cast a Spell** |

Validation: `validate_build(seed, Whispering Ice, Crown of the Inward Eye, Demon Stitcher)` = **VALID**.

**Why it works** — The amulet's ES-cost conversion (sole KB carrier) makes ES the skill currency: the whole cast loop runs on the ES pool, refilled by life-sacrifice per cast and by the faster-recharge implicit. Intelligence feeds spell damage directly on the staff and the ES pool via `rule:intelligence_energy_shield`. If the ES bridge counts rule-granted ES modifiers (hypothesis — not modeled in KB), int also gains a second spell-damage path through Transfiguration of Soul (ES% → 30% spell damage).

**Evidence** —
- `stat:base_skills_cost_es_instead_of_mana_life` → sole granter = seed amulet
- `stat:energy_shield_delay_-%` (implicit) + family (32 mods / 4 passives)
- `stat:intelligence` → `rule_applies_to` → `rule:intelligence_energy_shield` (1% inc max ES per 10 int)
- `mod:SpellDamagePerIntelligenceUniqueStaff12`, `mod:IcestormUniqueStaff12` → unique:326
- `mod:SacrificeLifeToGainESUnique__1` → unique:811 Demon Stitcher
- `stat:additive_energy_shield_modifiers_apply_to_spell_damage_at_30%_value` ← `mod:TransfigurationOfSoulUnique__1_` → unique:1083

---

## Build 4 — Transfigured Mana (mana axis, two same-output paths) — VALIDATED (core)

| Slot | Item | Details |
| ---- | ---- | ------- |
| Amulet | Whispers of Infinity *(available)* | **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana** · **Skills Cost Energy Shield instead of Mana or Life** · (60-40)% reduced maximum Mana · (10-15)% faster start of Energy Shield Recharge |
| Body | Crown of the Inward Eye *(available)* | **Transfiguration of Mind** (stat: `additive_mana_modifiers_apply_to_damage_at_30%_value`) · Transfiguration of Body · Transfiguration of Soul · (+ to Life/Mana/ES — values not returned by API) |

Validation: `validate_build(seed, Crown of the Inward Eye)` = **VALID**.

**Why it works** — Maximum mana becomes the shared axis with two confirmed paths into the same output: the flat attack-chaos-per-100-mana stat (amulet) and the 30%-of-value application of increased/reduced-mana modifiers to damage (Crown). They stack additively on attack damage — **multi-use, not quadratic** (no cross-multiplication between the paths). The seed's −40-60% mana is a double-edged tax: it shrinks the flat-chaos denominator *and* enters the Mind bridge as a negative additive modifier.

**Evidence** —
- `stat:max/min_attack_added_chaos_damage_per_100_mana` (sole carrier: seed)
- `stat:additive_mana_modifiers_apply_to_damage_at_30%_value` ← `mod:TransfigurationOfMindUnique__1` → unique:1083
- `stat:maximum_mana_+%` generator surface (78 mods / 72 passives), `stat:base_maximum_mana` (228 mods / 11 passives / int rule)

Optional extensions (equippable, from the same probes): Ming's Heart ring (phys→extra chaos; −25% life/ES tax), Atziri's Promise flask (elemental→extra chaos during effect; flask slot unknown-check).

---

## Rejected / anti-synergy findings (API-backed)

- **The Scales of Justice** (unique:1306, Shield, available): "Added Fire Damage per 100 of Maximum Life or Maximum Mana, whichever is lower" + "Immune to Elemental Ailments while Life and Mana are close" — but it also carries **no Energy Shield**, which zeroes the ES pool the seed's cost engine needs. Dead pairing.
- **mod:GainManaOnManaPaidManaCost1-3** ("(25-30)% chance when you pay a Skill's Cost to gain that much Mana" + 30% reduced max Mana): with the seed equipped, skill costs are paid in ES — whether the trigger counts ES-paid costs is not derivable from the KB (UNKNOWN). Not built on.
- **Weapon-tree "IntelligenceAndNoInherentBonus" mods** ("+60 to +120 to Intelligence, Gain no inherent bonuses from Intelligence"): would cancel the two intelligence rules that both int architectures rely on.
- **mod:IncreasedManaUnique__19 (+500 max Mana)** and several big %-mana mods return **no unique carriers** (live-only KB: true absence) — the +500-mana item is not nameable via the API; mana generation is represented instead by the passive/mod surface and the int rule.
- **Eldritch Knowledge** (unique:340, "5% increased Chaos Damage per 10 Intelligence from Allocated Passives in Radius"): **unavailable** per PoB obtainability verdict — the only KB-evidenced %chaos-per-int multiplier, so no available carrier of a chaos-multiplier-from-int path exists.

## API gaps / unknowns (fail-closed, not guessed)

1. **Influenced/rare-item compatibility not modeled** (validator limitation; also no unique carriers exist for these mods, so `carriers()` returns empty — e.g. `DamagePer100INTEldritchImplicit*` "3-6% increased Damage per 100 Intelligence" (body), `FrenzyChargeOnHitChanceInfluence1` "10% chance to gain a Frenzy Charge on Hit", `PhysicalDamageAddedAsChaosEldritchImplicit*`, `ChanceToPoisonWithAttacksUnique___2` "(40-50)% chance to Poison on Hit with Attacks"). Recorded as hypotheses only; none included in the validated builds.
2. **Hit→poison derivation** (poison DoT base = hit's chaos damage, × DoT multiplier) is not exposed as a KB edge; the Build-2 quadratic claim is a candidate with this link marked hypothesis.
3. **Unallocated-int mechanics** for Transcendent Mind (whether transform/radius jewels feed unallocated counts, and whether engine rules count as "additive ES modifiers" for the Transfiguration bridges) are engine-level semantics not represented in the KB — the associated paths are hypotheses.
4. **Gem text is not searchable** (only modifiers carry `text`); attack-chaos gem enumeration relied on the support gem's granted stats (`gem:SupportChanceToPoison` → poison chance + added chaos stats).
5. **No spell→attack damage bridge found in KB prose** (`resolve "apply to attacks"` → only Cast-Speed→Attack-Speed; the Transfiguration trio covers life/mana/ES→damage). A spell-side scaler converting into attack chaos is therefore not evidenced; not pursued.

## Growth loop — sweep log (scaling-discovery §10)

| Sweep | Probes | Added |
| ----- | ------ | ----- |
| 1 | seed neighbourhood; carriers of all 4 seed stats; mana pool stat; `resolve "per 100"` | seed-exclusive stats; mana generator surface; delay family |
| 2 | `carriers stat:intelligence` (2 rules); `resolve "per 10 intelligence"`; `resolve "based on mana"`/`"per mana"`; conversion family | int rules; per-int damage families; elemental/phys→chaos conversions; Scales of Justice rejection; no mana→multiplier stat |
| 3 | poison chance family; charge generators; `resolve "energy shield when"`; item neighbourhoods (HoWA, Whispering Ice, Poised Prism, Ming's Heart, Consuming Dark, Snakebite, Fenumus, Transcendent Mind, Wilma, Gluttonous Tide, Demon Stitcher, Crown of the Inward Eye) | poison engine trio; frenzy/power loops; ES-recovery triggers; all item mod lists + classes |
| 4 | `resolve "apply to attacks"` / `"apply to attack damage"`; Transfiguration trio stat extraction; validators ×4 (plus 2 re-runs without no-slot-model items) | applies-to bridge family; Body/Mind/Soul bridge stats; all 4 builds VALID (flask/jewel unknown-check); **no new nodes/edges — fixed point** |

Open leads (parked, not pursued): Tincture Mana-Burn mods (pen per mana burn — melee, weak link to the seed); Chaos-Damage→Chaos-Aura-Effect mods (aura engine, tangential); The Gluttonous Tide crit-frenzy bow (same poison engine, weapon-class variant of Build 2, not rendered separately per no-cosmetic-variants rule).

*Ascendancy: UNKNOWN for all builds — no evidence source in this session established one.*
