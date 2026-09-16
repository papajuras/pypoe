# Phase 7B — Post-Fix Autonomous Discovery Rerun (2026-09-16)

Continuation of `REPORT.md` (run 1) in this directory, after: ascendancy exposure
(`passive_info` in seeds/neighbour levels), ascendancy validator (exactly-one, no-mixing,
≤4 notables), availability filtering (PoB `Source: No longer obtainable`), consumer
projection ON.

## Configuration

- `depth=3` (walks used 1–3 per query), `carrier_grouping=true` throughout.
- Starting points: `get_start_seed({'type':'UniqueItem','seed':<48-bit secrets int>,'count':3})`
  — all 15 attempt seeds recorded below. No other seed types needed.
- Validation: `phase7_build_validity.py` (check-then-commit; `validate_addition` per
  component, final `validate_build`). Commit rule: VALID→commit, INVALID→reject,
  UNKNOWN→never assumed.
- No step cap; stopping by judgment (attempts 12–15 were 1-call probes; exploration
  stopped when new branches turned repetitive/thin).

## Attempt log (15 UniqueItem random starts)

**A1** seed 187722653540647 — Saffell's Frame, Replica Soul Tether (**unbound** — replica
binding gap), Brightbeak. Flat/defensive; parked (Saffell, Brightbeak). Dead.

**A2** seed 130521123326602 — The Anvil (block + gain life/mana on block + reflect on
block), Impresence (chaos degen), Precursor's Emblem (**unbound, 2nd occurrence — gap**).
Parked The Anvil (block axis). No candidate yet.

**A3** seed 51649496073629 — Ancient Skull (minion crit + "go crazy on crit").
Followed to `mechanic:minion`; probed minion-charge stats: KB has only 2 minor
minion-charge stats — **no minion↔charge interaction layer** (coverage gap). Dead.

**A4** seed 41163025393674 — Replica Rumi's (unbound), Brinerot Flag (warcry/arcane
surge), **The Formless Inferno** (SupportedByInfernalLegion + minion life from
**overcapped fire res**). Formless Inferno followed: conversion stat →
`mechanic:minion`; Infernal Legion support gem + radius stats found; burn-damage-%-life
stat absent from KB (uncertain, recorded). → **Build A**.

**A5** seed 92500623251933 — The Ignomon (flat), Doryani's Catalyst (flat), Mask of the
Spirit Drinker (inverted ES; mods resolve to no stats in KB — **mechanics unmodeled**).
Dead.

**A6** seed 78573013183254 — Replica Winterheart (unbound), Sadima's Touch (flat),
Kiloava's Bluster (block + avoid ailments + `enemy_hits_%_chance_to_treat_elemental_
resistances_as_90%`). Consumer probe found **AscendancyCustomGladiator7 "Risky Exploit"
grants the same stat** (item↔ascendancy shared-stat link) + Gladiator block kit
(additional_block_% smalls, 'Heads' spell-block small). → **Build B** (joined with A2's
The Anvil + A1's Brightbeak after the validator rejected the shield without a 1H main
weapon — legitimate weapon_configuration catch).

**A7** seed 141742153711050 — Brute Force Solution (str→int jewel), Gorgon's Gaze
(stationary defense, no mechanic projection), Kaltenhalt (cold conversion; not pursued).
`mechanic:attribute` probed: 40+ consumer stats (damage%/crit/added per attribute).
Chieftain found granting `base_strength` broadly → **Build C** (jewel left
UNKNOWN/not-assumed: no slot model).

**A8** seed 251660278300083 — Immutable Force (single mod), Cloak of Tawm'r (minion
blind), Flesh and Spirit (**rampage/vaal-souls mechanics unmodeled**). Dead.

**A9** seed 91802386396197 — Crest of Desire (flat gem multipliers), Headhunter
(**buff-steal = single unlinked stat — mechanic unmodeled**), Emperor's Might (flat).
Dead.

**A10** seed 120897285360471 — Giantsbane (Iron-Grip-on-item, not pursued), **Pillar of
the Caged God** (attack speed per dex, AoE per int, phys per str), **Hyrri's Demise
flagged `unavailable` at seed time — live availability catch, skipped**. Pillar upgraded
Build C → fully VALID.

**A11** seed 73037626761754 — Blood of Corruption (parked), **Blood Sacrifice flagged
`unavailable` at seed time — skipped**, **Touch of Anguish** (at max frenzy → +2 chains;
frenzy on killing frozen enemy; cold claw). Consumer probe: Saboteur **"Glacial Wave"**
notable = chilled-take-more-by-chill-effect. → **Build D** (two projected mechanics:
frenzy + chill).

**A12** seed 19138154608453 — **Apparitions flagged `unavailable` — skipped**; Sundance
(flat), Mask of the Spirit Drinker (repeat, dead). Dead.

**A13** seed 79176579949079 — The Dark Seer (thin), **Pyroshock Clasp** (enemies ignited
phys→fire / shocked→lightning), Quecholli (enemies explode; not pursued). Probe:
**Elementalist "Shaper of Flames" notable grants the same ignite-conversion stat** →
**Build E**.

**A14** seed 248562363322803 — Dying Sun (flask modifiers), Saemus' Gift (lightning per
int), The Restless Ward (charge duration). Thin. Dead.

**A15** seed 214337826212774 — Replica Witchfire Brew, Restless Cycles, Kitava's Hunger
(all `availability: None` — no PoB block; cannot establish; per fail-closed convention
not assumed available either, just unchecked). No candidate.

## Successful builds

### Build A — Overcapped Fire-Res Minion Burn (recombination)
- **Committed:** The Formless Inferno (available ✓) + Summon Skeletons + Infernal Legion
  Support (support chain valid) + Necromancer notables Mindless Aggression (minion
  life/damage FINAL) + Bone Barrier (minion life→ES, phys-red per minion). 2/4 notables,
  1 ascendancy. FINAL: **unknown** — only because the gem group's weapon_check is skipped
  (no weapon-class item equipped); item availability + ascendancy checks clean.
- **Chain (graph-evidenced):** overcapped fire res (gear) →
  `minion_life_increased_by_overcapped_fire_resistance` → `mechanic:minion` → Infernal
  Legion radius stats; Necromancer FINAL multipliers scale minion life (the burn fuel).
- **Uncertain:** Infernal Legion burn %-of-life damage stat is not in the KB (only radius
  stats + display stat) — payoff modeled indirectly.
- Emerged from: A4 random anchor → conversion stat → mechanic:minion → ascendancy probe
  (Necromancer notable stat grants verified via `passive_info`).
- ~6 API calls.

### Build B — Gladiator Block Tank (recombination, cross-attempt)
- **Committed (fully VALID):** Brightbeak (1H mace) + Kiloava's Bluster (shield) + The
  Anvil (amulet) + Gladiator: Risky Exploit (notable) + 'Heads' (small). 1/4 notables.
- **Chain:** additional_block_% (Gladiator kit) → block defense;
  gain life/mana on block (The Anvil) → recovery; reflect-on-block (Anvil) → offense;
  shared stat `enemy_hits_..._treat_elemental_resistances_as_90%` (Kiloava's item =
  Risky Exploit notable) → item↔ascendancy evidence link.
- Validator catch recorded: shield without 1H weapon → INVALID until Brightbeak added.
- Emerged from: A2 + A6 + A1 parts (parked candidates from earlier attempts composed
  after the ascendancy link was found).
- ~8 API calls.

### Build C — Chieftain Attribute Stacking (recombination)
- **Committed (fully VALID):** Pillar of the Caged God (2H; per-dex/int/str scaling) +
  Chieftain "Defences and Strength" notable (base_strength + global defences). Smalls
  uncounted. Jewel component (Brute Force Solution str→int) = **UNKNOWN (no slot model),
  rejected-commit, not assumed**.
- **Chain:** base_strength (Chieftain generator) → str consumer fan-out (life, armour,
  block-per-str, added fire/phys, crit) → weapon per-attribute stats (Pillar);
  str→int jewel conversion → int consumers (uncertain: conversion semantics not graph-
  verifiable beyond the stat's existence).
- Emerged from: A7 jewel → mechanic:attribute fan-out → ascendancy sweep (Chieftain
  grants strength).
- ~7 API calls.

### Build D — Frenzy-Chain Chill (recombination, two projected mechanics)
- **Committed (fully VALID):** Touch of Anguish (claw; max frenzy → +2 chains; frenzy on
  frozen kill) + Frost Blades + Chain Support (support + weapon checks valid) + Saboteur
  "Glacial Wave" notable (chilled take more, scaled by chill effect). 1/4 notables.
- **Chain:** cold hits → `mechanic:chill` (projected) → chill-effect-amp (Glacial Wave);
  frozen kills → frenzy (converter stat) → max-frenzy → chains → Frost Blades chain
  fan-out; `mechanic:frenzy_charge` (projected).
- Emerged from: A11 anchor → frenzy/chain stats → chill-scaling ascendancy probe.
- ~5 API calls.

### Build E — Enemy-ailment conversion ignite (recombination, thin)
- **Committed (fully VALID):** Pyroshock Clasp (belt; ignited phys→fire, shocked→lightning)
  + Elementalist "Shaper of Flames" notable (same conversion stat family; always-ignite).
  1/4 notables.
- **Chain:** ignite mechanic (projected) → enemy-side conversion stats shared between
  belt and ascendancy notable → fire-damage scaling (generic consumer, no deep fan-out
  verified). Weakest of the five — kept because the item↔ascendancy shared-stat link is
  genuine graph evidence.
- Emerged from: A13 anchor → conversion mod → shared-stat ascendancy probe.
- ~4 API calls.

### Ascendancy: unresolved cases
None — all five builds established an evidence-based ascendancy (0 unresolved). The
weakest evidence is Build E (single shared stat); strongest are B (three independent
stat links) and A (two notables with direct mechanic stats).

## Unavailable-content encounters
- Hyrri's Demise (A10), Blood Sacrifice (A11), Apparitions (A12) — **flagged at seed
  time and skipped before any exploration cost**. Blood Sacrifice and Apparitions were
  also `unavailable` items that would previously have entered exploration.
- 3 names with `availability: None` (no PoB block) — not assumed available (A15).
- No build commit ever contained an unavailable item.

## Comparison with run 1

| Metric | Run 1 | Run 7B |
|---|---|---|
| Random attempts | 15 | 15 |
| Build concepts | 3 | 5 |
| Fully VALID finals | 1 (Build B-equivalent class only) | 4 |
| Ascendancy established | 0 (state model crashed) | 5/5, ≤2/4 notables used |
| Availability filtering | none (Serle's-class risk unknown) | 3 live catches at seed time |
| Dead-end attempts | 9 | 10 |
| Multi-mechanic builds | 1 (Build #2, 2 layers) | 2 (A: 3 layers; D: 2 mechanics) |
| Unknown-status finals | 2 (jewel; gem-weapon) | 1 (Build A gem-weapon only) |

**Measured (not impression) improvements:**
1. Legal composition: ascendancy commits went from impossible (ValueError crash) to 5/5
   validated with mixing/cap enforcement — Build B additionally shows the weapon-
   configuration constraint catching a shield-without-weapon error.
2. Ascendancy selection: `passive_info` exposure + `passive_grants_stat` probes made
   evidence-based ascendancy links findable in-graph (three item↔ascendancy shared-stat
   links discovered: Kiloava's/Risky Exploit, Pyroshock/Shaper of Flames, Formless/
   Necromancer notables).
3. Unavailable content: 3 real candidates (Hyrri's Demise, Blood Sacrifice, Apparitions)
   removed at zero exploration cost; previously they would have been probed and possibly
   committed.
4. Multi-mechanic reasoning: projected mechanics (minion, chill, frenzy, ignite,
   attribute) anchored 4 of 5 builds; run 1 had 1.
5. Feasibility awareness: 2 live validator catches (shield/1H; gem weapon-context
   unknown) shaped final compositions honestly.

**Remaining limitation (single most important):** gem-group weapon-context UNKNOWNs —
KB gem records lack weapon tags (run-1 finding, unchanged), so attack-skill groups keep
finals at UNKNOWN (Build A) unless the skill has no weapon restriction (D validated via
Frost Blades' claw path). Secondary: jewels/cluster jewels have no slot model; replica/
index uniques are unbound.

## Convergence observations
- Parked candidates from dead attempts (Anvil, Brightbeak) became build components —
  parking paid off.
- Three of five builds are ascendancy-linked via *shared-stat* convergence (item and
  ascendancy granting the same stat) — an emergent, repeatable discovery pattern.
- Repetition: replica uniques repeatedly unbound (4×); attribute/mechanic-adjacent flat
  uniques repeatedly dead. No attempt needed re-walking previously visited mechanics.

## Final verdict
1. Yes — material improvement, measurable on all six axes above.
2. Yes — 4/5 builds fully VALID; the 5th is unknown only through a pre-existing gem-tag
   gap, not a composition fault.
3. Yes — every ascendancy was selected from graph evidence (shared-stat or direct stat
   grants), then validator-committed.
4. 0/5 unresolved (vs 3/3 in run 1).
5. Yes — 3 live rejections; commit-time availability checks enforce the rest.
6. Yes — multi-hop chains remain (e.g. overcapped res → minion life → burn; frozen-kill
   → frenzy → chains → chill-amp).
7. The removed step limit caused no exploration spiral: attempts averaged 2–6 calls;
   stopping criteria (repetition/thinness) fired naturally. Mild benefit: follow-through
   (A6→B, A7→C) without budget pressure.
8. Most important remaining limitation: KB gem weapon-tag gaps → weapon-context
   UNKNOWNs that block full VALID on attack-skill builds.
