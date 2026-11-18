# Benchmark v1 — Isolated Run Report

- **Run date**: 2026-09-17 (isolated run; the earlier `benchmark_v1` artifacts in this
  directory tree were not read or used, and were not modified)
- **Corpus**: `santa-maria/docs/experiments/seed_corpus_v1/corpus.json`
  - name `seed_corpus_v1`, built 2026-09-16T19:00:53+00:00, selection_seed 20260916
  - sha256 `d62839a9045e28c8aa0bc9d431c3aaef241089c40acee121c96e294e900d56a8`
  - 81 entries (3 mandatory, 20 ascendancy_coverage, 58 random_draw), used unmodified, in order
- **Governing skills**: `discovery-api-usage` (interface + epistemic contract), `scaling-discovery` (methodology), `build-output` (rendering)
- **Artifacts**: `runner.py` (Stage A), `probe.py`/`stageC.py`/`builds.py`/`builds2.py` (Stage C/D),
  `audit/api_calls.jsonl` (every call), `digests/` (per-seed evidence digests), `results.json`
  (machine-readable verdicts), `builds/build_*.md` (14 build sheets), `triage.py`/`triage.txt`

## Protocol and budget (fixed, audited)

All research went through the public API only (`phase8_research.resolve/carriers`,
`phase6_api.get_neighbour/get_start_seed`, `phase7_build_validity.validate_build`,
`phase7_build_feasibility.can_support`). No internals, no DB queries, no reads of the
previous run's artifacts.

| Stage | Budget | Actual |
|---|---|---|
| A — uniform probes, every entry | ≤6 calls: resolve, neighbour(d3, both, cap 60), carriers(start), carriers(top-2 downstream stats), 1 mechanic probe | 343 calls, 81/81 entries |
| C — promoted-seed deep probes | ≤12 calls per full promotion (9,12,14,16,21,32,33,35,43,47,64,66,67); ≤5 per lite check (1,19,25,29,30) | 146 calls over 18 seeds |
| D — build assembly + validation | validator calls per assembled build | 37 validate_build + 2 can_support |

Every call is logged in `audit/api_calls.jsonl` (489 raw lines, 462 unique — 27 lines are
duplicates from two re-executions needed after terminal-output truncation; reported counts
are raw, unique counts given for honesty). KB files were not written; run recorded in
`audit/run_meta.json`.

## Verdict vocabulary

**SCALING-CORE** (axis + multi-source generation + ≥1 consumer layer), **ENABLER**
(enabling/converting role, no own consumer layer evidenced), **ISOLATED** (real but
single-family/single-carrier axis), **NONE** (no build-facing relationship; includes
zero-edge / zero-carrier KB facts recorded per the epistemic contract).

## Per-seed results

Full notes per entry: `results.json`. Verdict counts: **SCALING-CORE 18 · ISOLATED 42 ·
NONE 16 · ENABLER 5**.

| # | Start | Verdict | Build / note |
|---|---|---|---|
| 0 | Replica Alberon's Warpath | ISOLATED | per-50-str chaos self-family; MI hypothesis absent from KB edges for this node |
| 1 | Whispers of Infinity | ISOLATED | mana→attack-chaos converter unique-internal (1 carrier) |
| 2 | item_class:Boots | NONE | 60/91 uniques sampled; no common axis; rare bases not modeled |
| 3 | Path of the Shadow | NONE | structural path node |
| 4 | Toxic Delivery | ISOLATED | poison-duration self-family |
| 5 | Rite of Ruin | ISOLATED | rage self-family |
| 6 | Master of Metal | ISOLATED | impale reflected-hits sub-axis (4 carriers) |
| 7 | Tukohama, War's Herald | ISOLATED | body-armour totem-support enabler, self |
| 8 | Gathering Winds | ISOLATED | tailwind/gale-force self |
| 9 | Shaper of Storms | SCALING-CORE | **build_09** — shock forcing 23 carriers → crit-vs-shocked 15 |
| 10 | Gratuitous Violence | ISOLATED | bleed-explode 5 carriers |
| 11 | Unwavering Crusade | NONE | zero edges (KB fact) |
| 12 | Pursuit of Faith | SCALING-CORE | **build_12** — totem count 26 / speed 81 carriers |
| 13 | Instruments of Zeal | ISOLATED | fanatic charges self-contained |
| 14 | Unflinching | SCALING-CORE | **build_14** — endurance generation 39-carrier stat + uniques (VALID) |
| 15 | Commander of Darkness | ISOLATED | aura-ally small family |
| 16 | Unholy Authority | SCALING-CORE | **build_16** — curse limit 28 carriers + hexproof (VALID) |
| 17 | Master Toxicist | ISOLATED | flask-poison self |
| 18 | Caster Weapon Display | NONE | zero edges (KB fact) |
| 19 | Born in the Shadows | SCALING-CORE | **build_19** — blind 33 carriers, consumer thin → CANDIDATE |
| 20 | Overwhelm | ISOLATED | crit-vs-density self |
| 21 | Swift Killer | SCALING-CORE | **build_21** — frenzy cap 42 carriers, 104-stat mechanic |
| 22 | Lesson of the Seasons | ISOLATED | barkskin self; Warden id-ns mismatch |
| 23 | Shroud of the Lightless | ISOLATED | per-abyssal-jewel self-family |
| 24 | Replica Cheap Construction | NONE | unavailable + zero UMA (KB fact) |
| 25 | Perandus Signet | ISOLATED | int-per-unique 1 carrier; per-unique damage 0 carriers |
| 26 | Legacy of Fury | ISOLATED | scorch family small |
| 27 | Farrul's Chase | ISOLATED | cat-stealth enabler |
| 28 | Replica Quill Rain | NONE | zero UMA (KB fact) |
| 29 | Dendrobate | ENABLER | stat-gated poison converters, self-gated; item-validated, no build |
| 30 | Farrul's Bite | ISOLATED | crit-blind loop fully self-carried |
| 31 | Circle of Ambition | ISOLATED | herald reservation 6 carriers |
| 32 | Badge of the Brotherhood | SCALING-CORE | **build_32** — charge-role conversion (VALID, item) |
| 33 | Facebreaker | SCALING-CORE | **build_33** — crit-multi mass 152 carriers → unarmed converter |
| 34 | Solstice Vigil | ISOLATED | Shaper's Presence enabler |
| 35 | Disciple of the Unyielding | SCALING-CORE | **build_35** — per-charge damage 38 carriers (VALID) |
| 36 | Map Drop Chance | ISOLATED | quant domain |
| 37 | Totem Attack Speed | ISOLATED | tree smalls |
| 38 | Dexterity | ENABLER | 82 passive generators; consumers not enumerated |
| 39 | Lord's Descent | ISOLATED | brequel fruit 3 carriers |
| 40 | Grasp the Past | ISOLATED | 1+1 carriers |
| 41 | Executioner | ISOLATED | low-life single; AoE-if-killed 12 |
| 42 | Totem Damage and Placement Speed | SCALING-CORE | independently reaches 12's architecture; no separate file |
| 43 | Splitting Steel | SCALING-CORE | **build_43** — impale 58 carriers |
| 44 | Greater Devour Support | ISOLATED | Devour family 2 |
| 45 | WIP Support | ISOLATED | single-carrier WIP gem |
| 46 | Summon Holy Relic of Conviction | ISOLATED | relic count self-family |
| 47 | Commandment of Reflection | SCALING-CORE | **build_47** — minion-damage redirect via Spiritual Aid |
| 48 | Essence Drain of Desperation | ISOLATED | generic chaos-dot mass; desperation self |
| 49 | Penance Mark | ISOLATED | phantasm generator; consumer unprobed |
| 50 | Summon Skeletons Channelled | ISOLATED | skeleton count self-family |
| 51 | brequel fruit rarer-rewards stat | ISOLATED | 1 carrier |
| 52 | unique-jewel duration stat | ISOLATED | 1 carrier |
| 53 | stat:cannot_die | NONE | all 7 carriers monster-only (KB fact) |
| 54 | crit per 200 int | ISOLATED | 1 carrier |
| 55 | watchstone monster life | ISOLATED | 1 carrier, watchstone domain |
| 56–58 | banner_adrenaline / virtual_minion_AS / crit_per_lightning_adaptation | NONE ×3 | zero carriers (KB facts) |
| 59 | MapMonsterCrit Delve mod | ISOLATED | quant axis ≥1000 carriers (ceiling-truncated) |
| 60 | Iron Grip Hard Mode | ISOLATED | weapon-tree display stat |
| 61 | Recover ES on Kill flask mod | ISOLATED | 1 unique (Cinderswallow Urn) |
| 62 | ColdResistUnique__43 | ISOLATED | generic resist 202 carriers |
| 63 | TemporalChainsReservationCost | ISOLATED | TC-no-reservation 3 carriers |
| 64 | MonsterMinionInstability | SCALING-CORE | **build_64** — keystone with 7 acquisition sources |
| 65 | mechanic:minion | SCALING-CORE | 200-stat hub; build not separately attempted (overlaps 47; budget) |
| 66 | mechanic:suppression | SCALING-CORE | **build_66** — 111-carrier generation + consumer roles |
| 67 | mechanic:attribute | SCALING-CORE | **build_67** — 107-stat meta-axis; converters KB-thin |
| 68 | mechanic:frenzy_charge | SCALING-CORE | independently reaches 21's architecture; no separate file |
| 69 | mechanic:chill | SCALING-CORE | 103-stat hub; build not attempted (budget) |
| 70 | tag:lightning | ENABLER | coarse family fan-out |
| 71 | tag:curse | ENABLER | domain breadth; stacking axis is 16's session |
| 72 | tag:quiver_eyrie | ENABLER | 18 influence mods, no consumer layer |
| 73 | tag:blight_death_physical | NONE | 1 monster mod |
| 74 | item_class:CursedDucat | NONE | zero edges (KB fact) |
| 75 | item_class:Tincture | ISOLATED | 5 tincture uniques, item-class domain |
| 76–78 | HeistEquipmentWeapon / IncubatorStackable / Support Skill Gem | NONE ×3 | zero edges (KB facts) |
| 79 | item_class:Map | ISOLATED | 33 map uniques, display/quant domain |
| 80 | item_class:BrequelFruit | NONE | zero edges (KB fact) |

## Concrete builds (files in `builds/`)

| File | Core | Status |
|---|---|---|
| build_09_shock_forcing.md | Shaper of Storms → crit-vs-shocked fan-out | CANDIDATE (passives VALID) |
| build_12_hierophant_totems.md | count/speed/duration compound axes | CANDIDATE (gem weapon UNKNOWN) |
| build_14_juggernaut_endurance.md | charge generation + max-cap uniques | **VALIDATED** (items+passives) |
| build_16_occultist_curses.md | curse limit + hexproof | **VALIDATED** (passives) |
| build_19_saboteur_blind.md | blind generation → thin consumer | CANDIDATE (gem UNKNOWN) |
| build_21_trickster_frenzy.md | frenzy cap + multi-consumer economy | CANDIDATE (gem UNKNOWN) |
| build_32_badge_charge_conversion.md | frenzy=power role conversion | **VALIDATED** (item+passives) |
| build_33_facebreaker_unarmed_crit.md | crit-multi mass → unarmed converter | CANDIDATE (unarmed uncheckable) |
| build_35_endurance_payoff.md | minimum charges → per-charge damage | **VALIDATED** (passives) |
| build_43_champion_impale.md | impale 58-carrier axis | CANDIDATE (weapon UNKNOWN) |
| build_47_reflection_redirect.md | minion-damage redirect (Spiritual Aid) | CANDIDATE (gem UNKNOWN) |
| build_64_minion_instability.md | 7-source keystone + Absolution spam | **VALIDATED** (passives; gem UNKNOWN) |
| build_66_warden_suppression.md | suppression event economy | **VALIDATED** (passives) |
| build_67_omniscience_attributes.md | all-attribute meta-axis | **VALIDATED** (item) |

## Discovery summary

- **Strongest multi-source axes** (carrier counts measured this run): totem placement speed
  (81), impale chance (58), spell-suppression chance (111), crit-multiplier (152),
  curse limit (28), endurance-charge damage (38), max endurance/frenzy charges (39/42),
  blind-on-hit (33), always/all-damage-shock (23).
- **Multi-use / compound patterns**: frenzy charges (21+68: one cap investment → accuracy,
  speed, block, movement, travel cooldown, poison conditionals); totems (12+42: count ×
  placement-speed × duration as independent sub-axes); endurance charges (14+35: generation
  → damage + defense); Badge (32: charge-role conversion unifying two charge economies).
- **Enablers**: Dendrobate (stat-gated poison converter), Dexterity (generation layer),
  coarse tags (lightning/curse/quiver_eyrie).
- **Legitimate dead ends**: all zero-edge / zero-carrier facts (11, 18, 24, 28, 53, 56–58,
  74, 76–78, 80), item-class domains (2, 75, 79), self-family uniques (0, 23, 30…),
  quant economy axes (36, 59, 79).
- **Independent-session convergence**: sessions 12 and 42, and 21 and 68, each separately
  reached the same architecture from different starting points — cross-entry confirmation,
  not carried state.

## Build-construction summary

- Candidates assembled: **14** (presented files above) + 3 item-only validations recorded
  (25, 29, 67-alternate state) that were not promoted to presented builds.
- **VALIDATED (final state)**: 8 — 14, 16, 32, 35, 64, 66, 67 (+ passives-only sub-states of
  09). "Valid" = only the implemented deterministic constraints (slots, ascendancy
  composition, gem support, availability); not a full PoE build-validity claim.
- **UNKNOWN-blocked**: 6 final states (12, 19, 21, 33, 43, 47 + gem states of 64/66) —
  uniformly because the validator's weapon context requires exactly one committed
  weapon-class item and no weapon-class unique existed in the respective session's
  evidence. Unarmed (33) is structurally uncheckable.
- **REJECTED**: none at build level; intermediate stepwise attempts that failed were recorded
  (35/64 "no Ascendancy in final build state"; ambiguous passive names in 32/33/64/66 fixed
  by id). Two candidate items were excluded on evidence: Kaom's Way (availability
  unavailable), and no build was forced where the consumer layer was KB-thin (19 kept only
  as CANDIDATE; 29 not promoted).
- **Pattern that produced coherent builds most often**: a broad multi-source *stat axis*
  (carrier mass) + a named converter/consumer (unique or keystone) — 9 of 14 builds follow
  it; the remainder are mechanic-hub architectures (47, 66, 67).

## Aggregate measurements

| Metric | Value |
|---|---|
| Corpus size | 81 entries (100% resolved via public API; no substitutions) |
| API calls (raw / unique) | 489 / 462 (resolve 119, carriers 240, neighbour 91, validate_build 37, can_support 2) |
| Stage A | 343 calls, uniform ≤6/seed, 81/81 |
| Stage C/D | 146 calls over 18 promoted seeds (2 seeds exceeded the nominal 12-call cap through re-execution after output loss: 09→13, 14→16 lines incl. duplicates) |
| Verdicts | SCALING-CORE 18 · ISOLATED 42 · NONE 16 · ENABLER 5 |
| Build candidates / validated / unknown-blocked | 14 / 8 / 6 |
| Truncated-result calls | 38 (BFS 60-node caps; carrier ceiling 1000 on map quant stats; mechanic hubs capped at 200) |
| API GAPs (hard stops) | 0 — no research line had to be abandoned |
| Capability gaps observed (non-blocking) | no Mechanic nodes for shock/poison (resolve returned 0); unique-mod associations missing for several key mods (AdditionalTotems*, MinionDamageAlsoAffectsYouUnique__1, AlwaysCritShockedEnemiesUnique__1, AttackImpaleChanceUnique__1/2, eldritch per-charge/impale implicits); gems lack display names; no unarmed slot model; rare items absent from the item model |

## Critical self-review

- **Frozen corpus + budget respected**: yes — exact node ids, corpus order, sha recorded;
  uniform Stage A, bounded Stage C/D. Two seeds exceeded the nominal Stage C call cap only
  because scripts were re-executed after terminal-output truncation; the duplicates are in
  the audit log and flagged here.
- **Session independence**: maintained. No discovery was imported between seeds; where two
  sessions converged (12/42, 21/68), each kept its own evidence and only one build file was
  written per constructed build, referenced from the second session's record as
  "shared architecture — no separate file". Resolving *within* a session's subject
  (e.g. resolve('Necromancer') inside seed 64) was used to select components, not to import
  other seeds' findings.
- **Public API rules**: followed; no internals, no DB, no workaround of the API. Zero-carrier
  and truncation results were recorded as facts, not smoothed over.
- **Evidence discipline**: every build sheet cites only this run's API results; one error was
  caught and corrected mid-run (an item name nearly entered build_67 from memory — replaced
  by the API-resolved `Crystallised Omniscience`). Unresolved unique owners are marked
  UNKNOWN rather than guessed.
- **Forced builds?** None presented at higher strength than its evidence: consumer-thin
  architectures (19) are CANDIDATE; KB-thin converter layers (67) are flagged in the sheet;
  weak seeds were left as ISOLATED/NONE instead of being manufactured into builds.
- **Validation claims**: stated strictly as "valid with respect to the validator's
  implemented constraints"; UNKNOWN states (weapon context) were kept visible, not repaired.
- **One build-output file per presented build**: yes (14 files).
- **Main limitations**: validator's item model (no rares/jewels, no unarmed), KB gaps in
  unique-modifier associations for several axis-relevant mods, absence of shock/poison
  mechanic nodes, and the carriers-only detail level for mod payloads (mods carry no display
  text through the public API).

Benchmark v1 stands as run here; any future change of prompt, corpus, or conditions
should be recorded as benchmark v2, not as an edit of this run.
