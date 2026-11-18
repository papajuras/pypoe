# Phase 5 — Step 0: Final Review (requirements / representability)

Machine-readable test spec: `docs/phase5_test_cases.json` (12 cases, unchanged).
This document is the concise requirements review. It answers only:
1. WHAT relationships must the future graph discover?
2. CAN those relationships be represented from existing Phase 4 data without semantic inference?
3. What are the genuine data gaps or limitations?

No implementation. No Phase 5 architecture, edge types, SQL, regexes, or traversal design.

---

## Purpose

Specify the structural chains the future relationship graph must be able to discover and traverse, so that an LLM exploring PoE mechanics can reach the relevant nodes through deterministic, source-backed links. Every relationship below must be derived from Phase 4 nodes/payloads (or reported as a gap) — never from semantic guesswork.

---

## Test cases (kept in full, incl. the adversarial case)

| id | chain | kind | classification |
|---|---|---|---|
| `T_exemplars` | node existence (Iron Will, Avatar of Fire, Crown, ignite/ignited, Strength, Intelligence, Hopeshredder, Whispers, Unholy Trinity) | green | representable |
| `T4_unique_rare_shared_stat` | Unique ↔ rare via shared stat (`physical_damage_%_to_add_as_fire`) | green | representable |
| `T1_firemin_firemax_shared` | FireMin ↔ FireMax on a rare modifier (`AddedFireDamagePerStrengthInfluence1`) | green | representable |
| `T2_per_charge_mods` | per-endurance-charge FireMin/FireMax on a rare modifier | green | representable |
| `T_ut_types` | Unholy Trinity ↔ Lightning/Physical/Chaos (gem tags + resonance stats) | green | representable |
| `T_int_grant_stat` | `maximum_mana_+_per_2_intelligence` unique↔rare bridge | green | representable |
| `T_int_lightning_mods` | per-10-intelligence lightning mod (`RecombinatorSpecial…`) | green | representable |
| `T_mana_lightning_anchor` | mana→lightning anchor stat | green | representable |
| `R1_strength_to_fire` | Strength → FireMin/FireMax | red | representable (head) — Phase 5 must provide a deterministic link |
| `R2_endurance_charge_to_fire` | Endurance Charge → FireMin/FireMax | red | **data gap** (head entity) + representable (damage side) |
| `R3_hopeshredder_scaling` | Hopeshredder → verified stat-bearing mods | red | representable, **unvalidated** (resolution candidates only) |
| `R_adv_whispers_chain` | Whispers → mana → Intelligence → Lightning-per-Int → Lightning → Unholy Trinity | red | mixed: representable hops + **data gaps** (inherent grant application, Whispers validation) |

---

## Evidence / representability (per relationship)

**Unique ↔ rare through shared stat** — verified: 1,429 stat ids appear on both a `unique`-gen and a `prefix`/`suffix` mod (e.g. `stat:physical_damage_%_to_add_as_fire` on `mod:AbberathsFuryEnrageStance` [unique] and `mod:ConvertPhysicalToFireInfluenceMaven` [prefix]). Deterministic T1-style join on the stat id. **Representable.**

**FireMin ↔ FireMax ↔ rare mods** (Strength and Endurance-Charge damage sides) — verified: `attack_minimum/maximum_added_fire_damage_per_10_strength` co-occur on `mod:AddedFireDamagePerStrengthInfluence1` (prefix); `minimum/maximum_added_fire_damage_per_endurance_charge` co-occur on `mod:AddedFireDamagePerEnduranceChargeInfluence1` (prefix). The damage side is **representable**.

**Strength → FireMin/FireMax head** — `stat:strength` exists. No mod/passive grants a strength stat **and** a per-strength fire stat, so the only source fact linking them is the **stat-id string itself** (`…per_10_strength`). This is a real, deterministic, source-backed fact (string containment), so the relationship is **representable** — Phase 5 must define a deterministic relationship that connects a Strength node to the per-strength scaling stats. The mechanism is Phase 5's choice; it is not prescribed here.

**Endurance Charge → FireMin/FireMax head** — the per-charge fire stats and rare mods exist, but **no node represents the "Endurance Charge" concept** (no stat, passive, or group). This is a **data gap**: the start entity is absent from the export. Phase 5 cannot create it without a new node type (out of scope); the damage side remains representable.

**Hopeshredder → mechanics** — `unique:739` exists; its vid (`UniqueBow21`) appears in 0 mods keys; resolution is **method-2 text candidates only** (`validated:false`). The candidate mods are plausible (e.g. `AddedColdDamagePerFrenzyChargeUnique__1`) but **unvalidated — they are not facts**. The underlying mods live in `mods.json` (representable in principle), but the unique→mod association must be validated before it becomes a relationship. **Representable, currently unvalidated.**

**Whispers of Infinity → mana → Intelligence → Lightning-per-Int → Lightning → Unholy Trinity**
- `unique:1461` (Whispers) — **unvalidated** (method-2 candidates only; none reference lightning/intelligence). Head is a validation gap, same class as Hopeshredder.
- mana / Int→mana — `stat:base_maximum_mana` and `stat:maximum_mana_+_per_2_intelligence` exist; the latter is a **mod-granted stat** (unique + Necropolis crafting prefix), NOT the inherent grant. The inherent application (Int grants mana) is a **data gap** (accepted limitation — client-side, absent from export).
- Intelligence → Lightning-per-Int → Lightning — `stat:intelligence`, the per-10-intelligence lightning stats, and the plain lightning damage stats all exist. No mod bridges them; the only source fact linking them is the **stat-id string** (`…per_10_intelligence`). **Representable** (Phase 5 deterministic relationship required).
- Lightning → Unholy Trinity — `gem:SupportUnholyTrinity` tags include `lightning`, `physical`, `chaos` (Tag nodes exist) and its per_level carries unholy-resonance stats. **Representable.**

**Unholy Trinity ↔ damage-type tags** — verified: gem tags `[physical, chaos, lightning, dexterity, support]`; Tag nodes `tag:lightning/physical/chaos` exist. **Representable.**

---

## Data gaps / limitations

1. **Inherent attribute→derived-stat grant APPLICATION** (Int→Mana, Str→Melee/Armour, Dex→Accuracy/Evasion): the stat *definitions* exist (`maximum_mana_+_per_2_intelligence`, `bonus_accuracy_rating_+_from_dexterity`, `bonus_damage_+%_from_strength`, plus negations/overrides), but **no record applies them to characters** — the application is client-side and absent from the export. **Data gap (accepted).**
2. **Endurance Charge head entity**: no node represents endurance charges. **Data gap.**
3. **Unique resolution validation**: Hopeshredder and Whispers resolve only via unvalidated method-2 text candidates. They must not be treated as facts until validated. **Validation gap (not a data gap — the mods exist).**
4. Two inherent-rule stats exist only as prefixed/conditional variants, not bare stats (Int→ES per 10, Str→Melee phys per 10).

---

## Adversarial findings

- **No test secretly requires semantic inference**: every assertion is node/payload fact or deterministic string/linkage on source data. The attribute-head relationships are anchored to the real **stat-id string** (a source fact), not to parsed display text.
- **Unvalidated candidates are never facts**: R3/R_adv heads depend on resolution validation; until then they must fail (they are red tests).
- **Red tests do not hardcode**: R_adv requires a genuine multi-hop traversal; its assertions explicitly exclude the quantitative variance hypothesis (that is later reasoning, not a Step 0 requirement).
- **Tests describe desired graph behaviour, not implementation**: assertions are about reachability/presence, not about how Phase 5 computes them.
- **Green tests cannot mask missing edges**: the head-relationships are separate red tests, so a missing structural link cannot hide behind a passing damage-side test.

---

## Final verdict

**READY for Phase 5 architecture.** Step 0 has a complete, source-backed requirements contract:
- representable relationships are explicitly enumerated with verified node/stat evidence;
- genuine gaps are classified (inherent-grant application = data gap, accepted; Endurance-Charge head = data gap; unique resolution = validation gap, not data);
- no test requires unsupported inference; unresolved candidates are kept non-factual.

Phase 5 architecture may proceed using `phase5_test_cases.json` (green = must pass, red = required relationships with the gap classification above) as its requirements specification.
