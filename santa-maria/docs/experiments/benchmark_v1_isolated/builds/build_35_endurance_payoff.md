# Build 35 — Juggernaut Endurance Payoff (Disciple of the Unyielding)

Status: **VALIDATED** (passive layer; item layer limited — per-charge damage uniques have no KB mod associations)

Central interaction: hard *minimum* endurance charges (generation guarantee) into the per-charge damage payoff — the offensive side of the endurance axis, with generation as enabler.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Ascendancy | Juggernaut — Unyielding (passive:AscendancyJuggernaut9) | endurance-charge ascendancy anchor |
| Tree | **Disciple of the Unyielding** (passive:endurance_charges_notable2425) | **base_minimum_endurance_charges**; **damage_+%_per_endurance_charge**; endurance_charge_on_kill_% |
| Ring (influence, marked: slot filler) | ChargeBonusDamagePerEnduranceCharge family | per-charge damage mods |
| Gloves (eldritch, marked: slot filler) | DamagePerEnduranceChargeEldritchImplicit1..6 + Pinnacle presence | eldritch implicit family of the payoff stat |
| Cross-class fact | Juggernaut [Ascendant] (AscendancyAscendant31) | per-charge damage carrier — axis not Juggernaut-locked |

**Why it works** — Minimum charges make the per-charge damage stat permanently active (base_minimum_endurance_charges ← 15 mods + 3 passives), while the payoff stat itself is broadly generated: `damage_+%_per_endurance_charge` ← 35 mods + 3 passives (eldritch implicits, ChargeBonus family, influence tiers). On-kill generation (66-mod group at depth 2) sustains the stack. This is the offense half of the endurance axis; the defense half (per-charge resistances/block) lives in the same stat family.

**Evidence**
- stat:damage_+%_per_endurance_charge ← mgs=35, pgs=3 (Unyielding [Juggernaut], Juggernaut [Ascendant], Disciple of the Unyielding)
- stat:base_minimum_endurance_charges ← mgs=15, pgs=3
- stat:endurance_charge_on_kill_% ← 66-mod depth-2 group
- KB fact: all 3 probed per-charge-damage unique-named mods (Eldritch implicit presence variants) have **no unique association edges**

Validation: `validate_build{passives:[Disciple of the Unyielding, Unyielding]}` → **valid** (both Juggernaut-namespace; ascendancy composition + cap pass). Intermediate attempt with Disciple alone was **invalid** ("no Ascendancy in final build state") — recorded; resolved by adding Unyielding.
