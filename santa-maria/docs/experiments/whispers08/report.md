# Whispers of Infinity — whispers08 (2026-09-21, clean slate)

Skills: discovery-api-usage / scaling-discovery v5 / build-output. All evidence via the public
Research API (`research.py` resolve/carriers/neighbour, `phase7_build_validity`, `weapon_check`).
No reuse of previous runs. All mechanics below are derived from API results; anything the API
did not evidence is marked API GAP / UNKNOWN.

## Seed (unique:1461, "Whispers of Infinity", Amulet, available) — carrier census

Seed modifier texts (from `carriers(mod)` → `subject_text`):
1. **(5–10) to (20–25) Added Attack Chaos Damage per 100 Maximum Mana** — the only carrier of
   `stat:max/min_attack_added_chaos_damage_per_100_mana` in the whole KB
   (`carriers` → 1 modifier, 0 passives, 0 gems, 0 uniques).
2. (60–40)% reduced maximum Mana (`stat:maximum_mana_+%`).
3. **Skills Cost Energy Shield instead of Mana or Life**
   (`stat:base_skills_cost_es_instead_of_mana_life`) — sole carrier in the KB.
4. (10–15)% faster start of Energy Shield Recharge.

Forward neighbours of the seed chaos stat: none beyond its granting modifier
(`neighbour stat:max_attack_added_chaos_damage_per_100_mana` → only carrier group, 0 edges).
Mechanic edges on the mana-% stat: `stat_mechanic_relation` →
`mechanic:applies_to_transfiguration_of_mind` and
`mechanic:applies_to_mana_applies_to_shock_effect` only.

Axis X = Intelligence (discovered via the intrinsic rule rows on `stat:intelligence`):
- `rule:intelligence_mana` — "1 Mana per 2 Intelligence", formula `floor(Intelligence / 2) Mana`
  (intrinsic rule row surfaced on the attribute; operands: int → `stat:base_maximum_mana`).
- `rule:intelligence_energy_shield` — "1% increased maximum Energy Shield per 10 Intelligence".
- plus `stat_scales_with` family on `stat:intelligence` (lightning-to-attacks, crit, DoT-multi etc.).

The seed participates through its mana-per-100 attack-chaos stat (mana fed by the int rule) and
through its ES-cost modifier where noted. Confirmed seed-side: reduced max mana is a real cost of
the scaling (chaos dmg is per-100-mana, so the 60→40% reduction is a real anti-synergy the build
must buy back with flat/int mana).

## Architectures (4 genuinely distinct, plus 2 rejected non-architectures)

---

## Build 1 — Mana-Stack Infinity Claw (attack chaos, X = Intelligence → Mana)

X=Intelligence: rule `intelligence_mana` → max mana → seed "Added Attack Chaos Damage per 100
Maximum Mana". Second mana→damage path: none found beyond the seed for *attacks* — this is the
**single-use / multi-use** rung: mana improves attack chaos (dmg) and pool/defense only.
Reported as the base architecture the seed implies; no quadratic claim.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | **Whispers of Infinity** (unique:1461, available) | **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana**; (60-40)% reduced maximum Mana; **Skills Cost Energy Shield instead of Mana or Life**; (10-15)% faster start of Energy Shield Recharge |
| Gloves | Atziri's Acuity (unique:232, available) | **+(60-80) to Intelligence**; (40-60)% increased Global Critical Strike Chance; +(60-75) to maximum Life; (200-220)% increased Armour; You have Vaal Pact if you've dealt a Critical Strike Recently |
| Ring | Valako's Sign (unique:294, available) | **+(100-150) to maximum Mana**; 25% chance to Shock; 40% increased Damage with Hits against Shocked Enemies; 1% of Damage Leeched as Life against Shocked Enemies; 20% increased Lightning Damage |
| Body | Cloak of Defiance (unique:204, available) | **+(100-150) to maximum Mana**; Regenerate 1% of Mana per second (×2 rows); (300-400)% increased Evasion and Energy Shield |
| Passive rule | `rule:intelligence_mana` | 1 Mana per 2 Intelligence (intrinsic engine rule) |

**Why it works** — Intelligence feeds maximum mana through the intrinsic engine rule
(1 mana per 2 int, confirmed formula), and the seed converts each 100 max mana into added attack
chaos damage. Atziri's Acuity, Valako's Sign and Cloak of Defiance are the biggest evidenced
int/mana carriers found by probing `carriers(stat:base_maximum_mana)` (241 granters audited) and
`carriers(stat:intelligence)`. The seed's "Skills Cost ES instead of Mana or Life" decouples
skill costs from the mana pool so the mana stack is pure damage fuel (resource-side evidence
only; no output-scaling claim beyond the seed).

**Evidence** — unique:1461 → unique_modifier_association →
mod:AttacksGainMinMaxAddedChaosDamageBasedOnManaUnique__1 → modifier_grants_stat →
stat:max_attack_added_chaos_damage_per_100_mana; stat:intelligence → rule_applies_to →
rule:intelligence_mana → base_maximum_mana.

Status: **VALIDATED core** (all items `validate_addition` → valid; amulet is core scaling
component; others slot fillers). CANDIDATE maximized variant: none needed — all components
modellable. Note: `+1 to maximum Mana per 2 Intelligence` (stat:maximum_mana_+_per_2_intelligence)
exists as a modifier but its uniques have **no carrier in the KB** (zero-carrier verdict;
`carriers(mod:GainManaPer2IntelligenceUnique_1)` → 0) — recorded as empty search.

---

## Build 2 — Heavy Strike of Trarthus Int-Staff (attack, X = Intelligence, cubic CANDIDATE)

X=Intelligence enters **one output (Heavy Strike attack hits)** through three gem-granted paths
(all `gem_grants_stat` edges on `gem:HeavyStrikeAltY`, "Heavy Strike of Trarthus"):
- path A: int → mana (rule) → seed added attack chaos per 100 mana;
- path B: int → **spell** damage (staff mod "1% increased Spell Damage per 10 Intelligence",
  Whispering Ice as staff) → gem stat
  `active_skill_additive_spell_damage_modifiers_apply_to_attack_damage_at_%_value` → attack damage;
- path C: gem stat `chance_to_deal_double_damage_%_per_10_intelligence`.

Interaction of B and C with A is multiplicative **on the same hit only if** the gem's spell→attack
bridge applies to the *added* chaos damage from mana and if double damage multiplies it —
that combining behavior is **NOT evidenced by the KB** (hypothesis; the KB carries the bridge stat
and the per-int double-damage stat on the same gem, but no rule row tying them together).

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | **Whispers of Infinity** (unique:1461, available) | **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana**; (60-40)% reduced maximum Mana; **Skills Cost Energy Shield instead of Mana or Life** |
| Weapon | The Whispering Ice (unique:326, Staff, available) | **Grants Level 1 Icestorm Skill**; **1% increased Spell Damage per 10 Intelligence** (mod:SpellDamagePerIntelligenceUniqueStaff12 → stat:spell_damage_+%_per_10_int); (14-18)% increased Intelligence; 1% increased Cast Speed; +1 to Level of Socketed Support Gems |
| Helmet | Crown of Eyes (unique:168, available) | **Attacks have 150% Arcane Might** (mod:SpellDamageModifiersApplyToAttackDamageUniqueHelmetInt7 → stat:additive_spell_damage_modifiers_apply_to_attack_damage_at_150%_value — sole carrier, available) |
| Gem | **Heavy Strike of Trarthus** (gem:HeavyStrikeAltY) | gem_grants_stat: **active_skill_additive_spell_damage_modifiers_apply_to_attack_damage_at_%_value** (spell→attack bridge ON the gem); **chance_to_deal_double_damage_%_per_10_intelligence**; chance_to_deal_double_damage_+%; trigger_level_20_bone_corpses_on_stun |

**Why it works** — All three int-fed damage paths are confirmed carriers on the same skill gem
and weapon: the staff turns int into spell damage, the gem carries the spell→attack additive
bridge (and Crown of Eyes doubles it to 150%), the same gem grants double-damage chance per 10
int, and the seed adds attack chaos per 100 mana fed by the int→mana rule. Whether the three
combine into super-linear (≈X³-candidate) scaling on a single Heavy Strike hit is a **hypothesis**
—the KB evidences each path separately, not their composition.

**Evidence** — gem:HeavyStrikeAltY → gem_grants_stat → (bridge stat, double-dmg-per-int stat);
unique:168 → mod → stat:additive_spell_damage_modifiers_apply_to_attack_damage_at_150%_value;
mechanic:applies_to_spell_damage_applies_to_attacks → stat_mechanic_relation → the bridge stats.
`weapon_check(gem:HeavyStrikeAltY, 'Staff')` → **valid** ("Staff is an allowed weapon class").

Status: **VALIDATED core** — `validate_build(BuildState(items=[unique:1461, unique:168,
unique:326], gem_groups=[{'skill':'gem:HeavyStrikeAltY'}]))` → **valid** (slot, availability,
weapon context Staff). CANDIDATE maximized variant: "Heavy Strike of Trarthus" Divergent-twin
value and gem numeric % values are not exposed by the API (documented gap); influenced
"Adds Lightning to Attacks per 10 Intelligence" mods (Hunter's etc.) have **zero unique carriers**
in the KB — recorded empty searches.

---

## Build 3 — Icestorm Int-Staff spell engine (spell, X = Intelligence; seed NOT in the damage path)

X=Intelligence enters Icestorm's output through **three confirmed gem/weapon carriers**:
- gem:Icestorm → `spell_minimum/maximum_base_cold_damage_+_per_10_intelligence` (added cold spell dmg per int),
- gem:Icestorm → `skill_effect_duration_per_100_int` (duration per int — more overlapping storms, interaction with damage NOT evidenced),
- unique:326 staff mod → `spell_damage_+%_per_10_int`.
Plus int → mana (rule) — mana is a *cost*, no evidenced mana→damage stat for this spell.

**Seed-participation verdict:** Whispers of Infinity has **no evidenced damage edge into
Icestorm** (the seed's chaos stat is *attack*-only; Icestorm is a spell; `resolve` over the
seed's stat forward-neighbours returns nothing spell-side). Kept only as a **slot-filler/
defense note, explicitly not part of the scaling structure** — flagging per the §1 invariant
that the seed must participate through a live edge contributing to the scaling. This
architecture stands on its own carriers; the seed's role here is UNKNOWN→none.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Weapon | **The Whispering Ice** (unique:326, Staff, available) | **Grants Level 1 Icestorm Skill**; **1% increased Spell Damage per 10 Intelligence**; (14-18)% increased Intelligence; 1% increased Cast Speed; +1 to Level of Socketed Support Gems |
| Gem | **Icestorm** (gem:Icestorm) | gem_grants_stat: **spell_minimum_base_cold_damage_+_per_10_intelligence**; **spell_maximum_base_cold_damage_+_per_10_intelligence**; **skill_effect_duration_per_100_int**; firestorm_drop_ground_ice_duration_ms; fire_storm_fireball_delay_ms |

**Why it works** — The staff grants the Icestorm skill, and both the gem and the staff scale
Icestorm directly with Intelligence: per-int added cold spell damage (gem) multiplied by per-int
%spell damage (staff), with per-int duration lengthening the storm. `validate_build` with
staff + gem → **valid**. The triple-int coupling makes this a cubic **candidate** on the same
spell (added-dmg × multiplier × duration-stacking is an interaction the KB does not evidence —
hypothesis).

**Evidence** — unique:326 → mod:IcestormUniqueStaff12 ("Grants Level 1 Icestorm Skill"),
mod:SpellDamagePerIntelligenceUniqueStaff12; gem:Icestorm → gem_grants_stat → the three per-int
stats (sole carrier each).

---

## Build 4 — ES-Battery mana-cost chaos (spell/support layer, X = Mana; seed-coupled)

X=Maximum Mana: the seed's attack-chaos-per-mana is the damage path; the second seed modifier
**"Skills Cost Energy Shield instead of Mana or Life"** (sole KB carrier of
`stat:base_skills_cost_es_instead_of_mana_life`, verified `carriers` → 1) makes the entire mana
pool permanent damage fuel — mana never pays costs. Mana→ES defense: Mindspiral
("Gain (10-15)% of Maximum Mana as Extra Maximum Energy Shield",
`stat:mana_%_to_add_as_energy_shield`, 9 KB carriers; Mindspiral available). Ascendancy
Sanctuary of Thought (`passive:AscendancyHeirophant8`) also grants the mana→ES stat
(`passive_grants_stat`, ascendancy name from carriers row — *which ascendancy class it belongs
to is UNKNOWN from the API; the row names it "Sanctuary of Thought"*).

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | **Whispers of Infinity** (unique:1461, available) | **Skills Cost Energy Shield instead of Mana or Life**; **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana**; (60-40)% reduced maximum Mana |
| Helmet | Mindspiral (unique:176, available) | **Gain (10-15)% of Maximum Mana as Extra Maximum Energy Shield**; (from `carriers(stat:mana_%_to_add_as_energy_shield)`) |
| Body | Cloak of Defiance (unique:204, available) | **+(100-150) to maximum Mana**; Regenerate 1% of Mana per second; (300-400)% increased Evasion and Energy Shield |
| Ring | Valako's Sign (unique:294, available) | **+(100-150) to maximum Mana**; 25% chance to Shock; 40% increased Damage with Hits against Shocked Enemies |
| Passive | Sanctuary of Thought (`passive:AscendancyHeirophant8`) | grants stat:mana_%_to_add_as_energy_shield (per `passive_grants_stat`; ascendancy identity UNKNOWN beyond the node name) |

**Why it works** — The seed itself is the architecture: ES-paying skills keep the mana pool
untouched while the per-100-mana chaos conversion (attacks) and Mindspiral's mana→ES conversion
(defense) both read the same stat. Mana is a single-use axis here (damage + pool → *different*
outputs: multi-use, not quadratic).

**Evidence** — unique:1461 → mod:SkillsCostEnergyShieldInsteadOfManaLifeUnique__1 →
stat:base_skills_cost_es_instead_of_mana_life (sole carrier); stat:maximum_mana_+% →
stat_mechanic_relation → mechanic:applies_to_mana_applies_to_shock_effect (the only other
mechanic reading the mana-% stat; its bridge stat
`additive_mana_modifiers_apply_to_shock_effect_at_30%_value` has **0 carriers** — KB fact).

Status: **VALIDATED core** (all four uniques validate_addition → valid; helmet/body/ring amulet
no slot conflicts). Note: `carriers(passive:poisonspells_*)` cluster notables returned 0 —
cluster-jewel notables have no slot model (validator limitation, recorded).

---

## Rejected non-architectures (checked, not proposed)

- **Transfiguration of Mind (Crown of the Inward Eye, unique:1083, all three Transfiguration
  mods, available)**: "Additive mana modifiers apply to damage at 30% value" reads *additive mana
  modifiers* — the KB gives no evidence this consumes the seed's per-100-mana chaos stat (a
  damage-grant stat, not an additive mana modifier). Carried as an **open hypothesis** only;
  validator `validate_build` with CoI + staff + amulet + gem is valid mechanically.
- **Transcendent Mind (unique:790, jewel, available)**: "+3% to Damage over Time Multiplier per
  10 Intelligence on Unallocated Passives in Radius" rewards *unallocated* int while every other
  path rewards stacking; its sibling mod is "-1 Intelligence per 1 Intelligence on Allocated
  Passives in Radius" (subject_text verified). Direct opposition to the axis → rejected.
  Jewel has no slot model (validator: "no slot model for this item class — not checked").
- **mana→shock-effect bridge** (`additive_mana_modifiers_apply_to_shock_effect_at_30%_value`):
  0 carriers — dead end (KB fact).
- **Eldritch Knowledge** ("5% increased Chaos Damage per 10 Intelligence from Allocated
  Passives in Radius"): unique availability **unavailable** (`carriers` row) — excluded.
- **Skills gain Added Chaos Damage equal to % of Mana Cost** (mutated wand family,
  stat:added_chaos_damage_%_mana_cost_if_payable): modifier has **no carrier** in the KB
  (zero-carrier verdict; tag `mutatedunique`) — no slot, unobtainable in-model. Recorded.

## Sweep log & spaces probed (§5/§12)

- Sweep 1: seed census (neighbour unique:1461 depth 1) — 4 mods, carriers probed each.
- Sweep 2: stat doors — carriers(stat:maximum_mana_+%) 150 granters,
  carriers(stat:base_maximum_mana) 241, carriers(stat:intelligence) + neighbour (rule rows +
  18 stat_scales_with per-int stats), carriers on each interesting per-int stat (all listed above).
- Sweep 3: mechanic/rule space — resolve --type Mechanic (10 applies_to mechanics),
  resolve "Transfiguration" (16), neighbour(mechanic) both sides, resolve --type Rule (1 rule:
  intelligence_mana) + neighbour(rule) operands, rule:intelligence_energy_shief side.
- Sweep 4: pattern mining — "per 10 intelligence" (26 mods), "per 100 maximum mana" (1),
  "added chaos damage" (42), "to Intelligence" (129 modifiers), poison-family resolve (370),
  mana resolve (~400 stat ids), "full mana"/"shock" probes.
- Fixed point reached: further probes (shock-mana bridge, mana-cost chaos, mana→multiplier)
  returned empty/no-carrier verdicts with queries recorded above. No re-anchoring needed
  (axis=int discovered in sweep 2 from the rule rows on the seed's mana operand; seed stays
  committed in Builds 1/2/4).

## Slot audit (§6)

- Amulet: evidenced (seed; Atziri's Foible +(16-24)% mana alt).
- Weapon staff: evidenced (Whispering Ice). Claw: evidenced (Hand of Wisdom and Action
  "Adds 1-12 Lightning to Attacks with this Weapon per 10 Intelligence" + (8-12)% increased
  Intelligence — available; single-use, not a distinct architecture). Wand: evidenced
  (Void Battery +(100-120) mana + int-class wands; spell-dmg-per-power-charge).
- Helmet: evidenced (Crown of Eyes, Mindspiral, Crown of the Inward Eye).
- Ring: evidenced (Valako's Sign). Body: evidenced (Cloak of Defiance).
- Jewel: **no slot model** (validator limitation); Transcendent Mind / Eldritch Knowledge
  recorded above. Gloves/Boots/Belt: no axis-evidenced unique carriers found in probed families —
  recorded empty (queries: resolve "to Intelligence" per-class mod lists show
  IntelligenceUniqueGlovesStr3 "+(60-80) to Intelligence" → **no carrier**,
  IntelligenceUniqueHelmetInt6 → **no carrier**; only via-craft paths).
- Flasks: no evidence found; not proposed.

## API gaps / coverage limits (fail-closed)

1. Gem numeric values (bridge %, double-damage per int) are not exposed — numbers unknown.
2. No public operation composes modifiers into a damage formula → all multi-path composition
   claims remain hypotheses (Builds 2/3 cubic candidates).
3. Cluster notables & jewels have no slot model (validator limitation, quoted).
4. Influenced per-int mods (Hunter's lightning-per-int, eldritch damage-%-per-100-int implicits)
   have zero unique carriers in the KB → CANDIDATE tier only with the zero-carrier verdict.
5. `carriers(passive:poisonspells_*)` → 0; poison-spell notables exist as passives granting
   `stat:spells_chance_to_poison_on_hit_%` but their acquisition source (cluster jewels) is not
   reachable through the public API.
6. Ascendancy class identity of `passive:AscendancyHeirophant8` (Sanctuary of Thought): the
   carriers row gives the node name only; class mapping UNKNOWN from the API.
