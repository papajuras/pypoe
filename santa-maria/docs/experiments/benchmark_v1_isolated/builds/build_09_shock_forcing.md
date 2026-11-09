# Build 09 — Shaper of Storms Shock-Forcing Crit-Stacker

Status: **CANDIDATE** (passive layer VALIDATED; item layer not committed — no shock-related unique has a KB mod association)

Central interaction: force Shock onto all damage, then harvest a crit-vs-shocked consumer family.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Ascendancy | Elementalist — Shaper of Storms | **all_damage_can_shock**; **always_shock**; shock_minimum_damage_taken_increase_% |
| Body armour (rare, marked: slot filler) | rare with `always_shock` / `all_damage_can_shock` craft | one of 8 always_shock mod carriers / 12 all_damage_can_shock carriers in the KB |
| Gloves (rare, marked: slot filler) | rare with crit-vs-shocked mod | `critical_strike_chance_+%_vs_shocked_enemies` family (Crusader's influence, 3 carriers) |
| Ring (rare, marked: slot filler) | rare with damage-vs-shocked | `damage_vs_shocked_enemies_+%` — 1 KB carrier (`mod:IncreasedDamageToShockedTargetsUniqueRing29`); the unique itself is not KB-associated (unresolved) |
| Skills | Lightning Trap family | gems granting **crit-vs-shocked** (gem:LightningTrap, LightningSpireTrap + Alt/Royale variants) |
| Jewels/passives | tree crit-vs-shocked passive | 1 passive carrier of the consumer stat (not individually named in the KB result) |

**Why it works** — Shaper of Storms converts the whole damage profile into a Shocking one (all_damage_can_shock + always_shock), a multi-source axis: 13 carriers for all_damage_can_shock, 10 for always_shock, including cross-ascendancy passive **Fidelitas' Spike** (AscendancyReliquarian22 — evidences that the axis is not Elementalist-locked). The consumer side is independently multi-source: `critical_strike_chance_+%_vs_shocked_enemies` is granted by 5 gems, 9 mods, 1 passive — a genuine fan-out from forcing to payoff. KB fact: `always_crit_shocked_enemies` exists but its only mod has **no unique association** in the KB.

**Evidence**
- stat:always_shock ← 8 mods + 2 passives (Shaper of Storms [Elementalist]; Fidelitas' Spike [Reliquarian])
- stat:all_damage_can_shock ← 12 mods + 1 passive
- stat:critical_strike_chance_+%_vs_shocked_enemies ← 9 mods + 1 passive + 5 gems
- stat:damage_vs_shocked_enemies_+% ← 1 mod (unique ring mod, unresolved owner)
- resolve('shock', Mechanic) → 0 matches: **no shock Mechanic node exists in the KB** (gap; stat-level evidence used instead)

Validation: `validate_build{passives:['Shaper of Storms']}` → **valid** (slot/ascendancy constraints). Items not committed: no unique in the KB carries the axis/consumer mods with a confirmed unique association. Ascendancy alternative (unbuilt): Reliquarian via Fidelitas' Spike.
