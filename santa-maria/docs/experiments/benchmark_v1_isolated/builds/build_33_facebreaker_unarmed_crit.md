# Build 33 — Facebreaker Unarmed Crit-Multiplier Stack

Status: **CANDIDATE** — item + passive + gem validated at component level; final state UNKNOWN (unarmed has no weapon-class slot in the validator, so gem weapon_check is skipped, not failed).

Central interaction: Facebreaker converts unarmed attacks into a more-multiplier carrier while a broad, class-independent critical-multiplier axis (152 KB carriers) feeds the crit side.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Gloves | **Facebreaker** (unique:924, available) | **unique_facebreaker_unarmed_melee_physical_damage_+%_final** (the unarmed converter); **base_critical_strike_multiplier_+**; extra_gore |
| Ascendancy | Assassin — Critical Strike Chance and Multiplier (passive:AscendancyAssassin5) | base_critical_strike_multiplier_+ |
| Skill | Ancestral Warchief (gem:AncestralWarchief) | unarmed melee totem slam |
| Jewels (rare, marked: slot filler) | crit-multi jewel mods | part of the 128-mod carrier population |
| Cross-class fact | Trickster crit-multiplier-and-stealth notables are Phrecia-alt (AscendancyCustomTrickster*) — base-namespace choice here is Assassin | |

**Why it works** — The unarmed identity is supplied entirely by Facebreaker's final multiplier; everything else can be the game's broadest generic axis. `base_critical_strike_multiplier_+` is granted by 128 mods + 18 passives + 6 gems (Icicle Mine family, ModSupport crit-multi supports, Assassin/Trickster notables) — the build's scaling depth comes from axis breadth, not from item scarcity. Facebreaker itself also carries base crit multi, joining the same axis.

**Evidence**
- unique:924 ← UMA: CriticalMultiplierUniqueGlovesDexInt2 (**base_critical_strike_multiplier_+**), FacebreakerUnarmedMoreDamage (**unarmed more-multi**), ExtraGore
- stat:base_critical_strike_multiplier_+ ← ggs=6, mgs=128, pgs=18
- stat:unique_facebreaker_unarmed_melee_physical_damage_+%_final ← 1 mod (this item)

Validation: `validate_build{items:[Facebreaker], gems:[AncestralWarchief], passives:[AscendancyAssassin5]}` → **unknown** — weapon context cannot be determined (Facebreaker is Gloves-class; the validator has no unarmed weapon representation; weapon_check skipped). Item, passive and availability checks pass.
