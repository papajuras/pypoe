# Phase 4B — Unresolved Uniques: looser-match check

Question from the taxonomy review: the ~967 uniques with **no** `mods.json`
record whose key contains `visual_identity.id` were labelled "unresolved".
Are their effects genuinely absent from structured data (flavour-only), or
is the `visual_identity.id` substring heuristic just too narrow?

Source: `cache/raw_records.db` only. Method: for each unresolved unique,
take its PoB display-text block (`pob/Uniques/*.json`), strip structural
lines and `{tags:…}` / `{variant:N}` markers, then match each normalized
effect line against normalized `mods.json` / `ModItemExclusive` `text`
fields (substring on a 24-char normalized window). This is evidence-based
looser matching — not the vid substring heuristic.

## 10-item spot check (verbatim evidence)

| unique | class | looser-match result | resolving `mods.json` record(s) |
|---|---|---|---|
| Ungil's Harmony | Amulet | FOUND | `StunRecoveryUniqueAmulet18` (alt-art vid `AlternateArtUniqueUngilsHarmony`; mod key is semantic) |
| Screams of the Desiccated | Belt | FOUND (shared effect) | `SoulcordAccelerationShrineUnique__1` — its shrine-buff effect text is a shared mod |
| Replica Soul Tether | Belt | FOUND (base-shared) | `KeystoneSoulTetherUnique__1/2`; replica (`…21x`) shares the base's (`…21`) mod key space |
| Replica Hyrri's Ire | Body | FOUND (base-shared) | `ChanceToSuppressSpellsUniqueBodyDex1`, `LocalIncreasedEvasionRatingPercentUniqueBodyDex1` |
| The Apostate | Body | FOUND | `LifeFromEnergyShieldArmourUnique__1` (+ `Divergent…PercentUnique__1`) |
| Cold Iron Point | Dagger | FOUND | `GlobalPhysicalSpellGemsLevelUnique__1` |
| Vorana's Preparation | Flask | FOUND | `FlaskDebilitateNearbyEnemiesWhenEffectEndsUnique_1` |
| Natural Affinity | Jewel | FOUND (indirect) | effect "Adds Nature's Patience" → passive node key `JewelExpansionNaturesPatience` (not a mod) |
| The Golden Rule | Jewel | FOUND | `ReflectBleedingToSelfUnique__1`, `IncreasedArmourWhileBleedingUnique__1`, `ChaosResistancePerPoisonOnSelfUnique__1` |
| Fated End | Ring | FOUND | `HexExpiresMaxDoomUnique__1` |

The mods exist; their keys are **semantic names** (`ReflectBleedingToSelfUnique__1`,
`LifeFromEnergyShieldArmourUnique__1`) that rarely embed the visual id.

## Full-set sweep (all 967 unresolved)

| outcome | count | notes |
|---|---|---|
| **FOUND via effect-text match** | **880** | 91% — effects present in `mods.json`/`ModItemExclusive` text under semantic keys |
| NOT-FOUND (no matching effect text) | 3 | Tabula Rasa, Thrillsteel, String of Servitude — see below |
| No PoB display text to match | 84 | classes without PoB text blocks (Map, Watchstone, HeistContract, …) — unmatched, not "absent" |

Machine-readable per-item evidence: `docs/phase4b_sweep.json` (found entries
carry the matching phrase + resolving mod keys).

### The 3 NOT-FOUND residuals — genuine, and structural not flavour-only
- **Tabula Rasa** (Body): PoB text is only `Sockets: W-W-W-W-W-W`. Its
  "all linked" mechanic is a **socket configuration**, not a mods.json stat.
  Effect exists structurally (socket system), not as a mod.
- **Thrillsteel** (Helmet): PoB text is only `Onslaught`. The effect is a
  bare buff grant; no unique-keyed mod in mods.json.
- **String of Servitude** (Belt): manual match found
  `ImplicitModifierMagnitudeUnique_2` (the Incursion implicit-magnitude
  mechanic is a shared mod); the sweep's window missed it — not absent.

## Verdict

**The "unresolved" set is ~91% a heuristic artifact, not missing data.**
The flavour-only hypothesis is effectively **NOT CONFIRMED**: nearly every
vid-unresolved unique has its effects represented in `mods.json` text under
semantic (non-vid) keys. True absences are limited to retired content and a
couple of structural/display-only mechanics (sockets, bare buff grants).

## Action for the taxonomy (4B/4C)

The UniqueItem → Modifier resolver must be upgraded from
`visual_identity.id` substring to:
1. **normalized effect-text matching** (primary; covers semantic-key mods),
2. **base-vid fallback** for replicas (replica keys share the base's mods),
3. **passive-grant resolution** (jewels like Natural Affinity →
   `JewelExpansion…` node keys),
4. keep the vid-substring match as a fast path.
"empty `resolved_mods`" must then be split into *genuinely absent (retired /
structural)* vs *unresolved-by-heuristic*, with the sweep numbers (880/3/84)
as the coverage baseline.
