# Build 030 — Farrul's Cat-Aspect Crit → Blind Loop

**Status: VALIDATED** (passed all checks implemented by `phase7_build_validity` — slot occupancy, availability, ascendancy composition; NOT a full PoE build-validity claim)

Central interaction: critical strikes while Cat's Stealth is active blind enemies, and hits against blinded enemies deal increased damage — so critical strike chance feeds hit damage both directly (crits) and indirectly (blind uptime), while the cat-aspect item family raises charge counts and stealth uptime.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Helmet | **Farrul's Bite** [available] | carries: `AdditionalCriticalStrikeChanceWithCatAspectUnique__1` · **`CritsBlindChanceWithCatsStealthUnique__1`** · **`DamageAgainstBlindedEnemiesUnique__1`** → `stat:hit_and_ailment_damage_+%_vs_blinded_enemies` · `DivergentGrantsCatAspect1` · `ColdResistUnique__25` · `LocalIncreasedEvasionAndEnergyShieldUnique__12` |
| Body Armour | Farrul's Fur [available] | carries: `CatsStealthDurationUnique__1_` · `DivergentCatAspectReservesNoManaUnique__1___` · **`GainMaxFrenzyAndPowerOnCatsStealthUnique__1`** · `GainPhasingWhileCatsStealthUnique__1` · `MutatedUniqueBodyStrDex8AttackDamage` |
| Gloves | Farrul's Pounce [available] | carries: `DamageAgainstBleedingEnemiesUnique__1` · `DivergentAttacksBleedOnHitWithCatsStealthUnique__1_` · `GainCrimsonDanceWithCatsStealthUnique__1` · `LocalIncreasedArmourAndEvasionUnique__8_` |
| Boots | Farrul's Chase [available] | carries: `ChanceToAvoidBleedingUnique__1` · `DivergentCatsStealthTriggeredIntimidatingCry` · `MovementSpeedWithCatsStealthUnique__1` · `LocalIncreasedEvasionRatingPercentUnique__13` |
| Passive | Critical Strike Chance and Multiplier (AscendancyAssassin5, Assassin) | grants: `stat:base_critical_strike_multiplier_+`, `stat:critical_strike_chance_+%` |
| Passive | Critical Strike Chance, Elusive Effect (AscendancyAssassin13, Assassin) | grants: `stat:critical_strike_chance_+%`, `stat:elusive_effect_+%` |

**Ascendancy:** Assassin (notables: Critical Strike Chance and Multiplier; Critical Strike Chance, Elusive Effect)

Note: the Research API exposes modifier/stat identifiers, not display text; the lists above are the exact ids returned by the API, unmodified.

## Why it works

Cat's Stealth (upheld by Fur's stealth-duration and Chase's stealth trigger) is the uptime engine: while active, Bite makes crits blind and boosts damage vs blinded, and Fur grants maximum frenzy and power charges. Critical strike chance (Assassin notables) feeds damage through two paths: direct crit multiplier, and blind application that enables the vs-blinded damage multiplier. Pounce adds a parallel bleed-on-hit-with-stealth path with its own vs-bleeding damage bonus.

## Scaling claim

**Quadratic hypothesis (not confirmed):** X = critical strike chance → path A: crit damage; path B: blind uptime (crits blind during stealth) → `hit_and_ailment_damage_+%_vs_blinded_enemies`. The KB evidences both paths and their carrier mods but does not quantify blind uptime as a function of crit chance, so the X² interpretation stays a hypothesis.

## Evidence

- `unique:764` → `mod:CritsBlindChanceWithCatsStealthUnique__1` (uma)
- `mod:DamageAgainstBlindedEnemiesUnique__1` → `stat:hit_and_ailment_damage_+%_vs_blinded_enemies`
- `unique:763` → `mod:GainMaxFrenzyAndPowerOnCatsStealthUnique__1`, `mod:CatsStealthDurationUnique__1_`
- `unique:765` → `mod:DivergentAttacksBleedOnHitWithCatsStealthUnique__1_`, `mod:GainCrimsonDanceWithCatsStealthUnique__1`

## Validation

All 6 additions passed `validate_addition`; final `validate_build` (final=True): **valid** — availability all available, single ascendancy class `Assassin`.
