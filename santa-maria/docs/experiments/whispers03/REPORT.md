# whispers03 — Builds around Whispers of Infinity (unique:1461)

Clean-slate discovery run (2026-09-18). Seed: `unique:1461` Whispers of Infinity — Amulet, availability: **available**.
All facts from the public Research API (`resolve` / `carriers` / `neighbour` / phase7 validator). No pretraining-derived claims; every unverified relationship is marked hypothesis/unknown.

## Seed modifiers (resolved text)

| Mod | Text |
| --- | --- |
| mod:AttacksGainMinMaxAddedChaosDamageBasedOnManaUnique__1 | **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana** |
| mod:PercentReducedMaximumManaUnique_1 | (60-40)% reduced maximum Mana |
| mod:SkillsCostEnergyShieldInsteadOfManaLifeUnique__1 | **Skills Cost Energy Shield instead of Mana or Life** |
| mod:ReducedEnergyShieldDelayImplicit1_ | (10-15)% faster start of Energy Shield Recharge |

Central axis **X = Maximum Mana**. The seed contributes: X → attack chaos damage (A-path), resource conversion to ES (enabler), faster ES recharge (defense-side sustain), and a 40–60% max-mana **tax on its own axis** (must be offset by generators).

## Carried mana→output paths (live KB, all carriers verified via `carriers`)

| Stat (id) | Readable text | Carriers |
| --- | --- | --- |
| stat:min/max_attack_added_chaos_damage_per_100_mana | (5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana | Whispers of Infinity only |
| stat:base_skills_cost_es_instead_of_mana_life | Skills Cost Energy Shield instead of Mana or Life | Whispers of Infinity only |
| stat:attack_skills_have_added_lightning_damage_equal_to_%_of_maximum_mana | Attack Skills have Added Lightning Damage equal to 6% of maximum Mana | Mind of the Council (unique:533), gem:PowerSiphonAltX |
| stat:added_physical_damage_to_attacks_equal_to_%_maximum_mana | (gem stat; wording unresolved) | gem:KineticBlastAltX |
| stat:skill_has_added_lightning_damage_equal_to_%_of_maximum_mana | (gem stat; wording unresolved) | gem:ManaInfusedStaff |
| stat:spell_damage_+%_per_100_maximum_mana_up_to_60% | (passive stat; wording unresolved, capped at 60%) | passive Prodigal Perfection (passive:mana_spell_damage_notable2609) |
| stat:bladefall_volley_frequency_+%_per_100_maximum_mana | (gem stat; wording unresolved) | gem:BladefallAltZ |
| stat:spell_damage_+%_per_500_maximum_mana | (6-8)% / (12-14)% increased Spell Damage per 500 Maximum Mana | Synthesis implicit mods only — **zero unique carriers** |
| stat:attack_damage_+%_per_500_maximum_mana | (6-8)% / (12-14)% increased Attack Damage per 500 Maximum Mana | Synthesis implicit mods only — **zero unique carriers** |

Zero-carrier mods probed and recorded as **true absence** in the live KB (empty `carriers`, no `excluded_*` caveat): VillageAttackFireDamageMaximumMana ("Adds 5% of your Maximum Mana as Fire Damage to Attacks with this Weapon"), DodgeAndSpellDodgePerMaximumManaUnique__1 (evasion per 500 mana), ClarityManaAddedAsEnergyShield, `maximum_mana_%_to_convert_to_armour_at_doubled_value` (no carrier at all), IncreasedManaUnique__19 (+500 mana), DivergentAttackLightningDamageMaximumManaUnique__1__ (vestigial alt-quality twin, no unique carries it).

---

# Build 1 — Mana-Battery Chaos Attack (amulet-led)

The amulet is the damage core: attacks gain chaos damage scaled by maximum mana, while every skill cost is paid from Energy Shield, leaving mana untouched as a pure stat battery.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | Whispers of Infinity *(unique:1461, available)* | **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana**; (60-40)% reduced maximum Mana; **Skills Cost Energy Shield instead of Mana or Life**; (10-15)% faster start of Energy Shield Recharge |
| Ascendancy | Hierophant | selected mana nodes (see below); one ascendancy only |
| Passive | Deep Wisdom *(passive:deep_wisdom900, notable)* | grants stat:base_maximum_mana (flat maximum mana; exact wording unresolved) |
| Passive | Path of the Savant *(passive:path_of_the_savant1538, notable)* | grants stat:base_maximum_mana (exact wording unresolved) |
| Passive | Mana *(passive:mana768, small node)* | grants stat:base_maximum_mana (exact wording unresolved) |
| Passive | Hierophant mana nodes *(AscendancyHeirophant4_/5/6)* | grant stat:maximum_mana_+% (exact wording/values unresolved) |
| Passive | Divine Guidance *(passive:AscendancyHeirophant7, Hierophant notable)* | grants stat:maximum_mana_+% (exact wording unresolved) |

**Status: VALIDATED** (validate_build final=True: valid — slot occupancy, weapon configuration, ascendancy composition; NOT a full PoE build-validity claim).

**Why it works** — The amulet converts maximum mana into added attack chaos damage; its other mods reroute all skill costs to Energy Shield, so the mana pool is never spent and can be stacked with flat-mana gear/passives despite the amulet's own 40–60% reduced mana. Faster ES recharge start supports the ES-paid cost loop. Chaos is the only carried damage type with no other KB-evidenced mana-scaling competitors on this amulet, making the amulet itself the unremovable core.

**Evidence**
- unique:1461 → unique_modifier_association → mod:AttacksGainMinMaxAddedChaosDamageBasedOnManaUnique__1 → stat:min/max_attack_added_chaos_damage_per_100_mana (confirmed)
- unique:1461 → unique_modifier_association → mod:SkillsCostEnergyShieldInsteadOfManaLifeUnique__1 → stat:base_skills_cost_es_instead_of_mana_life (confirmed)
- passives → passive_grants_stat → stat:base_maximum_mana / stat:maximum_mana_% (confirmed carriers)

**Quadratic check (hypothesis):** the only attack-damage *multiplier* per mana in the KB is the Synthesis implicit "increased Attack Damage per 500 Maximum Mana" — it has **zero unique associations** (obtainability/slot not exposed by the API). With it, X → added chaos (A) and X → multiplier (B) would be quadratic; without it, Build 1 is single-path. Treated as API GAP / hypothesis, not a claim.

---

# Build 2 — Lightning Battery (Mind of the Council helmet)

A dual-source attack battery: maximum mana feeds added lightning (helmet) and added chaos (amulet) to the same attacks, and the mana pool doubles as a lightning-damage buffer.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | Whispers of Infinity *(unique:1461, available)* | **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana**; (60-40)% reduced maximum Mana; **Skills Cost Energy Shield instead of Mana or Life**; (10-15)% faster start of Energy Shield Recharge |
| Helmet | Mind of the Council *(unique:533, available)* | **Attack Skills have Added Lightning Damage equal to 6% of maximum Mana**; Lose 3% of Mana when you use an Attack Skill; **30% of Lightning Damage is taken from Mana before Life**; +20% chance to be Shocked; +local Energy Shield (mod:LocalIncreasedEnergyShieldUnique__29, value unresolved); +local Evasion/ES (mod:LocalIncreasedEvasionAndEnergyShieldUnique__3, values unresolved) |
| Weapon | Piscator's Vigil *(unique:239, wand, available — slot filler)* | +*(340-400)* to Accuracy Rating; Cannot roll Caster Modifiers; *(20-30)%* increased Critical Strike Chance; *(10-18)%* increased Attack Speed; No Physical Damage; **Attacks with this Weapon have *(100-115)%* increased Elemental Damage**; Damage with Weapons Penetrates 5% Elemental Resistances |
| Skill gem | gem:PowerSiphonAltX *(display name unresolved — id references base "Power Siphon"; alternate-variant gem)* | grants stat:attack_skills_have_added_lightning_damage_equal_to_%_of_maximum_mana (values unresolved); power-charge-on-hit stats (wording unresolved); wand-projectile attack skill |
| Passive | Deep Wisdom *(notable)* | flat maximum mana (wording unresolved) |
| Passive | Mana *(passive:mana768, small node)* | flat maximum mana (wording unresolved) |
| Passive | Hierophant mana nodes + Divine Guidance | stat:maximum_mana_+% (values unresolved) |

**Status: VALIDATED** (final=True: valid; Power Siphon AltX weapon check: "Wand is an allowed weapon class").

**Why it works** — Maximum mana enters attack damage through two confirmed carried paths (helmet lightning + amulet chaos), and the ES-cost conversion on the amulet absorbs all skill costs so only the helmet's 3%-mana-per-attack touches the pool. The helmet's 30%-lightning-from-mana-before-life turns the same pool into lightning defense; both paths scale with X but are independent consumers (multi-use, not quadratic — no carried attack multiplier per mana exists in the KB).

**Evidence**
- unique:533 → mod:AttackLightningDamageMaximumManaUnique__1__ → stat:attack_skills_have_added_lightning_damage_equal_to_%_of_maximum_mana (confirmed)
- unique:533 → mod:PercentLightningDamageTakenFromManaBeforeLifeUnique__1 (confirmed, defense path)
- unique:1461 chaos path (confirmed, as Build 1)
- gem:PowerSiphonAltX → gem_grants_stat → same lightning stat (confirmed; stacking of gem + helmet = hypothesis, KB does not state they combine)

**Unknowns** — whether "Lose 3% of Mana" still triggers when skills pay costs as ES (no KB edge); Shocked downside unmitigated in this committed set.

---

# Build 3 — Cluster Kinetic Blast (phys added-per-mana wand attack)

A projectile AoE architecture: the alternate Kinetic Blast gem itself converts maximum mana into added physical attack damage, and its variant behavior turns projectile-count modifiers into cluster-count instead.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | Whispers of Infinity *(unique:1461, available)* | **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana** (secondary path: same attacks, chaos); (60-40)% reduced maximum Mana; **Skills Cost Energy Shield instead of Mana or Life**; (10-15)% faster start of Energy Shield Recharge |
| Weapon | Piscator's Vigil *(unique:239, wand, available — slot filler)* | +*(340-400)* to Accuracy Rating; **Cannot roll Caster Modifiers**; *(20-30)%* increased Critical Strike Chance; *(10-18)%* increased Attack Speed; No Physical Damage; Attacks with this Weapon have *(100-115)%* increased Elemental Damage; Damage with Weapons Penetrates 5% Elemental Resistances |
| Skill gem | gem:KineticBlastAltX *(display name unresolved — id references base "Kinetic Blast"; alternate-variant gem)* | grants stat:added_physical_damage_to_attacks_equal_to_%_maximum_mana (values unresolved); **stat:kinetic_blast_modifiers_to_number_of_projectiles_instead_apply_to_number_of_clusters**; stat:active_skill_additive_spell_damage_modifiers_apply_to_attack_damage_at_%_value; stat:projectiles_cannot_split; tags: attack, physical (remaining gem stats unresolved) |
| Passive | Deep Wisdom *(notable)* | flat maximum mana (wording unresolved) |
| Passive | Hierophant mana nodes + Divine Guidance | stat:maximum_mana_+% (values unresolved) |

**Status: VALIDATED** (final=True: valid; Kinetic Blast AltX weapon check: "Wand is an allowed weapon class").

**Why it works** — The gem is a carried X→damage path (added phys = % of maximum mana) distinct from the amulet's chaos path, and the same gem converts projectile modifiers into cluster counts, making area/extra-projectile investment a different scaling surface than the raw mana axis. The gem's spell-damage-mods-apply-to-attack-damage stat is a second possible bridge (spell scaling onto attacks) — interaction values unresolved.

**Evidence**
- gem:KineticBlastAltX → gem_grants_stat → stat:added_physical_damage_to_attacks_equal_to_%_maximum_mana (confirmed)
- gem:KineticBlastAltX → stat:kinetic_blast_modifiers_to_number_of_projectiles_instead_apply_to_number_of_clusters (confirmed)
- unique:1461 chaos path (confirmed)

**Unknowns** — Piscator's Vigil "No Physical Damage" (weapon-local) vs. gem-added physical damage: no KB edge states how these interact. Whether the gem's added-phys stat and the amulet's added-chaos-per-mana combine on the same hit is unconfirmed (independent added-damage sources; no KB statement of interaction).

---

# Build 4 — Bladefall Volley-Frequency Battery (mana → cast rate)

A rate-scaling architecture: maximum mana directly increases the skill's volley frequency, a different output axis than any added-damage path.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | Whispers of Infinity *(unique:1461, available)* | (60-40)% reduced maximum Mana; **Skills Cost Energy Shield instead of Mana or Life**; (10-15)% faster start of Energy Shield Recharge — committed as resource converter; **no damage mod applies (the seed's chaos mod is attack-tagged, Bladefall is a spell)** |
| Weapon | Dying Breath *(unique:220, staff, available — enabler/slot filler)* | **18% increased maximum Mana**; 18% increased Cast Speed; +20% Chance to Block Attack Damage (implicit); 18% increased Area of Effect of Aura Skills; 18% increased Area of Effect of Hex Skills; 18% increased effect of Non-Curse Auras from your Skills; 18% increased Damage; Nearby Enemies have 18% increased Effect of Curses on them; Nearby allies gain 18% increased Damage |
| Skill gem | gem:BladefallAltZ *(display name unresolved — id references base "Bladefall"; alternate-variant gem)* | **stat:bladefall_volley_frequency_+%_per_100_maximum_mana** (values unresolved); stat:bladefall_base_volley_frequency_ms; stat:bladefall_create_X_lingering_blades_per_volley; phys spell, area (remaining gem stats unresolved) |
| Passive | Deep Wisdom *(notable)* | flat maximum mana (wording unresolved) |
| Passive | Arcane Will *(passive:mana_and_mana_regen_notable2255, notable)* | grants stat:maximum_mana_+% (wording unresolved) |
| Passive | Hierophant mana nodes + Divine Guidance | stat:maximum_mana_+% (values unresolved) |

**Status: VALIDATED** (final=True: valid; Bladefall AltX: "no weapon restrictions").

**Why it works** — Volley frequency scales with maximum mana per the gem's stat; the amulet routes all skill costs to Energy Shield so the mana pool is never spent, and faster ES recharge sustains that loop; Dying Breath adds 18% max mana on the weapon. The seed participates via its resource-conversion edge only — its damage mods are attack-tagged and do not apply to this spell, and its reduced-mana mod actively taxes the frequency axis (documented tension; the build still validates and the ES-cost edge is a live contribution to the resource structure).

**Evidence**
- gem:BladefallAltZ → gem_grants_stat → stat:bladefall_volley_frequency_+%_per_100_maximum_mana (confirmed)
- unique:1461 → ES-cost edge (confirmed, resource structure)
- unique:220 → MaximumManaUniqueStaff5 → stat:maximum_mana_+% (confirmed)

---

# Build 5 — Prodigal Perfection Spell Battery (quadratic candidate, X²)

The only architecture where **both** paths from X to the same output are carried by committable components: added spell lightning per mana (gem) and a spell-damage multiplier per mana (passive).

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | Whispers of Infinity *(unique:1461, available)* | (60-40)% reduced maximum Mana; **Skills Cost Energy Shield instead of Mana or Life**; (10-15)% faster start of Energy Shield Recharge — committed as resource converter (spell costs paid from ES; mana pool intact); no damage contribution (attack-tagged mods do not apply to spells) |
| Weapon | Dying Breath *(unique:220, staff, available — X generator)* | **18% increased maximum Mana**; 18% increased Cast Speed; +20% Chance to Block Attack Damage (implicit); aura/hex AoE mods; Nearby allies gain 18% increased Damage (full list in Build 4) |
| Skill gem | gem:ManaInfusedStaff *(display name unresolved; staff skill gem)* | **stat:skill_has_added_lightning_damage_equal_to_%_of_maximum_mana** (values unresolved); stat:active_skill_always_reserves_unmodifiable_X%_of_mana; stat:mana_infused_staff_base_trigger_interval_ms; stat:active_skill_buff_block_chance_+%_final_to_grant; stat:active_skill_buff_mana_cost_+%_final_to_grant; tag: lightning (other stats unresolved) |
| Passive | Prodigal Perfection *(passive:mana_spell_damage_notable2609, notable)* | grants **stat:spell_damage_+%_per_100_maximum_mana_up_to_60%** (wording unresolved; stat id shows a 60% cap) and **stat:maximum_mana_+%** |
| Passive | Deep Wisdom *(notable)* | flat maximum mana (wording unresolved) |
| Passive | Hierophant mana nodes + Divine Guidance | stat:maximum_mana_+% (values unresolved) |

**Status: VALIDATED** (final=True: valid; ManaInfusedStaff: "no weapon restrictions").

**Why it works** — X enters spell damage through the gem's added-lightning-per-maximum-mana (A) and through Prodigal Perfection's increased-spell-damage-per-maximum-mana multiplier (B, capped at 60% by its stat id). Prodigal Perfection itself also generates X (max mana %). Seed role: converts all skill costs to ES and speeds ES recharge, leaving mana untouched by casting — a resource-side enabler; its reduced-mana mod taxes the axis.

**Scaling ladder: quadratic candidate (X → A, X → B, A × B → spell lightning damage)**
- A path: gem:ManaInfusedStaff → stat:skill_has_added_lightning_damage_equal_to_%_of_maximum_mana — **confirmed carrier**.
- B path: passive:mana_spell_damage_notable2609 → stat:spell_damage_+%_per_100_maximum_mana_up_to_60% — **confirmed carrier**.
- Interaction (increased multiplier applying to the added damage): **hypothesis** — the KB exposes both stats but no edge stating that increased spell damage multiplies the gem's added damage. Not claimed as confirmed.

**Unknowns** — the gem's own unmodifiable mana reservation competes with the amulet's tiny mana pool; how the reservation amount and the trigger interact with Whispers' 40–60% reduced mana is not stated anywhere in the KB.

---

## Architecture distinctness

| Build | Output of X | Mechanic class | Why not a variant of the others |
| --- | --- | --- | --- |
| 1 | attack hit damage (chaos) | added damage per mana, amulet-carried | seed is the sole damage core; no other carried chaos-per-mana source |
| 2 | attack hit damage (chaos+lightning) + damage mitigation | dual added-damage + mana-as-lightning-buffer | only carrier of "Lightning Damage taken from Mana before Life"; two-element battery |
| 3 | attack AoE (phys) | gem-carried added phys + projectile→cluster conversion | only cluster-count conversion in the set |
| 4 | cast/volley rate | frequency-per-mana | only rate-scaling output; spell, seed has no damage role |
| 5 | spell hit damage (lightning) | added-per-mana × multiplier-per-mana | only two-path (quadratic-candidate) structure |

Builds 1–3 share the "attack added-damage per mana" family but differ in damage type, carried source, and interaction structure; they are presented as the three distinct members of that family rather than three cosmetic copies. If stricter distinctness is wanted, 1–3 collapse into one architecture with three loadouts.

## Scaling axis / seed roles

- Seed role: Build 1/2/3 — **scaling axis holder + damage carrier** (chaos-per-mana mod is live and contributes directly); Build 4/5 — **mechanic converter / enabler** (ES-cost edge + ES recharge; reduced-mana mod documented as anti-axis).
- Axis re-anchoring: none — X stayed Maximum Mana throughout (seed neighbourhood evidenced mana-scaled outputs directly; no stronger axis found).
- Scaling classification: Build 5 = quadratic candidate (interaction hypothesis); Builds 1–4 = multi-use at best in KB evidence; the attack quadratic (added per mana × Synthesis-implicit multiplier per mana) is **blocked** because both Synthesis mods have zero unique carriers.

## Sweep log (fixed point)

1. **Sweep 1** — `neighbour unique:1461 depth 2`: 4 mods → 5 stats + tags. Added: whole seed mod surface.
2. **Sweep 2** — `resolve maximum_mana` (Stat, 65 rows, untruncated) + `carriers` on every mana→output stat: found MotC (lightning), PowerSiphonAltX, KineticBlastAltX, ManaInfusedStaff, BladefallAltZ, Prodigal Perfection; recorded 6 zero-carrier mods as true absence.
3. **Sweep 3** — X generators: `carriers stat:base_maximum_mana` (246 rows), `carriers stat:maximum_mana_+%` (153 rows, `excluded_alternate_ascendancies: 9` — 9 alt-asc carriers suppressed by default exclusion, not absence); weapon carriers for validation (Dying Breath, Piscator's Vigil).
4. **Fixed point** — final sweep re-probed all committed nodes' stats for further mana→output links: none (the only attack/spell damage multipliers per mana are the zero-carrier Synthesis mods). Loop stopped: no new nodes, edges, or reclassifications.

## Validator results

All five build states passed `phase7_build_validity.validate_build(final=True)` → **VALID** with respect to slot occupancy, weapon configuration, gem supportability, ascendancy composition (ascendancy: Hierophant committed via its mana nodes in each build; gem weapon checks: wand allowed for 2/3, no weapon restrictions for 4/5). Limitations as stated by the validator apply — this is not a full PoE build-validity claim.

## API GAPs and unresolved data

1. **Gem display names** — `resolve`/`carriers` return `name: null` for all gem nodes (gem:PowerSiphonAltX, gem:KineticBlastAltX, gem:ManaInfusedStaff, gem:BladefallAltZ). Sheets render ids with an explicit "id references base …" note; real names unresolved, never guessed.
2. **Passive modifier wording** — passive nodes expose stat ids but no readable modifier text; all passive rows above state the granted stat ids only.
3. **Synthesis implicit obtainability** — mods SynthesisImplicitAttackDamagePerMana1/2 and SynthesisImplicitSpellDamagePerMana1/2 exist with real text but no carrier of any type; the KB cannot say which items/slots can roll them → the attack/spell quadratic via Synthesis implicits is an API GAP, recorded as hypothesis-only.
4. **Gem stat values** — gem-granted stats carry no numeric ranges in the projections used; values marked "values unresolved".
5. Alt-ascendancy note: `maximum_mana_+%` carriers include 9 suppressed alternate-ascendancy rows (`meta.excluded_alternate_ascendancies: 9`); not treated as absence.
