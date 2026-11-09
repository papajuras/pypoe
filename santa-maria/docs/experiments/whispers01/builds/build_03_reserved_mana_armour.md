# Build 03 — Memory Vault Reserved-Mana Armour Tank

**Status: VALIDATED** (passed `phase7_build_validity` checks — slots, availability, ascendancy composition; NOT a full PoE build-validity claim)

Central interaction: reserving mana for auras and curses generates armour equal to the reserved amount (Memory Vault), while the unreserved remainder of a large mana pool still feeds Whispers of Infinity's per-100-mana attack chaos — defence and offence both scale on the same mana pool, split by reservation.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | **Whispers of Infinity** [available] | carries: **`AttacksGainMinMaxAddedChaosDamageBasedOnManaUnique__1`** → `stat:max_attack_added_chaos_damage_per_100_mana` + `stat:min_attack_added_chaos_damage_per_100_mana` · `PercentReducedMaximumManaUnique_1` → `stat:maximum_mana_+%` (group: `MaximumManaIncreasePercent`; sign not exposed by API) · `SkillsCostEnergyShieldInsteadOfManaLifeUnique__1` → `stat:base_skills_cost_es_instead_of_mana_life` · `ReducedEnergyShieldDelayImplicit1_` → `stat:energy_shield_delay_-%` |
| Helmet | Memory Vault [available] | carries: **`GainArmourEqualToManaReservedUnique__1`** + `DivergentGainArmourEqualToManaReservedUnique__1` → `stat:gain_X%_armour_per_100_mana_reserved` · `ManaRegenerationUnique__6` · `LocalIncreasedEnergyShieldUnique__15` |
| Passive | Curse Mana Reservation Efficiency | grants: curse mana reservation efficiency (`curse_reservation_efficiency2863`) — lets more curse auras fit into the reserved pool |
| Passive | Armour and Evasion, Aura Effect (AscendancyChampion2, Champion small) | armour/evasion + aura effect small node |

**Ascendancy:** Champion

Aura gems (the reservation generators themselves) are not committed as gem groups here: the KB models reservation on the passive/gem layer but the validator cannot verify aura gem groups without a weapon context — marked UNKNOWN rather than assumed.

Note: the Research API exposes modifier/stat identifiers, not display text; lists above are exact API ids, unmodified.

## Why it works

Every point of mana reserved by auras/curses becomes armour via Memory Vault, so the reservation system — usually a cost — is the defence budget. Meanwhile WoI decouples skill costs from mana entirely (energy shield pays), so reserving mana never interferes with casting/attacking, and the total mana pool (reservations included in the pool's size) still sets the WoI added-chaos value. Curse reservation efficiency passives let the build reserve more total mana, scaling both terms.

## Scaling claim

**Multi-use (offence + defence from one pool), not quadratic.** X = reserved mana → armour (Memory Vault); Y = total maximum mana → attack added chaos (WoI). Reservation increases X and total mana increases Y; the KB models the two terms separately and no mechanic converts armour back into damage, so no X² claim is made.

## Evidence

- `carriers(stat:gain_X%_armour_per_100_mana_reserved)` → exactly 1 carrier: `mod:DivergentGainArmourEqualToManaReservedUnique__1`... via Memory Vault (`unique:713` carries both the base and Divergent versions via uma)
- `passive:curse_reservation_efficiency2863` (curse mana reservation efficiency family, 4 nodes found)
- `unique:1461` → `stat:base_skills_cost_es_instead_of_mana_life` (mana stays free to reserve)

## Validation

4/4 additions valid; final `validate_build` (final=True): **valid** — availability all available, class_mix `['Champion']`.

## Anti-synergy note (recorded negative finding)

Mana-spent engines (`stat:damage_+%_per_200_mana_spent_recently`, `stat:gain_x_rage_per_200_mana_spent`, onslaught-on-mana-spent, cast-on-mana-spent) are **dead** in any Whispers of Infinity build: `base_skills_cost_es_instead_of_mana_life` means mana is never spent. This rules out an entire apparent build family — checked via `resolve('_mana_spent','Stat')` (17 stats), none usable here.
