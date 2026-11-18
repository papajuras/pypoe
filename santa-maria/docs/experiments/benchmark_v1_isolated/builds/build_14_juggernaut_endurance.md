# Build 14 — Juggernaut Endurance Generation (Unflinching Charge Engine)

Status: **VALIDATED** (items + passives; validator constraints: slot occupancy, ascendancy composition, availability)

Central interaction: multi-source endurance-charge *generation* with hard maximum charges — an offense/defense dual-use axis (per-charge damage and per-charge block/resistances are the consumer side; the damage payoff was evidenced in this session only as the existence of the per-charge stat family, not its carriers).

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Ascendancy | Juggernaut — Unflinching | **chance_to_gain_endurance_charge_when_hit_%**; gain_endurance_charge_per_second_if_have_been_hit_recently; gain_maximum_endurance_charges_on_endurance_charge_gained_%_chance; **max_endurance_charges** |
| Tree | Endurance (passive:maximum_endurance_charges132) | max_endurance_charges |
| Ring | **Kaom's Sign** (unique:4, available) | carries MaximumEnduranceChargeUniqueRing2 (max_endurance_charges) |
| Body armour | **Daresso's Defiance** (unique:188, available) | carries MaximumEnduranceChargeUniqueBodyStrDex3 (max_endurance_charges) |
| Body armour (alt) | Death's Oath (unique:172, available) | carries MaximumEnduranceChargeUniqueBodyStr3 — alternative anchor |

**Why it works** — Unflinching stacks three independent generation mechanics (on-hit chance, per-second while hit recently, chance to gain maximum on gaining). The max-charge axis itself is broadly generated: `max_endurance_charges` ← 33 mods + 6 passives (Warlord's/Elevated Warlord's influence, 'of Shaping', unique body mods, Ancestral Endurance [Juggernaut Phrecia-alt]). Because charges are a capped resource, every +1 maximum is a multiplier on all per-charge consumers; this session evidences the consumer *family* (per-charge stats exist: block per charge, crit per charge, …) via `resolve('per_endurance_charge')` (50 stats) — the damage payoff's carriers were probed in the sibling session 35 and are intentionally not imported here.

**Evidence**
- stat:max_endurance_charges ← mgs=33, pgs=6
- stat:chance_to_gain_endurance_charge_when_hit_% ← mgs=4, pgs=3 (Unflinching, Inexorable, Indomitable Warrior)
- stat:gain_endurance_charge_per_second_if_have_been_hit_recently ← mgs=6, pgs=2
- unique:4 / unique:188 / unique:172 ← UMA links to max-charge mods (all **available**; Kaom's Way unique:889 is **unavailable** — excluded)

Validation: `validate_build{items:[Kaom's Sign, Daresso's Defiance], passives:[Unflinching, Endurance]}` → **valid**. Per-charge damage/blocked payoff layer: within-session status = consumer family exists, carrier depth not established here.
