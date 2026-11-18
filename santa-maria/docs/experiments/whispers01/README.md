# Whispers of Infinity — Build Discovery Run (whispers01)

- **Date:** 2026-09-17
- **Seed:** `unique:1461` — Whispers of Infinity [available] (Amulet)
- **Method:** public Research API only (`phase8_research.resolve/carriers`, `phase6_api.get_neighbour`, phase7 `validate_addition`/`validate_build`); skills: discovery-api-usage, scaling-discovery, build-output. No DB/internals access.
- **Goal:** genuinely distinct builds anchored on the amulet's own mechanics — no artificial duplication.

## The amulet (API evidence)

| Carrier mod | Stat(s) granted |
|---|---|
| `AttacksGainMinMaxAddedChaosDamageBasedOnManaUnique__1` | `max/min_attack_added_chaos_damage_per_100_mana` — **attacks gain added chaos per 100 mana** |
| `PercentReducedMaximumManaUnique_1` | `maximum_mana_+%` (group `MaximumManaIncreasePercent`; API exposes no sign) |
| `SkillsCostEnergyShieldInsteadOfManaLifeUnique__1` | `base_skills_cost_es_instead_of_mana_life` — **skills pay from energy shield** |
| `ReducedEnergyShieldDelayImplicit1_` | `energy_shield_delay_-%` |

Consequence that shapes every build: mana is a **pure stat pool** (never spent) and energy shield is the **actual resource**. Any "mana spent" engine is dead with this item (negative finding below).

## Distinct builds (3, one file each, all validated)

1. **builds/build_01_strength_stacker.md** — *Iron Whisper strength-stacker.* X = strength → mana (Shaper's Touch `X_mana_per_4_strength` + Mental Conditioning) → WoI attack chaos; same strength → melee physical % via The Iron Fortress `strength_damage_bonus_grants_melee_physical_damage_+3%_per_10_strength_instead`. Two damage paths from one axis. Berserker (Phrecia). VALID.
2. **builds/build_02_abyssal_jewel_stack.md** — *Lightless abyssal stack.* X = abyssal jewels → %mana (Shroud of the Lightless + Lightless notable — two redundant sources) → WoI chaos; per-jewel ele pen into the same attacks; per-jewel life. Jewel-count architecture. Trickster (Phrecia). VALID (jewels themselves UNKNOWN — outside validator scope).
3. **builds/build_03_reserved_mana_armour.md** — *Memory Vault reserved-mana tank.* X = reserved mana → armour (Memory Vault `gain_X%_armour_per_100_mana_reserved`); total mana → WoI chaos; ES-cost conversion makes reservation cost-free to gameplay. Champion. VALID (aura gems UNKNOWN — validator weapon-context limit).

## Why these three are genuinely distinct

Different scaling axis, different generator family, different second path, different ascendancy:

| Build | Axis | Mana generator | Second path | Ascendancy |
|---|---|---|---|---|
| 01 | strength | gloves + asc notable (STR→mana) | STR→melee phys conversion | Berserker |
| 02 | abyssal jewel count | armour + asc notable (%mana/jewel) | ele pen/jewel on same attacks | Trickster |
| 03 | reserved mana | n/a (reservation is the axis) | reserved→armour defence layer | Champion |

## Alternates recorded, NOT built (anti-duplication)

- **Dexterity→mana:** `passive:AscendancyCustomDeadeye14` ("an infinite pursuit") grants `X_mana_per_dexterity` — same skeleton as build 01 with a different attribute; listed inside build 01's sheet instead of a separate file.
- **Mental-Conditioning-only variant** of build 01 without Shaper's Touch: same axis and output, weaker generator; not a distinct architecture.

## Negative findings / dead ends (evidence, not guesses)

- **Mana-spent engines are unplayable with WoI** (mana is never spent): 17 `_mana_spent` stats found (`damage_+%_per_200_mana_spent_recently`, `gain_x_rage_per_200_mana_spent`, onslaught/cast-on-mana-spent, arcane-surge-per-mana-spent…) — all incompatible with `base_skills_cost_es_instead_of_mana_life`. Kills the entire apparent "mana-spender" family.
- **No energy-shield-spent vocabulary exists** in the KB: `resolve('energy_shield_spent')` and `resolve('per_100_energy_shield')` both complete-empty — the ES-pays-costs half of the item has no KB-modeled consumers.
- **Orphan stats (zero carriers — checked):** `maximum_mana_+%_per_blue_socket_on_staff` (0 carriers); spell-block→mana mod `IncreasedManaPerSpellBlockChanceUnique__1` (0 unique carriers) — no block-tank mana build possible from KB evidence.
- **Maven/Uber STR mods not item-reachable:** `GainAccuracyEqualToStrengthInfluenceMaven` (crit/STR) and `MeleePhysicalDamagePerStrengthWhileFortifiedUber1` have 0 unique carriers — cannot be validated components.
- **Only 3 stats scale "per 100 mana"** in the whole KB: WoI's own two + `gain_X%_armour_per_100_mana_reserved` (build 03) — the mana-consumer vocabulary is tiny; WoI's chaos-per-mana is nearly unique.

## API usage (this run)

neighbour 14 · carriers 15 · resolve 8 = **37 discovery calls**; validator calls: 12 additions + 3 finals (all valid). Cumulative session counter in `/tmp/opencode/api_usage.json`.

## Self-check

- All claims cite API-returned carriers/stats; empty results checked against `meta.counts` and recorded as facts.
- Sign of the amulet's mana mod is NOT exposed (mod id says "Reduced", group says "Increase") — rendered unresolved rather than guessed.
- Builds 02/03 have explicitly marked UNKNOWN slots (jewels, aura gems) — validator scope only, never assumed valid.
- Validation status is validator-scope only (slots/availability/ascendancy/gem-supportability), stated on every sheet.
