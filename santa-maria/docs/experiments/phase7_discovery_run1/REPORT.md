# Phase 7 — Autonomous Build Discovery (run 1, 2026-09-16)

Config: `depth=3` (used 1–3 per query), `carrier_grouping=true`, ≤40 exploration steps/attempt.
All starting points via `phase6_api.get_start_seed` with `type` filter + API `seed` int
(48-bit `secrets.randbits`); every seed recorded below. No DB access outside the API.
Validity via `phase7_build_validity.py`; projection state = consumer projection ON
(6 mechanics: ignite, suppression, attribute, chill, frenzy_charge, minion).

---

## Attempt log

**A1 — UniqueItem, seed 56168889020016 → Replica Quill Rain (unique:1179).**
Graph returned only `unique_in_class → Bow`; zero modifier bindings. Dead end (unbound node).

**A2 — UniqueItem, seed 223332072232359 → The Apostate (unique:1430).**
Mod → `gain_maximum_life_instead_of_maximum_es_from_armour_at_x%_of_the_value`; stat is a
leaf (no scaling/mechanic/consumer edges). Dead end (isolated conversion).

**A3 — Stat, seed 258178662162125 → `clarity_reserves_no_mana`.** Orphan node, depth 3 empty.

**A4 — Stat, seed 166405350858732 → sample of 3**
(`chart_contains_x_additional_starfish_packs`, `map_favour_from_zana_missions_+%`,
`enchantment_boots_attack_and_cast_speed...`). All unlinked domain junk. Dead end.
*Pattern: random Stat anchors overwhelmingly land on unbound/leaf stats.*

**A5 — Passive, seed 13421915908144 → atlas_map_drops_21.** Atlas passive → scarab-drop stat
→ leaf. Dead end (atlas domain).

**A6 — Gem, seed 266839398540223 → SummonHarbingerOfFocus.** Display stats only, leaf. Dead end.

**A7 — UniqueItem, seed 118893341758430 → sample of 3 → Roth's Reach (unique:450) bound.**
Followed `Additional Chain` → `stat:number_of_chains`: consumer fan-out to ~30+ projectile
skills (Arc, Frost Blades, Lightning Trap, Molten Strike, Cobra Lash, Kinetic Fusillade…).
Found `projectile_damage_+%_per_chain` (per-chain multiplier) — only **one** KB source
(corrupted implicit). `spectral_shield_throw_fire_shards_on_chain` — unbound (leaf).
Committed components: Roth's Reach + Chain Support + skill.
- Validator: "Lightning Strike" / "Cobra Lash" → **invalid**: `Bow not in weapon_restrictions`.
  KB gem-tag gap: Cobra Lash has only `attack, chaos` tags (no weapon tags recorded) —
  validator fails closed. With "Lightning Trap" + Chain Support → **VALID**.

**Build #1 (VALID, recombination):** *Chain-stack trap ballista* — Roth's Reach (+chains bow) →
Chain Support → Lightning Trap (per-chain fan-out consumer). Limitation (honest): per-chain
damage multiplier exists as a stat but is obtainable from a single corrupted implicit in the
KB; on-chain triggers unbound. Depth: axis + consumer fan-out only — no confirmed second layer.

**A8 — Gem, seed 30802922796613 → IceSpearRoyale.** Second-form crit chance/multiplier +
projectiles_return. Probed: second-form stats granted only by IceSpear itself — gem-internal
mechanic, no external layer. Parked with revisit reason (external crit consumers), dropped
when probing showed no outside grants. Dead end.

**A9 — UniqueItem, seed 15561159994530 → Conqueror's Longevity (unique:376).**
`avoid_all_elemental_status_%` — many sources (eldritch implicits, uniques 1087/1351/1402)
but no `stat_mechanic_relation` edges (ailment-avoidance thresholds not modeled as mechanics).
Defense stack with no scaling core → no build.

**A10 — UniqueItem, seed 184828770947377 → Bloodgrip (unique:1030).** Life regen, leaf. Dead end.

**A11 — UniqueItem, seed 129274041397682 → sample of 3** (The Green Dream, The Highwayman,
The Dancing Dervish — all bound). Explored The Green Dream:
- `mod:ColdResistAlsoGrantsFrenzyChargeOnKillJewelUnique__1` — cold res → frenzy on kill.
- `mod:ChaosDamageAsPortionOfColdDamageUnique__1` → `cold_damage_%_to_add_as_chaos`.
- `mechanic:frenzy_charge` consumer fan-out (truncated at 30): attack/cast speed per charge,
  `cold_damage_+%_per_frenzy_charge`, **`cold_damage_%_to_add_as_chaos_per_frenzy_charge`**
  (feedback: charges → more cold-as-chaos), **`bow_attacks_turn_frenzy_charges_into_additional_arrows`**
  (host unique:1330 = The Gluttonous Tide), `attacks_poison_while_at_max_frenzy_charges`
  (host = Dex/Int gloves mod, unique host not found in KB — uncertain obtainability).
- Obtainability: converters bound to single mods each (charge→arrows = Gluttonous Tide only).
Committed: The Gluttonous Tide + The Green Dream + Toxic Rain.
- Validator: overall **unknown** only because The Green Dream is a Jewel (no slot model);
  bow+gem group **valid**, jewel never assumed valid.

**Build #2 (VALID modulo jewel-unknown):** *Cold-res Frenzy Engine* — The Green Dream
(generator: cold res → frenzy on kill; converter: cold→chaos) → The Gluttonous Tide
(converter: frenzy → additional arrows) → frenzy consumers (per-charge speed, cold%/charge,
poison-at-max). Layers: generator → multiplier → converter → consumer. Genuine multi-hop
architecture discovered from a random anchor; damage-type feedback (charges amplify the cold
that the amulet converts) is non-obvious.

**A12 — Gem, seed 164834022755626 → UniqueSupportCastOnShockedKill.** Single stat leaf; no
`shock` mechanic projected (only 6 mechanics in graph). Dead end — projection coverage limit.

**A13 — Passive, seed 16507656727640 → AscendancyCustomHeirophant18.**
`maximum_life_%_to_add_as_maximum_energy_shield` + `minion_maximum_life_%_to_add_as_maximum_energy_shield`
→ `mechanic:minion`. Found a **two-way bridge**: player life→ES applies to minions
(Hierophant18, Necromancer9 — Necromancer9 also grants phys reduction per minion), while
`additive_minion_maximum_life_modifiers_apply_to_you_at_%_value` applies minion-life to the
player (sources: MinionLifeAlsoAffectsYouUnique__1 / Divergent variant — **no unique host
edge in KB**, obtainability uncertain). `all_res_%_per_active_minion` exists as consumer
(matches prior finding: 0 unique hosts — honest negative).
Committed: Soul Tether (unique:618, ES-as-%-of-life belt) + Summon Skeletons group
→ **VALID** (ascendancy passives not modeled by validator — recorded).

**Build #3 (VALID):** *Life↔ES minion bridge* — Hierophant18/Necromancer9 (life→ES also on
minions; minion count → phys reduction) + Soul Tether (ES→life) + minion-life-also-affects-you
(uncertain) + minion consumers (res per minion, minion damage→you at 150%). Layers: two
converters + defense consumers. Bridge mod obtainability = the uncertain pillar.

**A14 — UniqueItem, seed 188753777404913 → Maligaro's Lens (unique:284).**
Heal-allies-on-death shield, leaf. Dead end.

**A15 — UniqueItem, seed 52155214111644 → sample of 3** (Thousand Ribbons — flat stats;
Windshriek — boots incl. `immune_to_curses`, leaf; Precursor's Emblem — no mod bindings).
All dead ends.

---

## Multi-hop discoveries (real graph chains)
1. A7: unique → Additional Chain → `number_of_chains` → 30+ skill consumers →
   `projectile_damage_+%_per_chain` (1 source only).
2. A11: unique → cold-res→frenzy mod → `mechanic:frenzy_charge` → cold%/frenzy →
   cold-as-chaos/frenzy; separate chain frenzy→additional arrows → Gluttonous Tide host.
3. A13: passive → life→ES → `mechanic:minion` → minion-life-also-affects-you bridge →
   Soul Tether (ES→life).

## Recurring patterns / limitations
- **Random anchors are noisy:** 15 attempts → ~9 outright dead ends (unbound/orphan/leaf
  nodes, atlas/league-domain junk). Productive hits came from bound Unique/Passive anchors.
  Exploration productivity requires an API-supported text lookup (`id_contains`) plus
  directed-iterative probing — plain BFS caps starve hub nodes (matches prior findings).
- **Leaf-conversion stats dominate:** single-stat conversions (Apostate, Bloodgrip,
  Maligaro's Lens) have no KB edges to consumers; cannot be judged as builds.
- **Mechanic projection coverage:** only 6 mechanics projected; shock (A12) absent.
- **Validator gap:** bow-attack skill gems (Lightning Strike, Cobra Lash) carry no weapon
  tags in the KB → fail-closed rejection; bow+trap gem groups validate fine. Jewels/ascendancy
  unmodeled (unknown, never assumed valid).
- **Obtainability asymmetry:** several key converter stats bind to exactly one mod
  (Gluttonous Tide, Roth's Reach chain implicit, poisoned-at-max-frenzy gloves) — the KB
  exposes single-source fragility clearly, which is valuable.

## Were builds genuinely discovered?
Yes for the mechanics, with caveats. No attempt started from prior knowledge: each concept
emerged from API-random anchors and graph-returned neighbours (A11's cold-res→frenzy→arrows
architecture and A13's life↔ES minion bridge were not planned; both followed edges the
random anchors surfaced). Prior game knowledge was used only to read stat text. Builds #1's
per-chain-multiplier weakness and #2/#3's single-source converters are reported as found —
the graph does not claim them strong, and neither do I. Classification: #1 = recombination,
#2 = recombination with a non-obvious feedback edge, #3 = recombination (bridge direction is
the non-obvious part). Nothing qualifies as clearly non-obvious system design; all three are
shallow-to-moderate multi-layer stacks the KB supports end-to-end.

## Assessment
The current system **can** discover coherent multi-mechanic concepts from random anchors
(2 of 15 attempts yielded real architectures, 1 more yielded a valid single-axis build), but
yield is dominated by dead ends, and depth is limited by (a) sparse projection coverage,
(b) leaf conversions with no consumer edges, (c) gem-tag gaps that make the validator reject
valid-in-game weapon pairings. Directed-iterative probing + `id_contains` lookups are
essential; plain randomized BFS alone would have surfaced nothing.
