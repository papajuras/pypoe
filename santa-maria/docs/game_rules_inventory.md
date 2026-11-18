# Intrinsic game rules in the KB (Phase 5R)

Status: implemented 2026-09-19. Projector: `tools/phase5r_rules.py` (pipeline
step 11, idempotent). Tests: `tools/tests/test_rules.py`. API surface:
`rule_applies_to` / `rule_negated_by` / `rule_modified_by` edge types +
`Rule` node type, surfaced through the standard `carriers()`/`neighbour`
envelope (see `discovery-api-usage` skill).

## Semantics

Every rule below is a **default engine rule**, extracted from source as a
first-class `rule:` fact. It is never inferred from the existence of a RePoE
exception stat. Exceptions are separate facts, bound only where the PoB code
that consults the exception flag sits inside the rule's code region (code
containment), with a PoB-flag ↔ GGG-stat-id name correspondence that is
resolve-verified against `nodes.db` at build time.

| Edge | Meaning |
| --- | --- |
| `rule_applies_to` | rule → stat/tag: generic applicability target |
| `rule_negated_by` | rule → stat: exception **prevents** the default |
| `rule_modified_by` | rule → stat: exception **changes a parameter** |

Numeric attribute→resource conversions additionally remain canonical as
`attribute_grants_stat` edges (phase 5.6, golden tests
`test_attribute_grants.py`, `test_strength_arcane_chain.py`); each conversion
also has a `rule:` node as the semantic home for its exceptions. Both views
derive from the same artifact and are cross-checked by `phase5r --verify`.

Attribute quantity nodes: the engine totals the attribute from its sources,
which the KB represents as separate stats (`stat:base_<attr>` granted by tree
passives named after the attribute, `stat:additional_<attr>` granted by
"+X to <attribute>" item mods per RePoE translation) that aggregate into the
`stat:<attr>` operand. That aggregation is engine-internal and unrepresented,
so each conversion rule binds `applies_to` to the canonical operand AND the
two verified quantity nodes — probing any of them surfaces the rule.

## Rules (8)

Attribute conversions — source: `tools/sources/pob_attribute_mechanics.json`
(audited, pinned to PoB commit `ed354c2f8c42e148bc904c7508dbe851fb2cf952`,
`CalcPerform.lua` "Add attribute bonuses"):

| rule | formula | applies_to | negated_by |
| --- | --- | --- | --- |
| `rule:strength_life` | floor(Strength/2) Life | stat:strength, stat:base_maximum_life | gain_no_inherent_bonus_from_strength, gain_no_maximum_life_from_strength |
| `rule:strength_melee_physical_damage` | floor(Strength/5)% | stat:strength, stat:melee_physical_damage_% | gain_no_inherent_bonus_from_strength |
| `rule:dexterity_accuracy` | Dexterity × AccuracyPerDexBase (=2) | stat:dexterity, stat:accuracy_rating | gain_no_inherent_bonus_from_dexterity |
| `rule:dexterity_evasion` | floor(Dexterity/5)% | stat:dexterity, stat:evasion_rating_% | gain_no_inherent_bonus_from_dexterity, gain_no_inherent_evasion_rating_%_from_dexterity |
| `rule:intelligence_mana` | floor(Intelligence/2) Mana | stat:intelligence, stat:base_maximum_mana | gain_no_inherent_bonus_from_intelligence, gain_no_maximum_mana_from_intelligence |
| `rule:intelligence_energy_shield` | floor(Intelligence/10)% | stat:intelligence, stat:maximum_energy_shield_% | gain_no_inherent_bonus_from_intelligence |

Engine rules — source: PoB main-branch Lua, commit recorded at download time
in `data/manifest.json → _meta.sources.poblua.commit` (main HEAD at build;
re-download re-pins). PoB's default branch is `dev` (active development);
the pinned branch is `master` — the same convention as the other two manifest
sources (repoe-fork, pob-data).

| rule | value | source (anchors, re-verified by regex each build) |
| --- | --- | --- |
| `rule:chaos_damage_bypasses_energy_shield` | ES bypass +100% for Chaos | `pob-src/src/Modules/CalcDefence.lua` "-- Energy Shield bypass" block; `if not modDB:Flag(nil, "ChaosNotBypassEnergyShield")` → `+ 100` |
| `rule:energy_shield_recharge_delay` | 2 s, ÷ (1 + faster-start INC/100) | `pob-src/src/Modules/Data.lua` `EnergyShieldRechargeDelay = 2` + `CalcDefence.lua` delay formula line |

Exception bindings (engine rules):

| rule | negated_by | binding |
| --- | --- | --- |
| chaos bypass | `stat:chaos_damage_does_not_bypass_energy_shield` | flag `ChaosNotBypassEnergyShield` checked inside the bypass block |

## Unbound exceptions (reported, not guessed)

- `intelligence_energy_shield`: PoB flag `NoIntBonusToES` — no
  name-corresponding KB stat exists.
- `dexterity_accuracy`: override flag `DexAccBonusOverride` — no KB stat.
- Chaos-bypass variants (`..._while_not_low_life`, `..._while_not_low_mana`,
  `minion_...`, local/flask/virtual) — their PoB flag names were not verifiable
  inside the downloaded calc scope; left unbound.
- `energy_shield_recharge_not_delayed_by_damage` — different mechanism
  (dynamic delay on damage taken), not the 2 s start-delay rule.

## Deliberately NOT extracted (fail-fast)

- **"DoT cannot crit" / "DoT is not a hit"** — no mechanical anchor in PoB
  calc code; ailment dot-multipliers explicitly carry crit-conditional
  handling (`CalcOffence.lua`: `CritBleed/CritPoison/CritIgniteDotMulti`,
  `dotCfg.skillCond["CriticalStrike"]`). An absolute rule would be pretraining
  knowledge, not source.
- **Low Life 35% / Low Mana 30%** — engine-internal values. RePoE carries only
  the override stats (`low_life_threshold_%_override`,
  `full_life_threshold_%_override`); PoB's `data.misc.LowPoolThreshold = 0.5`
  (`src/Modules/Data.lua`) is a modeling fallback for EHP pools, not the game
  rule. No numeric rule node is emitted.

## KB vocabulary notes (discovered gaps)

- **`stat:base_intelligence` vs `stat:intelligence`** (same for
  strength/dexterity): the conversion edges and rules anchor at
  `stat:intelligence` (the operand PoB consumes); `stat:base_intelligence` is
  the mod-facing stat granted by 89+ passives. No KB edge links the two node
  pairs; the semantic relationship is unverified in the available sources.
  Agents probing `stat:base_*` should also resolve the plain attribute stat.
- `stat:maximum_mana` exists as a node but nothing edges to it; the canonical
  pool stat (per PoB/GGG mod names, hence per the artifact and its edges) is
  `stat:base_maximum_mana`.
- Per-attribute spell/damage stats use abbreviated ids
  (`spell_damage_+%_per_10_int`, not `..._intelligence`) — keyword sweeps must
  probe both spellings.
- Gem display names ("of Trarthus" league-gem family = `AltX/AltY/AltZ`
  record keys, e.g. `gem:HeavyStrikeAltY` = "Heavy Strike of Trarthus") are
  exposed by phase8 `resolve()` since the `_node_name` consistency fix
  (2026-09-19); gem numeric `%` values remain UNEXPOSED — documented
  coverage gap, separate issue, not fixed here.

## Applies-to bridge mechanics (Phase 5M, default pipeline)

Second scaling-relation family, complementing the `_per_<N>_` →
`stat_scales_with` rule: "increases and reductions to X also apply to Y at Z%
of their value". Representation: `mechanic:applies_to_<id>` nodes +
`stat_mechanic_relation` edges **on both sides** (member/output stat →
mechanic `role=output`; operand/input stat → mechanic `role=input`), surfaced
through the normal `neighbour`/`carriers` envelope (entity-side discovery =
`neighbour` with default filters; `carriers` on the mechanic = reverse member
view). Payload carries prose semantics — name (game wording where
translation-equality bound), description, input family, output, value,
members, pob_flag, provenance (pattern lines + handler code region + commit).

Pipeline: step [10] consumer projection (default), step [11]
`sources/generate_applies_to.py --check` (mechanical ModParser sweep →
committed `tools/sources/applies_to_mechanics.json`, drift-checked) +
`phase5m_applies_to.py` (projection). Tests: `tests/test_applies_to.py`
(includes the input-side discovery acceptance: probing
`stat:maximum_mana_+%` surfaces the "maximum Mana → Damage at 30%" mechanic
without knowing its name or output).

- Class boundary = mechanical flag-identifier regexes over ModParser pattern
  tables (`(Improved)?[A-Za-z]+AppliesTo[A-Za-z]+` +
  `[A-Za-z]*TransfigurationOf[A-Za-z]+` — the second family added when the
  fixtures exposed that the Transfiguration bridges carry their own flag
  names, ModParser:5487-5489).
- Bindings strictly evidence-backed: bridge stats via normalized-translation
  equality or verified flag-token transform (negation-guarded, `virtual_*`
  skipped); operands ONLY via PoB handler operand field (e.g. CalcOffence:511-519
  `Sum("INC", nil, "Mana")`) or the phrase operand segment, each verified
  against an existing KB stat whose translation/ModParser phrase table names
  the family. Unresolvable → unbound, reported (currently:
  `EnergyShieldRechargeAppliesToLife` — no bridge stat family exists).
- 26 mechanic nodes total: 9 audited (`pob_stat_mechanics.json`) + 17
  generated, incl. the three Transfiguration fixtures fully bound
  (operands `maximum_mana/life/energy_shield_+%`, value `data.misc.Transfiguration`
  = 0.3 → 30%) and the Arcane Might bridge (`spell_damage_%` →
  `attack_damage_%`, members incl. the 150% Crown of Eyes variant and Heavy
  Strike of Trarthus' gem-level variant).
- `stat_mechanic_operand` / `stat_mechanic_variant` (phase 5, structural)
  remain untouched supporting data; `stat_mechanic_relation` is the canonical
  LLM-facing relation. Both this projection and phase7C scope their deletes
  to their own namespaces (order-safe).

## Re-extraction

`tools/run_pipeline.sh` steps 10-12 (consumer projection, applies-to
mechanics, intrinsic rules), or individually: `python3
tools/phase5r_rules.py [--report|--verify-only]` and `python3
tools/sources/generate_applies_to.py [--check]` + `python3
tools/phase5m_applies_to.py`. Anchors are regexes over the downloaded Lua; if
PoB main changes the code, re-run `--force-download` (re-pins the commit in
the manifest), the `--check` step fails loudly on artifact drift, and the
projectors re-extract; a vanished anchor fails the build loudly rather than
silently dropping the rule.
