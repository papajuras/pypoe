# Build 032 — Badge of the Brotherhood Charge-Conversion Architecture

**Status: VALIDATED** (passed all checks implemented by `phase7_build_validity` — slot occupancy, availability, ascendancy composition; NOT a full PoE build-validity claim)

Central interaction: the amulet ties the frenzy-charge pool to the power-charge pool, so every investment in maximum power charges simultaneously raises maximum frenzy charges — one axis feeding two charge economies with different consumers.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | **Badge of the Brotherhood** [available] | carries: **`MaximumFrenzyChargesEqualToMaximumPowerChargesUnique__1`** → `stat:maximum_frenzy_charges_is_equal_to_maximum_power_charges` · `ElusiveBuffEffectPerPowerChargeUnique__1` · `LoseFrenzyChargeOnTravelSkillUnique__1` · `LosePowerChargeOnElusiveGainUnique__1_` · `MutatedUniqueAmulet57MovementVelocityPerFrenzyCharge` · `TravelSkillCooldownRecoveryPerFrenzyChargeUnique__1` · `HybridDexInt` |
| Passive | Critical Strike Chance per Power Charge | grants: `stat:critical_strike_chance_+%_per_power_charge` |
| Passive | Critical Strike Multiplier per Power Charge | grants: `stat:critical_strike_multiplier_+_per_power_charge` |
| Passive | Power Charge Duration | grants: `stat:power_charge_duration_+%` |
| Passive | Critical Strike Chance, Power Charge Duration (AscendancyAssassin1, Assassin) | grants: `stat:critical_strike_chance_+%`, `stat:power_charge_duration_+%` |

**Ascendancy:** Assassin (small node: Critical Strike Chance, Power Charge Duration)

Note: the Research API exposes modifier/stat identifiers, not display text; the lists above are the exact ids returned by the API, unmodified.

## Why it works

The equality stat makes maximum power charges the single shared pool ceiling: power-charge investment (tree/jewels — not yet committed here) raises both charge types at once. Power charges then pay out through per-charge crit chance and crit multiplier (committed passives) and elusive effect; frenzy charges pay out through travel-skill cooldown recovery and movement speed. Charge duration passives and the Assassin node extend sustain for both pools.

## Scaling claim

**Multi-use (no quadratic claim).** X = maximum power charges → A: frenzy pool size → travel cadence + movement; B: crit chance/multiplier per power charge; C: elusive effect per power charge. Consumers are independent outputs; the KB shows no path where two X-derived effects multiply into one output.

## Evidence

- `mod:MaximumFrenzyChargesEqualToMaximumPowerChargesUnique__1` → `stat:maximum_frenzy_charges_is_equal_to_maximum_power_charges` (the conversion)
- `mod:TravelSkillCooldownRecoveryPerFrenzyChargeUnique__1`, `mod:MutatedUniqueAmulet57MovementVelocityPerFrenzyCharge` (frenzy consumers)
- `mod:ElusiveBuffEffectPerPowerChargeUnique__1`, `mod:LosePowerChargeOnElusiveGainUnique__1_` (power/elusive loop)

## Validation

All 5 additions passed `validate_addition`; final `validate_build` (final=True): **valid** — availability valid, single ascendancy class `Assassin`. Power-charge generators are the known-open slot (not committed: no specific generator node was validated in this run).
