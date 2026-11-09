# Build 12 — Hierophant Totem Compound (Count / Placement Speed / Duration)

Status: **CANDIDATE** — passive layer + gem group; final state UNKNOWN only because no weapon-class item was committed (weapon_check skipped), not because of a conflict.

Central interaction: three independent totem sub-axes (count, placement speed, duration) with distinct carrier populations — compound scaling with separate generation and consumption layers.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Ascendancy | Hierophant — Pursuit of Faith | **number_of_additional_totems_allowed**; summon_totem_cast_speed_+%; totem_duration_+% |
| Ascendancy | Hierophant — Mana Regeneration, Totem Placement Speed (passive:AscendancyHeirophant2) | summon_totem_cast_speed_+% |
| Body armour (rare, marked: slot filler) | rare with additional-totems mod | `AdditionalTotemsUniqueBodyInt7` is a body-armour mod family member; **KB fact: no unique association edge exists for it** |
| Gem | Searing Bond (gem:SearingBond) | grants summon_totem_cast_speed_+% (15 gem carriers of the axis) |
| Skills | Siege Ballista / Ancestral Warchief | also in the 9-gem carrier set of the count axis |

**Why it works** — Pursuit of Faith is one of only 3 passive carriers of the totem-count axis and simultaneously carries the placement-speed axis. The count axis (`number_of_additional_totems_allowed`: 14 mods + 3 passives + 9 gems) multiplies every damage instance; the speed axis (`summon_totem_cast_speed_+%`: 55 mods + 11 passives + 15 gems) reduces time-to-first-damage and re-placement uptime — the two axes multiply rather than overlap. Ascendant's Hierophant node (AscendancyAscendant44) carries both axes, evidencing cross-class availability.

**Evidence**
- stat:number_of_additional_totems_allowed ← mgs=14, pgs=3, ggs=9
- stat:summon_totem_cast_speed_+% ← mgs=55, pgs=11, ggs=15
- carriers(mod:AdditionalTotemsUniqueBodyInt7, UMA) → 0 — unique-anchor absent in KB

Validation: `validate_build{passives:[Pursuit of Faith, passive:AscendancyHeirophant2], gems:[SearingBond]}` → **unknown** (weapon context not determined; no weapon-class unique exists in this session's evidence to commit). Passives-only sub-state is valid.
