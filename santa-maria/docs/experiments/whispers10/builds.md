# Whispers of Infinity — build sheets (whispers10)

Five architectures, each rendered in two tiers. **VALIDATED** = the listed components passed
`validate_build(final=True)` — which means only "valid with respect to the constraints
implemented and checked by this validator (slot occupancy, weapon configuration, gem
supportability, ascendancy composition); NOT a full PoE build-validity claim".
**CANDIDATE** = adds components the validator cannot model; every such component carries its
exact quoted verdict. No modifier, influence, ascendancy, or availability fact below was
supplied from outside the Research API.

> **Prose provenance.** Equipment rows quote the exact modifier `text` field. **Passive and Gem
> rows have no `text` payload in the API** — their entries are rendered from the granted
> `stat:` ids and are marked *(from stat id)* below. They are the KB's canonical mechanical
> names, not verified game wording; no passive or gem wording was reconstructed from memory.

---

## Build 1 — Twice-Mana Bridge

Maximum mana feeds the same attack twice: once as flat added chaos from the seed, once as a
spell-damage percentage that Crown of Eyes and the gem route into attack damage. Maximum mana
therefore scales the amount *and* the multiplier of one hit.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | **Whispers of Infinity** | **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana**<br>**(60-40)% reduced maximum Mana**<br>**(10-15)% faster start of Energy Shield Recharge**<br>**Skills Cost Energy Shield instead of Mana or Life** |
| Helmet | **Crown of Eyes** | **Attacks have 150% Arcane Might**<br>-30% to Fire Resistance<br>+(300-350) to Accuracy Rating<br>(0.4-0.8)% of Attack Damage Leeched as Life<br>(120-150)% increased Energy Shield<br>(0.2-0.4)% of Attack Damage Leeched as Mana |
| Weapon | Fencoil | (40-50)% increased Global Damage<br>Socketed Gems are Supported by Level 8 Trap<br>(10-20)% increased maximum Life<br>**(10-20)% increased maximum Mana**<br>+20% Chance to Block Spell Damage |
| Gloves | Shaper's Touch | **+2 Accuracy Rating per 2 Intelligence**<br>1% increased Energy Shield per 10 Strength<br>2% increased Evasion Rating per 10 Intelligence<br>+1 Life per 4 Dexterity<br>+1 Mana per 4 Strength<br>2% increased Melee Physical Damage per 10 Dexterity |
| Skill gem | Heavy Strike of Trarthus | *(from stat ids — no gem `text` in API)* Requires Staff or Warstaff (`weapon_check`: `valid` — "Staff is an allowed weapon class"). Grants `stat:chance_to_deal_double_damage_%_per_10_intelligence`, `stat:chance_to_deal_double_damage_%`, `stat:attack_speed_+%`, `stat:damage_+%`, `stat:active_skill_additive_spell_damage_modifiers_apply_to_attack_damage_at_%_value`. Tag: `attack`. |
| Passives | Mana and Spell Damage (minor) *(from stat ids)* | `stat:maximum_mana_+%`; `stat:spell_damage_+%` |
| Passives | **Prodigal Perfection** (notable) *(from stat ids)* | `stat:maximum_mana_+%`; `stat:spell_damage_+%_per_100_maximum_mana_up_to_60%` |
| Passives | Deep Thoughts (notable) *(from stat ids)* | `stat:base_intelligence`; `stat:mana_regeneration_rate_+%`; `stat:maximum_mana_+%` |
| Ascendancy | **Hierophant** — *Divine Guidance* (notable), *Sanctuary of Thought* (notable) *(from stat ids)* | Divine Guidance → `stat:maximum_mana_+%`; Sanctuary of Thought → `stat:guardian_reserved_mana_%_given_to_you_and_nearby_allies_as_base_maximum_energy_shield`. Both returned `passive_info.ascendancy: "Hierophant"`, `is_notable: true`; exactly one Ascendancy in the final state. |

**Status: VALIDATED** (all components `valid`, final build `valid`).

**Why it works.** Intelligence raises base maximum mana through a KB engine edge, and mana
percentage raises it again, so the pool grows from two directions. The seed converts that pool
into flat added chaos on every attack. Prodigal Perfection converts the same pool into spell
damage percentage, which Crown of Eyes and the Trarthus gem route into attack damage. Two
mana-fed legs land on one hit.

**Evidence**
- Intelligence → base maximum mana → *(seed)* → Added Attack Chaos Damage
- maximum Mana → increased Spell Damage (up to 60%) → *Arcane Might* → attack damage
- increased Spell Damage → operand of *"additive spell damage modifiers apply to attack damage"*
- Accuracy: Shaper's Touch "+2 Accuracy Rating per 2 Intelligence" (sole carrier)

**CANDIDATE maximized variant** (not validator-checked; exact reasons quoted)
- Body Armour with **(9-11)% increased maximum Mana** *(Shaper's)* — `valid`, "influence compatible with class" (`mod:MaximumManaBodyUber1`); the tier-2 **(12-15)%** roll (`mod:MaximumManaBodyUber2`) is the same shape. Both are influence-tagged mods with **no unique carrier** — `carriers` returns only `modifier_grants_stat`, `unique_modifier_association: 0`.
- **Healthy Mind** (Jewel) — "Increases and Reductions to Life in Radius are Transformed to apply to Mana at **200%** of their value" + (15-20)% increased maximum Mana. Validator: `unknown`, reason *"Healthy Mind (Jewel): no slot model for this item class — not checked"*.
- **Unknown:** whether the mana-scaling spell-damage leg is actually picked up by the Arcane Might bridge. The bridge binds only the canonical `stat:spell_damage_+%`; `neighbour stat:spell_damage_+%_per_100_maximum_mana_up_to_60%` returns **no** `stat_mechanic_*` rows.

---

## Build 2 — Intelligence Double-Strike

Intelligence is the only investment. It buys maximum mana, which buys the seed's flat chaos, and
it separately buys double-damage chance on the gem. Both legs are direct stat grants — no
mechanic binding is needed to establish them.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | **Whispers of Infinity** | **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana**<br>**(60-40)% reduced maximum Mana**<br>**(10-15)% faster start of Energy Shield Recharge**<br>**Skills Cost Energy Shield instead of Mana or Life** |
| Weapon | Fencoil | (40-50)% increased Global Damage<br>Socketed Gems are Supported by Level 8 Trap<br>(10-20)% increased maximum Life<br>**(10-20)% increased maximum Mana**<br>+20% Chance to Block Spell Damage |
| Gloves | Shaper's Touch | **+2 Accuracy Rating per 2 Intelligence**<br>1% increased Energy Shield per 10 Strength<br>2% increased Evasion Rating per 10 Intelligence<br>+1 Life per 4 Dexterity<br>+1 Mana per 4 Strength<br>2% increased Melee Physical Damage per 10 Dexterity |
| Skill gem | Heavy Strike of Trarthus | *(from stat ids)* Requires Staff or Warstaff (`valid`). **`stat:chance_to_deal_double_damage_%_per_10_intelligence`** (sole carrier), `stat:chance_to_deal_double_damage_%`, `stat:attack_speed_+%`, `stat:damage_+%`, spell→attack bridge. Tag: `attack`. |
| Passives | **Utmost Intellect** (notable) *(from stat ids)* | `stat:base_intelligence`; `stat:intelligence_+%` |
| Passives | **Arcane Conservation** (notable) *(from stat ids)* | `stat:base_intelligence`; `stat:maximum_energy_shield_+%`; `stat:energy_shield_delay_-%` |
| Ascendancy | **Hierophant** — *Divine Guidance* (notable) *(from stat ids)* | `stat:maximum_mana_+%` |

**Status: VALIDATED** (all components `valid`, final build `valid`).

**Why it works.** Utmost Intellect and Arcane Conservation both grant base Intelligence, and
Intelligence grants base maximum mana through a confirmed engine edge. That mana becomes flat
added chaos damage on every attack. The same gem turns Intelligence directly into
double-damage chance, so the flat chaos is what gets doubled. Strongest evidence chain of the
run: every leg is a direct `*_grants_stat` edge or an `attribute_grants_stat` edge.

**Evidence**
- Intelligence → base maximum mana → *(seed)* → Added Attack Chaos Damage
- Intelligence → chance to deal double damage (per 10 Intelligence)
- Accuracy: Shaper's Touch "+2 Accuracy Rating per 2 Intelligence"

**CANDIDATE maximized variant**
- Body Armour with **(9-11)% increased maximum Mana** *(Shaper's)* — `valid`, "influence compatible with class".
- **Unknown:** whether double damage multiplies the hit's added flat damage. The KB carries
  `stat:chance_to_deal_double_damage_%` but has no edge expressing the multiplication — the
  quadratic classification rests on engine semantics, not on a graph edge.
- *Rejected as a component here:* **Indigon** — its "(20-25)% increased Spell Damage for each
  200 total Mana you have Spent Recently, up to 2000%" is **dead**, because the seed pays skill
  costs in Energy Shield, so mana is never spent. It also occupies the helmet slot this build
  leaves free for a mana-to-ES or mana-to-lightning item.

---

## Build 3 — Mana-as-Energy-Shield

The seed swaps the fuel: skills are paid in Energy Shield, so mana is never spent and becomes a
pure pool. Mindspiral turns that pool into the Energy Shield that actually pays for skills.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | **Whispers of Infinity** | **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana**<br>**(60-40)% reduced maximum Mana**<br>**(10-15)% faster start of Energy Shield Recharge**<br>**Skills Cost Energy Shield instead of Mana or Life** |
| Helmet | **Mindspiral** | **Gain (10-15)% of Maximum Mana as Extra Maximum Energy Shield**<br>**+(100-120) to maximum Mana**<br>(10-20)% of Damage taken Recouped as Mana<br>Enemies Cannot Leech Mana From you |
| Passives | **Arcane Focus** (notable) *(from stat ids)* | `stat:base_intelligence`; `stat:maximum_energy_shield_+%`; `stat:energy_shield_delay_-%` |
| Passives | Energy Shield and Mana (minor) *(from stat ids)* | `stat:maximum_energy_shield_+%`; `stat:maximum_mana_+%` |
| Ascendancy | **Hierophant** — *Sanctuary of Thought* (notable) *(from stat ids)* | `stat:guardian_reserved_mana_%_given_to_you_and_nearby_allies_as_base_maximum_energy_shield` (sole carrier) |

**Status: VALIDATED** (all components `valid`, final build `valid`). No weapon and no gem are
committed — nothing in this architecture is weapon- or gem-gated, so the validator had no
weapon context to check and none was invented.

**Why it works.** Mindspiral adds a percentage of maximum mana as extra maximum Energy Shield,
so mana feeds the pool that the seed makes spendable. Arcane Focus grants Intelligence, and
Intelligence grants Energy Shield percentage through a confirmed engine edge *and* grants base
maximum mana, which feeds Mindspiral's conversion — two Intelligence-fed legs into one pool.
Sanctuary of Thought adds a third, reservation-based mana-to-shield path.

**Evidence**
- Skills Cost Energy Shield instead of Mana or Life → the ES pool is spent, not the mana pool
- maximum Mana → Extra Maximum Energy Shield (Mindspiral)
- Intelligence → maximum Energy Shield % **and** Intelligence → base maximum Mana
- reserved Mana → base maximum Energy Shield (Sanctuary of Thought)

**CANDIDATE maximized variant**
- **Healthy Mind** (Jewel) — "Increases and Reductions to Life in Radius are Transformed to apply
  to Mana at 200% of their value" + (15-20)% increased maximum Mana — a *third* generator that
  raises mana without Intelligence. Validator: `unknown`, reason *"Healthy Mind (Jewel): no slot
  model for this item class — not checked"*.
- Body Armour **(9-11)% increased maximum Mana** *(Shaper's)* — `valid`, "influence compatible with class".
- **Not usable here:** **The Scales of Justice** — "Has no Energy Shield" (`mod:NoEnergyShieldUnique__1`).
  Hard semantic conflict with the seed's cost-swap; the validator does not model it.
- **Recorded empty:** the Clarity path "Gain (6-10)% of Maximum Mana as Extra Maximum Energy
  Shield while affected by Clarity" — `carriers` → `total=0`; and the mutated body-armour
  variants (15-20%) — `total=0`.

---

## Build 4 — Two Mana Consumers, One Damage Type

Two different maximum-mana consumers exist — the seed's chaos and the Trarthus gem's physical —
and a ring converts the physical half into chaos, so both land in the same output type.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | **Whispers of Infinity** | **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana**<br>**(60-40)% reduced maximum Mana**<br>**(10-15)% faster start of Energy Shield Recharge**<br>**Skills Cost Energy Shield instead of Mana or Life** |
| Ring | **Ming's Heart** | **Gain (40-60)% of Physical Damage as Extra Chaos Damage**<br>+(40-50)% to Chaos Resistance<br>25% reduced maximum Life<br>25% reduced maximum Energy Shield |
| Weapon | Reverberation Rod | Adds (1-2) to (9-11) Lightning Damage to Spells and Attacks<br>Socketed Gems are Supported by Level 10 Controlled Destruction<br>**+(10-30) to Intelligence**<br>+2 to Level of Socketed Gems<br>Socketed Gems are Supported by Level 10 Arcane Surge<br>Socketed Gems are Supported by Level 10 Spell Echo<br>Socketed Gems are Supported by Level 10 Spell Echo |
| Skill gem | **Kinetic Blast of Clustering** *(from stat ids)* | Requires Wand (`valid` — "Wand is an allowed weapon class"). Grants `stat:added_physical_damage_to_attacks_equal_to_%_maximum_mana` (sole carrier) + `stat:active_skill_additive_spell_damage_modifiers_apply_to_attack_damage_at_%_value`. |
| Passives | Deep Thoughts (notable) *(from stat ids)* | `stat:base_intelligence`; `stat:mana_regeneration_rate_+%`; `stat:maximum_mana_+%` |
| Ascendancy | **Hierophant** — *Divine Guidance* (notable) *(from stat ids)* | `stat:maximum_mana_+%` |

**Status: VALIDATED** (all components `valid`, final build `valid`).

**Why it works.** The seed turns maximum mana into flat chaos on attacks. Kinetic Blast of
Clustering turns the same maximum mana into flat physical on attacks. Ming's Heart converts
physical damage into extra chaos, so the mana-derived physical contribution is re-typed into the
seed's damage type instead of being wasted. Reverberation Rod's Intelligence feeds the mana pool
that both consumers read.

**Evidence**
- maximum Mana → Added Attack Chaos Damage *(seed)*
- maximum Mana → added physical damage to attacks *(Kinetic Blast of Clustering)*
- Physical Damage → Extra Chaos Damage *(Ming's Heart)*
- **Ladder: multi-use, not quadratic.** The two chaos legs add rather than multiply — both are
  linear in mana. The mana × converter-% pair is an interacting two-input product, but it is not
  one axis scaling twice.

**CANDIDATE maximized variant**
- Body Armour **(9-11)% increased maximum Mana** *(Shaper's)* — `valid`, "influence compatible with class".
- **Alternative converters, same stat family** (choose one, ring/quiver/wand contention):
  **Obliteration** (Wand) 30-40%; **Spinehail** and **Maloney's Nightfall** (Quiver) 10-15%.
  All `available`.
- **Recorded empty:** `stat:lightning_damage_%_to_convert_to_chaos` → `total=0`. The
  Mind of the Council's "Attack Skills have Added Lightning Damage equal to 6% of maximum Mana"
  therefore **cannot** be routed into chaos; that mana consumer stays out of this architecture.

---

## Build 5 — Lowest-of-Pool Fire

The one architecture where the seed is a tax rather than a driver. The Scales of Justice scales
off the *lower* of maximum life and maximum mana, and the seed's 40-60% mana reduction lowers
that minimum.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | **Whispers of Infinity** | **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana**<br>**(60-40)% reduced maximum Mana** *(a direct drag on this build's axis)*<br>**(10-15)% faster start of Energy Shield Recharge**<br>**Skills Cost Energy Shield instead of Mana or Life** |
| Off-hand | **The Scales of Justice** | **(3-4) to (7-8) added Fire Damage per 100 of Maximum Life or Maximum Mana, whichever is lower**<br>**Unaffected by Ignite or Shock if Maximum Life and Maximum Mana are within 500**<br>**Has no Energy Shield**<br>+(40-70) to maximum Life<br>(10-15)% increased Spell Damage |
| Weapon | Reverberation Rod | Adds (1-2) to (9-11) Lightning Damage to Spells and Attacks<br>Socketed Gems are Supported by Level 10 Controlled Destruction<br>**+(10-30) to Intelligence**<br>+2 to Level of Socketed Gems<br>Socketed Gems are Supported by Level 10 Arcane Surge<br>Socketed Gems are Supported by Level 10 Spell Echo<br>Socketed Gems are Supported by Level 10 Spell Echo |
| Skill gem | Kinetic Blast of Clustering *(from stat ids)* | Requires Wand (`valid`). |
| Passives | Deep Thoughts (notable) *(from stat ids)* | `stat:base_intelligence`; `stat:mana_regeneration_rate_+%`; `stat:maximum_mana_+%` |
| Ascendancy | **Hierophant** — *Divine Guidance* (notable) *(from stat ids)* | `stat:maximum_mana_+%` |

**Status: VALIDATED** (all components `valid`, final build `valid`).

**Why it works.** The shield's fire damage reads the smaller of the two pools, so the seed's
mana reduction sets the ceiling while the shield's own +(40-70) life raises the other side. Its
second modifier only triggers while maximum life and maximum mana are within 500 of each other,
which forces both pools up together — a proximity condition, not a flat bonus. The seed's own
chaos damage rides along as a separate chaos source.

**Evidence**
- minimum(Maximum Life, Maximum Mana) → added Fire Damage *(The Scales of Justice)*
- **maximum Mana −40/-60% → lowers that minimum** *(the seed, working against its own axis)*
- (60-40)% reduced maximum Mana and max-life proximity condition interact: both pools must rise together

**CANDIDATE maximized variant**
- Body Armour **(9-11)% increased maximum Mana** *(Shaper's)* — `valid`, "influence compatible
  with class". **Note the perverse incentive:** this *raises* the axis the seed lowers, so on
  this build the seed's penalty shrinks as mana grows.
- **Hard conflict, stated not hidden:** "Has no Energy Shield" contradicts the seed's
  "Skills Cost Energy Shield instead of Mana or Life". The validator does not model stat-level
  conflicts (only slot occupancy, weapon configuration, gem supportability, ascendancy
  composition), so this composition is `valid` *and* semantically contradictory. Treat Build 5
  as a mana-tax study, not a shippable build.
- Validator-recorded conflicts for this slot pair: The Scales of Justice with any two-handed main
  hand → `INVALID`, *"offhand: shield requires a one-handed main weapon"*.
- **Not usable here:** the entire mana-spent family — Indigon, Dark Bargain, Forbidden Rite,
  Manabond — all require mana to be spent, which the seed prevents.

---

## Availability ledger (all four values)

| item | class | availability |
|---|---|---|
| Whispers of Infinity | Amulet | available |
| Crown of Eyes | Helmet | available |
| Mindspiral | Helmet | available |
| Mind of the Council | Helmet | available |
| Ming's Heart | Ring | available |
| Obliteration | Wand | available |
| Spinehail / Maloney's Nightfall | Quiver | available |
| The Scales of Justice | Shield | available |
| Fencoil / Dying Breath | Staff | available |
| Reverberation Rod / Moonsorrow / Midnight Bargain / Amplification Rod | Wand | available |
| Shaper's Touch | Gloves | available |
| Voll's Protector | Body Armour | available |
| Omeyocan | Boots | available |
| Graven's Secret | Belt | available |
| Chober Chaber | Mace | available |
| Healthy Mind | Jewel | available |
| Spirited Response / Chaber Cairn / Mirebough | Jewel / Mace / Staff | **unavailable** |
| Mindspiral + Crown of Eyes together | Helmet | **conflict** — `INVALID`, *"head: capacity 1 exceeded (2 slot units) — Crown of Eyes conflicts with Mindspiral"* |

Ascendancy: **UNKNOWN where not named.** Every build above names exactly one Ascendancy
(Hierophant) with the specific notables the API returned (`is_notable: true`,
`passive_info.ascendancy: "Hierophant"`). No other notable is inferred.