# Phase 7C — Multi-Consumer / Compound-Scaling Discovery Run (2026-09-16)

Third run in this directory (7A = `REPORT.md`, 7B = `RERUN_REPORT.md`). Focus of this
run: distinguish single-use scaling from multi-use (`X → A, B, C`) and compound
(`X → A, X → B, A + B → additional effect`) architectures, and distinguish genuine
synergy components from slot fillers.

## Configuration

- `depth=3` configured; in practice surgical per-hop walks of depth 1–3 with targeted
  `edge_types` subsets (a full depth-3 all-edge walk from a weapon explodes into the
  generic mod space via carrier grouping, so per-hop edge targeting was used instead —
  same walk budget, no KB modification).
- `carrier_grouping=true` throughout, except targeted flat (ungrouped) queries when the
  carrier of a stat had to be identified.
- Random starts: `get_start_seed({'type':'UniqueItem','count':3,'seed':<48-bit secrets
  int>})` — **15 draws used, exactly the cap** (draw seeds recorded per attempt).
- No step limit; stopping by judgment. Thin branches got 1–3 queries; compound branches
  were followed down to *carrier level* (which item/passive/gem carries each consumer
  stat), which is what the multi-consumer focus requires.
- Validator: `phase7_build_validity.py` check-then-commit (`validate_addition` per
  component, final `validate_build`); feasibility: `phase7_build_feasibility.py`
  (`can_support`). `phase7_consumer_project.py` was not invoked; consumer fan-out was
  established directly via `stat_mechanic_*` edges and in-edge carrier scans through the
  API.
- Committed ascendancies: exactly one per build, ≤4 notables, never mixed, UNKNOWN never
  assumed. Jewels: no slot model → never assumed (documented per instance).

## Attempt log (15 UniqueItem random starts)

**S1** draw seed 259582546764858 — Corrupted Energy (unavailable), Warrior's Tale
(unavailable), **Jorrhast's Blacksteel** (available). → **Build A**.

**S2** draw seed 164451715265964 — Might of the Meek (small-passive-effect multiplier;
multiplier, not an axis — no consumer layer in KB), Defiance of Destiny (single
missing-life-on-hit stat), Kitava's Thirst (mana-spend trigger enabler). The three do
not converge, but the mana-spend probe surfaced a genuine fan-out (below) → **Build B**.

**S3** draw seed 139041244456405 — Replica Badge of the Brotherhood (**unbound**: zero
`unique_modifier_association` edges — KB gap), The Beachhead (availability `None` — map,
not a build component), **Grand Spectrum** (+1 minimum power charges per stackable
jewel). → **Build C**.

**S4** draw seed 68653833514123 — **Replica Voidwalker** (chain while phasing), Pillars
of Arun (availability `None`), Energy From Within (jewel, life→ES conversion). Phasing
probe found a 43-stat conditional family (below) → **Build D**.

**S5** draw seed 159320453889882 — Bloodbond (Blood Offering = one skill's internal
sacrifice→regen/damage split; no external axis), Replica Stampede
(`movement_speed_is_%_of_base` — fixed-rate mechanic, nothing to scale), Kaom's Sign
(on-kill endurance gen, single thin consumer family). **Dead.**

**S6** draw seed 198189613627339 — Redbeak (flat starter), Kalandra's Touch
(`stat:local_ring_duplicate_other_ring` — single unlinked meta-stat, no consumer layer;
same unmodeled-meta-mechanic shape as Headhunter's buff-steal in run 1), Replica
Duskdawn (**unbound**). **Dead.**

**S7** draw seed 182294255842705 — Uzaza's Valley (flat dex/ES/life ring), Prismatic
Eclipse (socket-conditional package: per-green/red/blue/white-socket stats — a fixed
setup bonus, not a scalable X), Replica Conqueror's Efficiency (unavailable). **Dead.**

**S8** draw seed 39007402103982 — Mantra of Flames (unavailable), Rotting Legion
(unavailable), Lioneye's Remorse (defensive shield; mutated life→armour converter but no
axis engine in the draw). **Dead** (recorded as insufficient, not explored further).

**S9** draw seed 179279547481794 — **The Hallowed Monarch** (link-skill minion
mechanics: steal-rare-mods on kill, links grant less damage taken — both bind to
`mechanic:minion` via `stat_mechanic_relation` but have no deeper consumer layer; PoE2
link mechanics are shallow islands in the KB), The Goddess Unleashed (availability
`None`), Meginord's Girdle (flat str/flask filler). **Dead.**

**S10** draw seed 253969826559740 — Cowl of the Ceraunophile (res-override, single
mechanic), Ahn's Heritage (str jewel), **Fidelitas' Spike** (Herald of Thunder buff
effect + shock + Blood Magic). Herald probe found per-herald consumer fan-out (below)
→ **Build E**.

**S11** draw seed 225136986956152 — **Shade of Solaris** (crits deal no damage; spell
damage if crit recently), Kaom's Command (warcry corpse explosion — single stat, no
fan-out), Coiling Whisper (hexes, thin). "Crit recently" probe found a 49-stat
conditional family (below) → **Build F**.

**S12** draw seed 26624285502121 — Limbsplit (Gore Shockwave trigger gated at 150
strength), Firesong (self-ignite jewel), Astramentis (all attributes). Attribute
stacking is a **repeat encounter** of run-1 Build C (Pillar of the Chieftain /
`mechanic:attribute` with 40+ consumers already mapped). New detail recorded:
strength-**gated** trigger (`TriggerGoreShockwaveOnMeleeHitWith150Strength`). Not
recommitted — would be a shallow recombination. **Rejected.**

**S13** draw seed 8098289110042 — **Lightpoacher** (spirit charges → phys-as-each-
element per charge; 15-stat family, single converter, single carrier — thin), Eclipse
Solaris (fire damage from light radius), The Red Trail (bleeding-gated frenzy +
stationary-gated endurance gens). Light-radius probe found a true multi-consumer axis
(below) → **Build G**.

**S14** draw seed 8098289110042 — Lightbane Raiment (phys→chaos + desecrated-ground-on-
block; chaos-aura consumer side **absent** from KB — only the conversion stat + a
display stat exist), Nadir Mode (crit per intensity + spells lose intensity),
Grand Spectrum (repeat, 2nd occurrence). Intensity probe found a real family (below) →
**Build H**.

**S15** draw seed 111409040654026 — Reclaimed Malevolence (jewel, **unbound**), The
Sundered Will (chaos-damage-mods→chaos-aura-effect conversion at % value — but the KB
holds no chaos-aura skill or consumer family; dead end), Perepiteia (stat stick +
lightning-aegis trigger, no axis). **Dead.**

## Discovered builds

### Build A — Animate Weapon / Animate Guardian compound  ✅ VALID (asc established)
Seed path: S1 (Jorrhast's Blacksteel `unique:424`).

Scaling axis **X = number of animated weapons**. Graph evidence:

- Generator: Jorrhast's Blacksteel — triggered Animate Weapon
  (`TriggeredAnimateWeaponUnique`), +copies (`stat:animate_weapon_number_of_additional_
  copies`), minion damage if you hit enemy.
- **Consumer A (swarm):** the animated weapons themselves (minion engine,
  `mechanic:minion` via smr from the copies stat).
- **Consumer B (hypercarry):** `stat:animate_guardian_damage_+%_per_animated_weapon`
  — X is literally the stat's operand. Carried by **two independent sources**:
  `Chains of Command` (`mod:AnimatedGuardianDamagePerAnimatedWeaponUnique__1__`) and
  the Hierophant notable **Marionettes** (`passive:AscendancyCustomHeirophant12`).
  This is the `X → A, X → B` plus `A + B → more` shape: swarm kills trigger AG's
  weapon (`AnimateGuardianWeaponOnAnimatedWeaponKillUnique__1` on Chains of Command) —
  B's engine is fed by A's output.
- Defensive tie-in: `defences_from_animated_guardians_items_apply_to_animated_weapon`
  (Marionettes) — AG's equipment defends the swarm.
- Constraint noted: Chains of Command's `CannnotHaveNonAnimatedMinionsUnique__1`
  (no non-animated minions) — fine here, all minions are animated.

Components committed (all VALID additions, final `validate_build` **valid**,
availability valid): Jorrhast's Blacksteel (generator/enabler), Chains of Command
(consumer B + kill-feedback), Marionettes (generator + converter, ascendancy
**Hierophant**, validated). Gem groups validated via `can_support`: Animate Weapon ←
Minion Damage/Elemental Army (valid), Animate Guardian ← Minion Damage/Elemental Army
(valid). Classification: no slot fillers — every component is graph-bound to X.

**Scaling class: compound** (X→A, X→B, A's kills feed B's trigger).

### Build B — Mana-spent-recently axis  ✅ VALID (asc established, partial)
Draw S2 (Kitava's Thirst was the seed; axis found by probing its trigger stat).

Scaling axis **X = mana spent recently**. KB fan-out (multi-consumer, verified):
`spell_damage_+%_per_200_mana_spent_recently` (**Indigon**, helmet),
`damage_+%_per_200_mana_spent_recently` (no carrier), `gain_x_rage_per_200_mana_spent`
(**Ravenous Passion** helmet + Deadeye notable **"wait a little"**,
`passive:AscendancyCustomDeadeye12`), `gain_onslaught_on_200_mana_spent` (map-mod tier
only), `arcane_surge_effect_+%_per_200_mana_spent...`, `curse_effect_+%_if_200_mana_
spent_recently` (no carrier), `cast_socketed_spells_on_X_mana_spent` (Kitava's Thirst
trigger), and Indigon's own `mana_cost_+%_per_200_mana_spent_recently` — a feedback
amplifier (spending raises cost, raising spending).

Committed: Indigon + Deadeye "wait a little" — final `validate_build` **valid**.
**Honest limitation found by the validator:** Ravenous Passion is also a helmet —
`validate_addition` rejected it (head capacity 1), and Kitava's Thirst is a helmet too,
so the trigger consumer and the rage item cannot coexist with Indigon. Rage's KB
consumers are attack-side (`attack_speed_+%_from_rage`, added phys per rage) while
Indigon's consumer is spell-side — the two outputs do not interact. Recorded as
**multi-use, not compound**; the richer composition was broken by the helmet slot, not
by choice.

### Build C — Minimum charges → absorption charges (defense)  ✅ VALID (asc established)
Draw S3 (Grand Spectrum was the seed).

Scaling axis **X = minimum charge modifiers**. Graph structure:

- Generators: Grand Spectrum (`minimum_power_charges_per_stackable_unique_jewel`),
  Ralakesh's Impatience (boots), passives incl. **Devout of Ralakesh** (Guardian
  notable: min endurance + min frenzy + min power + corrupted-blood immunity).
- Consumer A: `aura_effect_+%_while_at_minimum_power_charges` (Discipline /
  Vaal Discipline gems) — active only when min = max.
- Converter: **Graven's Secret** (amulet) — `modifiers_to_minimum_power_charges_instead_
  apply_to_absorption_charges`; consumer: `elemental_damage_taken_goes_to_energy_
  shield_over_4_seconds_%_per_absorption_charge` (defense).
- **Exclusivity catch (graph-supported):** the converter routes X *instead of* power
  charges, so consumer A dies when the converter is on. Any single build uses one
  branch; the axis is multi-use at the graph level, single-use per build.

Committed: Graven's Secret + Ralakesh's Impatience + Devout of Ralakesh (Guardian,
validated) — final **valid**, availability valid. Grand Spectrum: jewel, no slot model
→ **not assumed**, documented as the optional per-jewel generator. Scaling class:
**multi-use** (defense consumer + charge-permanence outputs; no A+B→C evidence).

### Build D — Phasing state-uptime  ✅ VALID (asc unresolved)
Draw S4 (Replica Voidwalker was the seed).

State axis **X = phasing uptime**: ≥8 generator stats (gain phasing on kill / on hit /
while hasted / at max frenzy / after dash / on ES-recharge begin / if blocked recently)
and a 43-stat "while phasing" consumer family spanning offense
(`nearby_enemies_all_exposure_%_while_phasing`, Replica Voidwalker's own projectiles-
chain-while-phasing), defense (`avoid_%_while_phasing`), and utility (speed, rarity).

Committed: Replica Voidwalker (boots) — final **valid**. Honest classification: the
axis is genuinely multi-consumer **at stat level**, but only one unique carrier was
drawn/found this run; the build is one unique enabler + stat-level consumers.
Ascendancy: `stat:raider_phasing_aura_...` hints at Raider, but **no ascendancy passive
grants any phasing stat in the KB** (verified by scanning all `passive_grants_stat`
edges) — recorded as unmodeled, not forced.

### Build E — Herald swarm + HoT shock feedback  ✅ VALID (asc unresolved)
Draw S10 (Fidelitas' Spike was the seed).

Structure: X = active heralds / herald buff effect.
- Generators: multiple Herald gems (Thunder/Ash/Agony/Purity — all `CreatesMinion`,
  supportable; validated).
- Consumer B (defense): `avoid_stun_35%_per_active_herald` — **carrier-less** in the KB
  (the mod exists but no unique carries it; recorded as graph-only).
- Consumer C (buff power): `aura_effect_on_self_from_skills_+%_per_herald_effecting_
  you`.
- Feedback: Fidelitas' Spike grants shock chance + HoT buff effect; **Storm Secret**
  (amulet) carries `create_herald_of_thunder_storm_on_shocking_enemy` — herald damage →
  shock → extra HoT storms. A + B interact: herald output feeds the trigger engine.

Committed: Fidelitas' Spike + Storm Secret + 3 herald gem groups — final **valid**,
availability valid. Ascendancy: **unresolved** — `Farewell to Flesh`
(`passive:AlternateAscendancyLycia3_`, herald-buff-effect-per-mana-reserved) is
**unclassifiable** by the validator ("ascendancy/flags unclassifiable in KB — never
guessed"); committing it makes the final state INVALID, so it was dropped and the build
committed with zero passives (ascendancy not established — not forced). Scaling class:
**compound** (X→A damage, A's shock→C storms, X→B/C per-herald buffs), with the caveat
that B's carrier is missing.

### Build F — Crit-recently state (no-damage crits)  ✅ VALID (asc unresolved)
Draw S11 (Shade of Solaris was the seed).

State axis **X = crit-recently uptime**, made *free* by Shade of Solaris (wand: crits
deal no damage, spell damage if crit recently). Verified fan-out: 49 `crit_recently`
stat ids incl. `attack_speed/cast_speed_+%_if_have_crit_recently`
(**Unyielding Flame**, shield), `gain_perfect_agony_if_you_have_crit_recently`
(**Replica Atziri's Acuity**, gloves), `gain_vaal_pact_if_you_have_crit_recently`
(Atziri's Acuity, non-replica), `additional_block_%_...`, `area_of_effect_+%_...`,
added-phys pairs, and trigger: `CommandmentOfInfernoOnCrit` on Unyielding Flame
(crit → meteor, costless under no-damage crits).

Committed: Shade of Solaris + Replica Atziri's Acuity + Unyielding Flame — final
**valid**, availability valid. Consumers span offense (spell dmg, speed, meteors),
defense (block, Perfect Agony), keystones. Uncertainty (semantic, not checked by the
validator): the KB does not model whether no-damage crits still increment the
crit-recently state. Ascendancy: **no ascendancy passive in the KB grants any crit
stat** (programmatic scan) — unresolved, not forced. Scaling class: **multi-use**
(offense + defense + trigger), no compound link found between the consumers beyond
sharing the state.

### Build G — Light radius as a scaling stat  ✅ VALID (asc unresolved)
Draw S13 (Eclipse Solaris was the seed).

This is the run's clearest **compound** find after A. Axis **X = light radius**:

- Generator: **Incandescent Heart** (body) carries `stat:light_radius_scales_with_
  energy_shield` (Arcane Vision) — ES investment *generates* X — plus a mutated
  light→accuracy converter.
- Consumers, each with a distinct carrier:
  - fire damage per 1% light radius (min+max, attack) — **Eclipse Solaris** (wand,
    also crit vs blinded);
  - light-radius increases apply to **damage** — **Wreath of Phrecia** (amulet);
  - light-radius increases apply to **AoE** — Wreath of Phrecia + Blinding Aura gem;
  - light-radius increases apply to **accuracy** — Wreath of Phrecia family /
    Incandescent Heart (mutated).
  - `light_radius_+%_while_phased` — cross-link to Build D's phasing axis (recorded,
    not used).

Committed: Eclipse Solaris + Wreath of Phrecia + Incandescent Heart + Blinding Aura gem
— final **valid**. **Live availability catch:** first assembly used **Corona Solaris**
(amulet; blind engine + light→accuracy + fire/crit vs blinded) — `validate_addition`
rejected it: *"no longer obtainable"*. Rebuilt around Wreath of Phrecia. Ascendancy: no
asc passive grants light_radius/blind/ES stats (scan) — unresolved, not forced.
Scaling class: **compound** (Y=ES → X=light → {fire, accuracy, AoE, damage} + blind →
crit consumers).

### Build H — Intensity / overloaded intensity  ✅ VALID (asc unresolved)
Draw S14 (Nadir Mode was the seed).

Axis **X = intensity** (gained by repeating the same skill — `gem:CracklingLance` is
the only `GainsIntensity` gem in the KB):
- consumers: `disintegrate_damage_+%_final_per_intensity` (gem-inherent),
  `critical_strike_chance_+%_per_intensity`, `additional_projectiles_per_intensity`
  (carrier unbound), `area_of_effect`/damage conversions;
- two-stage conversion: losing 6 intensity → `gain_overloaded_intensity_for_x_ms`
  → `critical_strike_multiplier_+_per_overloaded_intensity` — Nadir Mode
  ("spells lose intensity" + crit per intensity) is the inversion enabler that feeds
  the loss→overloaded pipeline.

Committed: Crackling Lance + Overloaded Intensity Support (`can_support` valid —
support requires `GainsIntensity`, excludes Channel etc.) + **Twyzel** (wand) — Twyzel
is an **explicitly declared slot filler**: it exists only so the gem group's weapon
context is determined (validator: "weapon context not uniquely determined: 0 weapon-
class items equipped; weapon_check skipped" → UNKNOWN). A rare wand would serve the
same role in practice; per the skill, the Unique is marked, not glorified. Nadir Mode
is a jewel → **not assumed** (no slot model), documented. Scaling class: **multi-use**
with a two-stage conversion (X→overloaded→crit multi); jewel-side components remain
unvalidated.

## Unavailable-content encounters (this run)

| Content | Where | Handling |
|---|---|---|
| Corrupted Energy, Warrior's Tale, Replica Conqueror's Efficiency, Mantra of Flames, Rotting Legion | seed draws | skipped at seed time |
| **Corona Solaris** | Build G first assembly | **live `validate_addition` catch** — replaced by Wreath of Phrecia |
| The Beachhead / The Goddess Unleashed / Pillars of Arun (availability `None`) | S3, S9, S4 | treated as not gear / not build components |
| Farewell to Flesh (AlternateAscendancyLycia3) | Build E | validator unclassifiable → cannot commit → dropped (ascendancy left unresolved) |

Unbound uniques (zero KB modifier edges — extraction/coverage gap, recorded): Replica
Badge of the Brotherhood, Replica Duskdawn, Reclaimed Malevolence.

## Convergence with previous runs

- The run-2 pattern "item ↔ ascendancy shared-stat convergence" recurred once (Build A:
  Jorrhast's Blacksteel and Marionettes share
  `animate_weapon_number_of_additional_copies`) but was not the dominant pattern this
  time; this run's dominant pattern was **shared consumer stats across multiple items**
  (A: 2 carriers of the per-animated-weapon operand; G: 3 carriers of light-radius
  converters; F: 3 carriers of crit-recently conditionals).
- Attribute stacking (run-1 Build C) was re-encountered (Astramentis + Limbsplit) and
  deliberately **not recommitted** — avoiding shallow recombination was an explicit
  goal.
- Validator catches this run: 1 head-capacity rejection (Ravenous Passion vs Indigon),
  1 live availability rejection (Corona Solaris), 1 unclassifiable-passive rejection
  (Farewell to Flesh), jewel no-slot-model UNKNOWNs (Grand Spectrum, Nadir Mode, Energy
  From Within, Ahn's Heritage — never assumed), 1 weapon-context UNKNOWN resolved by
  equipping a declared slot-filler weapon.

## Final analysis

1. **Coherent build candidates:** 8 of 15 draws (S1, S2, S3, S4, S10, S11, S13, S14)
   produced committed candidates; 7 draws (S5–S9, S15 + rejected S12) were dead ends,
   each with a recorded reason (unbound, availability `None`, unmodeled meta-mechanics,
   single-skill internal loops, absent consumer families).
2. **Validated ascendancies:** 3 of 8 (A: Hierophant/Marionettes, B: Deadeye/"wait a
   little", C: Guardian/Devout of Ralakesh). E's candidate (Farewell to Flesh, Lycia
   alternate ascendancy) is unclassifiable by the validator and was dropped rather than
   assumed. D, F, G, H: no ascendancy passive in the KB binds to their stat families
   (programmatically verified for crit/ES/light/herald) — unresolved, never forced.
3. **Genuine multi-consumer scaling:** 8 of 8 committed builds carry ≥2 graph-supported
   consumers for their axis at stat level; at carrier level: A, C, E, F, G have
   distinct item/passive/gem carriers for ≥2 consumers; D and H are multi-consumer only
   at stat level (missing/dangling carriers, unassumed jewel).
4. **Compound/interacting scaling:** 3 clear (A: animated-weapon kills feed AG-weapon
   triggers, X is the operand of a second stat; E: herald damage → shock → extra HoT
   storms; G: ES → light radius → four converter-routed outputs + blind→crit) plus 2
   partial (C: converter-mediated defense routing with an exclusivity constraint; H:
   two-stage intensity→overloaded→crit-multi). Not forced — B, D, F are recorded as
   multi-use without compound evidence.
5. **Essentially shallow recombinations:** 1 of 8 (B — the richer mana-spent
   composition was broken by the head-slot conflict, leaving a spell-damage + off-class
   rage pair; honest but not deep). The S12 attribute-stack re-encounter was rejected
   as a recombination rather than committed.
6. **Slot fillers:** exactly one — Twyzel in Build H (declared, weapon-context
   determination; a rare wand would serve). All other committed uniques have
   graph-supported roles; unavailable/irrelevant draws were rejected rather than used
   to fill slots.
7. **Exploration behavior:** thin branches (S5–S9, S15) were stopped after 1–3 probes
   with recorded reasons; promising branches were followed to *carrier level* (which
   specific item/passive/gem carries each consumer stat) — that is what turned
   "mana-spent", "light radius", "crit recently", and "herald" from stat families into
   builds, and what exposed the missing carriers (stun-avoidance-per-herald, chaos
   aura) and the Corona Solaris unavailability. No branch was abandoned while an
   unexplored interaction was visible; the agenda held one parked item at a time
   (Wreath of Phrecia as the Corona Solaris replacement) and it resolved.
8. **Richer than previous runs?** Yes, with caveats. Runs 1–2 mostly produced single-
   consumer axes plus one shared-stat item↔ascendancy link. This run produced three
   genuinely compound architectures: A (X is the *operand* of another build's stat,
   with a kill-trigger bridge between the two consumers), G (a generator→stat→four-
   consumer fan-out where the generator is itself a conversion from a different pool),
   and E (an output of one mechanic closes a feedback loop into the same mechanic).
   That said, 5 of 8 builds still have no established ascendancy, and several real
   consumer stats have no carriers in the KB — the depth is graph-real but only
   partially item-realizable.
9. **Strongest remaining limitation:** ascendancy metadata binds to very few stat
   families — a programmatic scan shows **no ascendancy passive grants any crit, ES,
   light-radius, or herald stat** — so ascendancy resolution fails structurally
   (3/8 established, 1 unclassifiable alternate) outside the charge/minion/block
   families that earlier runs found. Second-order gaps that materially shaped this
   run: jewels have no slot model (three enablers left not-assumed), two of 15 seed
   uniques and one key consumer item are unbound, and one converter family (chaos
   aura) exists without its consumer side.

## Uncertainties carried forward

- Shade of Solaris: whether no-damage crits still count for "crit recently" states —
  not modeled by the validator/KB (semantic gap, flagged, not assumed).
- Herald per-herald consumers (`avoid_stun_35%_per_active_herald`,
  `aura_effect_..._per_herald`) lack carriers — architecture is graph-supported but
  itemless beyond the trigger/buff-effect items.
- Alternate-ascendancy payloads (Lycia) are present in the KB but unclassifiable by
  the validator — Build E's best ascendancy candidate is unusable, not merely absent.
- Intensity inversion (Nadir Mode) rests on the jewel being buildable at all (no slot
  model) — the two-stage overload conversion is graph-evidenced, the jewel is not
  validated.
