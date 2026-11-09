# Build 32 — Deadeye Charge-Role Conversion (Badge of the Brotherhood)

Status: **VALIDATED** (item + 2 passives)

Central interaction: Badge converts the power-charge role into the frenzy role, which unifies two charge economies and exposes movement/travel consumers that frenzy charges pay for.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | **Badge of the Brotherhood** (unique:1065, available) | **maximum_frenzy_charges_is_equal_to_maximum_power_charges**; lose_a_power_charge_when_you_gain_elusive_%_chance; lose_a_frenzy_charge_on_travel_skill_use_%_chance; travel_skills_cooldown_speed_+%_per_frenzy_charge; movement_velocity_+%_per_frenzy_charge (MutatedUniqueAmulet57); elusive_effect_on_self_+%_per_power_charge; additional_dexterity_and_intelligence |
| Tree | Movement Speed per Frenzy Charge (passive:frenzy_charges2418) | movement consumer |
| Ascendancy | Deadeye — Avidity (passive:AscendancyDeadeye10) | max_frenzy_charges |
| Boots (rare, marked: slot filler) | travel-skill cooldown consumer mods | per-frenzy travel-cooldown family |
| Jewels (not committed) | — | jewels/flasks have no slot model in the validator (limitation) |

**Why it works** — The conversion stat makes maximum frenzy = maximum power, so a single "raise your cap" investment now serves two charge types at once (compound scaling). The per-frenzy consumers on the item itself — movement velocity and *travel-skill cooldown recovery* — turn a charge engine into a mobility engine: every travel skill spends a frenzy charge and comes back faster per charge invested. The elusive-per-power stat couples the defensive layer into the same economy.

**Evidence**
- unique:1065 ← 7 KB-linked mods (all listed above; MutatedUniqueAmulet57 flagged membership)
- stat:maximum_frenzy_charges_is_equal_to_maximum_power_charges ← 1 mod (this item)
- stat:movement_velocity_+%_per_frenzy_charge ← MutatedUniqueAmulet57
- stat:travel_skills_cooldown_speed_+%_per_frenzy_charge ← TravelSkillCooldownRecoveryPerFrenzyChargeUnique__1
- stat:lose_a_frenzy_charge_on_travel_skill_use_%_chance ← stat_mechanic_relation → mechanic:frenzy_charge
- passive:AscendancyDeadeye10 (Avidity) ← max_frenzy_charges carrier

Validation: `validate_build{items:[Badge of the Brotherhood], passives:[Movement Speed per Frenzy Charge, Avidity]}` → **valid** (slot occupancy, ascendancy composition, availability all pass).
