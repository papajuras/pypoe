# Build 035 — Endurance Charge Stacker (Disciple of the Unyielding)

**Status: VALIDATED** (passed all checks implemented by `phase7_build_validity` — ascendancy composition; no items committed, so availability trivially valid; NOT a full PoE build-validity claim)

Central interaction: the seed notable both generates endurance charges (minimum base + on-kill chance) and consumes them for damage per charge, while sibling tree notables convert the same charge pool into armour, area of effect, and life regeneration — one pool, five consumers.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Passive | **Disciple of the Unyielding** (notable, seed) | grants: `stat:base_minimum_endurance_charges` · **`stat:damage_+%_per_endurance_charge`** · `stat:endurance_charge_on_kill_%` |
| Passive | Armour per Endurance Charge | grants: armour per endurance charge (notable `endurance_charges2423`) |
| Passive | Area of Effect per Endurance Charge | grants: AoE per endurance charge (notable `endurance_charges2424`) |
| Passive | Life Regeneration per Endurance Charge | grants: life regeneration per endurance charge (`life_regeneration_per_endurance_charge141`) |
| Passive | Armour, Endurance Charge Duration (AscendancyJuggernaut1, Juggernaut) | grants: `stat:endurance_charge_duration_+%`, `stat:physical_damage_reduction_rating_+%` |

**Ascendancy:** Juggernaut (small node: Armour, Endurance Charge Duration)

Note: the Research API exposes stat identifiers, not display text; the list above is the exact id set returned by the API, unmodified. The three sibling notables are identified by their API display names.

## Why it works

The seed notable is a self-contained generator+consumer block: minimum charges guarantee a floor, on-kill chance refills in combat, and damage scales per charge held. The sibling per-charge notables make the same pool pay into defence and area simultaneously, and the Juggernaut node extends duration and armour — every additional charge raises all five consumers at once.

## Scaling claim

**Multi-use (no quadratic claim).** X = endurance charges held → damage%, armour, AoE, life regen, physical damage reduction (via the ascendancy node's charge duration support). Four-plus independent linear consumers of one pool; the KB shows no interacting pair of X-derived effects combining into a single output. A wider family of per-charge stats exists (`stat:bleed_damage_+%_per_endurance_charge`, `stat:fire_damage_+%_per_endurance_charge`, `stat:melee_damage_+%_per_endurance_charge` — resolved but not committed).

## Evidence

- `passive:endurance_charges_notable2425` → `stat:damage_+%_per_endurance_charge`, `stat:base_minimum_endurance_charges`, `stat:endurance_charge_on_kill_%`
- resolve('endurance charge', Passive) → 10-node family incl. `endurance_charges2423` (armour), `endurance_charges2424` (AoE), `life_regeneration_per_endurance_charge141`
- resolve('damage_+%_per_endurance_charge', Stat) → 4 per-charge damage stat variants

## Validation

All 5 additions passed `validate_addition`; final `validate_build` (final=True): **valid** — single ascendancy class `Juggernaut`. Passive-only concept: no weapon/gear committed; a full build would need a melee skill set (slot intentionally left open, marked here rather than filled speculatively).
