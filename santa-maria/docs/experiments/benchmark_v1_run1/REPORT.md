# PoE Discovery Benchmark v1 — Run Report

- **Date:** 2026-09-17
- **Corpus:** `santa-maria/docs/experiments/seed_corpus_v1/corpus.json` (frozen; sha256 prefix `d62839a9045e28c8`, 81 entries: 3 mandatory + 20 ascendancy coverage + 58 random draws)
- **Governing skills:** discovery-api-usage, scaling-discovery, build-output
- **Interface:** public Research API only — `phase8_research.resolve/carriers`, `phase6_api.get_neighbour`, phase7 validators via `validate_addition`/`validate_build`. No DB, raw-record, cache, or internal-adjacency access at any point.

## Method and fixed budget

Per-entry budget (fixed before the run): **≤3 discovery API calls per entry**, extendable to **5** only for a concrete lead, each follow-up justified in the record. Build-construction validator calls tracked separately. Discovery protocol per seed: reverse projection (`carriers`) and/or forward adjacency (`get_neighbour` depth 1); for uniques, forward `nb(unique→mods)` then targeted `nb(mod→stats)`; for passives, `nb(out)` granted stats + `carriers` (reverse); for stats/mods, `carriers`; for mechanics/tags/item classes, both directions as appropriate. Every empty result was checked against `meta.counts` and recorded as a fact of absence, never as an error.

## Per-seed results

Verdict vocabulary: BUILD (validated build file written) · MULTI-USE · ENABLER · HUB (vocabulary/container node) · ISOLATED (single axis, no second path) · ORPHAN-STAT (stat with zero grantors) · KB-EMPTY (node exists but KB models no content) · DROPPED (lead killed by evidence) · NONE.

| # | Seed | Verdict | Primary finding |
|---|------|---------|-----------------|
| 0 | unique:1198 Replica Alberon's Warpath | ISOLATED | STR→added-chaos-to-attacks per 50 STR; family = 2 mods, same stat; `carriers(unique)` empty by design |
| 1 | unique:1461 Whispers of Infinity | MULTI-USE | mana→attack chaos dmg per 100 mana; ES-instead-of-mana cost conversion; no interacting pair |
| 2 | item_class:Boots | HUB | 60+ uniques in class (truncated); no stat-level class view |
| 3 | Ascendant5 Path of the Shadow | ISOLATED | 1 stat (`display_can_take_character_start_point`); 0 carriers |
| 4 | Assassin10 Toxic Delivery | MULTI-USE | poison-duration-per-poison-recently + poison-from-crit + life/kill; family = 2 Animal charms + notable |
| 5 | Berserker8 Rite of Ruin | ISOLATED | rage effect % + rage loss rate; single mechanic |
| 6 | Champion14 Master of Metal | MULTI-USE | impale reflected hits + armour-if-impaled-recently |
| 7 | Chieftain11 Tukohama | ENABLER | body armour supported by Ancestral Call / Fist of War |
| 8 | Deadeye14 Gathering Winds | ISOLATED | tailwind per gale force; 1 stat |
| 9 | Elementalist19 Shaper of Storms | ISOLATED | always shock + all-damage-can-shock + shock floor |
| 10 | Gladiator7 Gratuitous Violence | ISOLATED | bleeding enemies explode %life as phys |
| 11 | Guardian16 Unwavering Crusade | KB-EMPTY | 0 out-edges, 0 carriers — KB models nothing for this notable (fact) |
| 12 | Hierophant9 Pursuit of Faith | MULTI-USE | +totems, totem cast speed, totem duration |
| 13 | Inquisitor14 Instruments of Zeal | ISOLATED | fanaticism charge loop, self-contained |
| 14 | Juggernaut11 Unflinching | ENABLER | endurance-charge generation block (on hit/sustained/max-gain/max) |
| 15 | Necromancer12 Commander of Darkness | MULTI-USE | aura-linked attack/cast speed, damage, resists |
| 16 | Occultist8 Unholy Authority | ENABLER | +curses, ignore hexproof |
| 17 | Pathfinder14 Master Toxicist | ENABLER | poison +100% final chance + spread during flask effect |
| 18 | Reliquarian9 Caster Weapon Display | KB-EMPTY | 0 out-edges, 0 carriers (fact) |
| 19 | Saboteur4 Born in the Shadows | ISOLATED | blind-on-hit loop, self-contained |
| 20 | Slayer8 Overwhelm | ISOLATED | crit multi per nearby enemy (cap 100); sole carrier = the notable |
| 21 | Trickster2 Swift Killer | ENABLER | max frenzy + charge duration |
| 22 | Raider8 Lesson of the Seasons | MULTI-USE | bark stacks: spell dmg per bark + spell dmg taken per bark (id-namespace mismatch known) |
| 23 | unique:734 Shroud of the Lightless | MULTI-USE | per-abyssal-jewel: ele pen + life + mana |
| 24 | unique:1238 Replica Cheap Construction | KB-EMPTY | jewel with 0 modelled mods (fact) |
| 25 | unique:165 Perandus Signet | ISOLATED | INT per equipped unique; single stat |
| 26 | unique:1281 Legacy of Fury | ISOLATED | scorch apply/amplify/degen-explode, single item |
| 27 | unique:766 Farrul's Chase | ENABLER | Cat's Stealth trigger + movement (cat family) |
| 28 | unique:1179 Replica Quill Rain | KB-EMPTY | bow with 0 modelled mods (fact) |
| 29 | unique:679 Dendrobe | MULTI-USE | poison dmg >300 dex + poison duration >150 int (threshold converters) |
| 30 | unique:764 Farrul's Bite | **BUILD** | crit→blind loop; quadratic hypothesis; `build_030_farruls_crit_blind_loop.md` |
| 31 | unique:1443 Circle of Ambition | ENABLER | herald reservation + herald bonus |
| 32 | unique:1065 Badge of the Brotherhood | **BUILD** | max-frenzy=max-power conversion; `build_032_badge_charge_conversion.md` |
| 33 | unique:924 Facebreaker | ISOLATED | unarmed `_%_final` multiplier; single path in-session |
| 34 | unique:838 Solstice Vigil | ISOLATED | Shaper's Presence + all damage + mana regen |
| 35 | endurance_charges_notable2425 | **BUILD** | charge pool, 5 consumers; `build_035_endurance_charge_stacker.md` |
| 36 | atlas_path_17 | ISOLATED | map item drop chance; non-combat |
| 37 | totem_attack_damage2676 | ISOLATED | totem attack speed; 1 stat |
| 38 | dexterity848 | ISOLATED | base_dexterity; 1 stat |
| 39 | UniqueItemsNode31_ Lord's Descent | ISOLATED | fruit unique chance; non-combat |
| 40 | atlas_memory_notable_4 | ISOLATED | zana influence lucky; non-combat |
| 41 | reaver605 Executioner | ISOLATED | dmg vs low life + AoE on recent kill |
| 42 | totem_ranged_damage2668 | ISOLATED | totem dmg + placement speed |
| 43 | gem:SplittingSteel | **BUILD** | projectile-mods→splits converter; `build_043_splitting_steel_fury_valve.md` |
| 44 | gem:SupportGreaterDevour | ENABLER | corpse-consume → soul/life/mana |
| 45 | gem:SupportCastLinkedCursesOnCurse (WIP) | ISOLATED | single stat `cast_linked_curses_on_curse` |
| 46 | gem:SummonHolyRelicAltX | DROPPED | relic-count scaling killed: `AdditionalHolyRelicUnique__1` has 0 unique carriers (orphan fact) |
| 47 | gem:EnchantmentOfReflectionWhenHit4 | ENABLER | cast-when-hit minion summon |
| 48 | gem:EssenceDrainAltX | ISOLATED | spell-dmg-modifiers-apply-to-DoT converter; single gem |
| 49 | gem:PenanceMark | ENABLER | no-damage mark → phantasms when hit |
| 50 | gem:SummonSkeletonsChannelled | ISOLATED | channelled skeleton count + added dmg final |
| 51 | stat:brequel…rarer_rewards_chance_+% | ISOLATED | carrier = Artificial Selection notable; non-combat |
| 52 | stat:local_unique_jewel…witch_start | ISOLATED | 1 carrier (starter jewel mod) |
| 53 | stat:cannot_die | ISOLATED | 7 carriers, monster-side auras + `CannotDieUnique__1` (0 unique carriers — orphan fact); not player-reachable |
| 54 | stat:crit…at_least_200_int | ISOLATED | sole carrier `The Tactician` [UNAVAILABLE] — dead end |
| 55 | stat:map_watchstone_monsters_life_+%_final | ISOLATED | 1 carrier; map balance, not player scaling |
| 56 | stat:banner_adrenaline_duration_+% | ORPHAN-STAT | 0 carriers (fact) |
| 57 | stat:virtual_minion_attack_speed_+% | ORPHAN-STAT | 0 carriers (fact) |
| 58 | stat:crit…per_lightning_adaptation | ORPHAN-STAT | 0 carriers (fact) |
| 59 | mod:MapMonsterCriticalStrikesAndDamageDelve2 | ISOLATED | delve/map balance mod |
| 60 | mod:WeaponTreeSupportIronGripHardMode | ENABLER | Iron Grip support on 1H+shield weapon tree |
| 61 | mod:RecoverMaximumEnergyShieldOnKill… | ISOLATED | single flask stat |
| 62 | mod:ColdResistUnique__43 | ISOLATED | single stat |
| 63 | mod:TemporalChainsReservationCostUnique__2 | ISOLATED | TC no reservation; unique-side |
| 64 | mod:MonsterMinionInstability | ENABLER | keystone stat family: 6 mods (hellscape/recombinator/sanctum/weapon-tree/unique-side) + passive keystone |
| 65 | mechanic:minion | HUB | 60+ related stats (truncated) |
| 66 | mechanic:suppression | HUB | ~29 related stats |
| 67 | mechanic:attribute | HUB | 107+ per-attribute scaling stats (largest) |
| 68 | mechanic:frenzy_charge | HUB | 104+ stats, generators + per-charge consumers |
| 69 | mechanic:chill | HUB | 103+ related stats |
| 70 | tag:lightning | HUB | 150+ gems (truncated) |
| 71 | tag:curse | HUB | 150+ gems (truncated) |
| 72 | tag:quiver_eyrie | ENABLER | 18-mod Eyrie quiver influence pool |
| 73 | tag:blight_death_physical | ISOLATED | exactly 1 carrier mod (monster death) |
| 74 | item_class:CursedDucat | NONE | 0 members (fact) |
| 75 | item_class:Tincture | HUB | 5 unique tinctures |
| 76 | item_class:HeistEquipmentWeapon | NONE | 0 members (fact) |
| 77 | item_class:IncubatorStackable | NONE | 0 members (fact) |
| 78 | item_class:Support Skill Gem | NONE | 0 members in class container (fact; support gems exist as gem nodes) |
| 79 | item_class:Map | HUB | 33+ unique maps |
| 80 | item_class:BrequelFruit | NONE | 0 members (fact); cross-refs #51 via its stat |

## Concrete builds (4, all validated, one file each)

1. **build_030_farruls_crit_blind_loop.md** — Farrul's Bite crit→blind loop; quadratic hypothesis (unconfirmed blind-uptime link); seed anchor kept.
2. **build_032_badge_charge_conversion.md** — Badge of the Brotherhood power/frenzy pool conversion; multi-use; open slot: power-charge generators (marked).
3. **build_035_endurance_charge_stacker.md** — endurance-charge pool, five consumers; multi-use; passive-only, gear slot marked open.
4. **build_043_splitting_steel_fury_valve.md** — projectile-mod→split conversion shared by 6 carriers (4 gems + 1 unique mod + Fury Valve); The Princess marked **slot filler**.

## Discovery summary

- **Strongest architecture family: charge pools.** Endurance (#35), power/frenzy conversion (#32), and the frenzy-charge mechanic vocabulary (#68) all show the same shape — a countable X with on-node or on-family generators and many per-charge consumers. Two of four builds came from it.
- **Compound finding: the cat-aspect item family** (#30) is the only place where two full X-paths into one output (crit chance → crit damage; crit chance → blind → vs-blinded damage) are all KB-evidenced — recorded as a quadratic *hypothesis*, not confirmed.
- **Multi-use without interaction** is the dominant positive pattern (8 seeds): one stat paying into 2–3 independent outputs. Per the scaling skill, none were promoted to quadratic.
- **Converter nodes** (#43 splits, #48 spell-dmg→DoT, #49 no-damage→phantasms) are single-mechanic translations; #43 became a build because the conversion stat is demonstrably multi-source.
- **Legitimate dead ends:** 33 isolated single-path seeds, 3 orphan stats, 4 KB-empty nodes, 5 empty item-class containers, and #46 where a build lead was killed by a checkable absence (the +1-relic modifier has no carrier).
- **Cross-entry observation (post-sessions):** #67 attribute HUB enumerates 107+ per-attribute converters that retroactively contextualize #0/#25-style attribute axes; #68's generators pair naturally with #32's conversion. These links were not fed back into individual sessions.

## Build-construction summary

- Candidates attempted: **5** (030, 032, 035, 043, 046).
- Validated: **4**. Rejected/dropped: **1** (#46 — orphan mod fact).
- UNKNOWN-blocked: **0 final** (one intermediate UNKNOWN in #43 — gem group without weapon context — was resolved by adding an explicitly-marked slot-filler weapon, per validator semantics).
- API-GAP-blocked: **0 builds** (one API-level gap affected output rendering, see below).
- Failures/lessons: the validator's final rule requires exactly one ascendancy (B and C initially invalid as passive-only; fixed by adding fitting ascendancy nodes). Two session-driver bugs (status-case mismatch; passives added to items) produced **discarded false "valid" finals over empty states**; all chains were re-run after the fix and the printed state contents verified.

## Aggregate measurements

- Corpus size: **81** (3 mandatory, 20 coverage, 58 draws) — all sessions run, none substituted.
- Discovery API usage: **184 calls** (neighbour 100, carriers 75, resolve 9) ≈ 2.3/entry; per-entry cap 5 respected.
- Validator usage: ≈**30** invocations (validate_addition + validate_build, incl. discarded pre-fix runs and re-runs).
- Verdict counts: BUILD 4 · MULTI-USE 8 · ENABLER 13 · HUB 10 · ISOLATED 33 · ORPHAN-STAT 3 · KB-EMPTY 4 · DROPPED 1 · NONE 5 (= 81).
- Build candidates 5 → validated 4, dropped 1; UNKNOWN-blocked 0 final; API-GAP-blocked 0.
- Truncation events: **8** (Boots in-adjacency; lightning/curse tag vocabularies; minion/suppression/attribute/frenzy/chill mechanic vocabularies) — totals reported from `meta`, never treated as exhaustive.
- API GAPs: **1** — the API exposes modifier/stat identifiers but not their display text, so build sheets render exact ids unmodified (per build-output anti-hallucination rules) instead of human-readable wording.
- KB/modeling limitations observed: two ascendancy notables with zero modelled stats (#11, #18); two zero-mod uniques (#24, #28); player-unreachable orphan modifiers (`CannotDieUnique__1`, `AdditionalHolyRelicUnique__1`); an unavailable sole carrier (#54).

## Critical self-review

- **Corpus & budget respected:** yes — frozen file, byte-verified sha; 184/81 calls, no entry exceeded 5 discovery calls; build validators tracked separately as declared.
- **Session independence:** yes for discovery; one nuance — build #30's components were fetched fresh in the build phase (`resolve('Farrul')` + validators), not carried from #27's session; cross-entry links appear only in the cross-entry section.
- **Public API rules:** yes — resolve/carriers/neighbour/validators only; empty results recorded as facts; no internals opened; the one capability gap is reported as an API GAP rather than worked around.
- **Evidence-supported discoveries:** yes; every scaling claim names X, paths, and degree; **zero confirmed quadratic findings** — the single hypothesis (#30) is labelled as such.
- **Builds forced?** No. #46 was dropped on evidence; #35 and #043 carry explicitly marked open/filler slots instead of speculative components.
- **Validation claims justified?** Within validator scope — every build sheet restates that VALID covers only slot/availability/gem/ascendancy checks.
- **Build-output files:** 4 builds, 4 separate files, ids rendered faithfully with UNKNOWN/unavailable states preserved.
- **Biggest limitations:** the API's missing display-text layer (rendering fidelity), the KB's sparse modelling of some ascendancy notables and rare bases, and my own session-driver bug (caught and corrected; all affected validations re-run).
