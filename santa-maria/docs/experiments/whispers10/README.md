# Whispers of Infinity — whispers10 (clean slate, API-only)

Run date: 2026-10-06. Seed: `unique:1461` **Whispers of Infinity** (`item_class:Amulet`,
`availability: available`). Skill version: `scaling-discovery` v5, `discovery-api-usage`,
`build-output`. Every claim below was produced by the public Research API
(`santa-maria/tools/research.py` → `phase8_research.resolve` / `carriers`,
`phase6_api.get_neighbour`, `phase7_build_validity.validate_addition` / `validate_build`,
`phase7_build_feasibility.weapon_check`). No previous run was read, reused, or evaluated.
Phrecia alternate ascendancies were excluded by default everywhere;
`meta.excluded_alternate_ascendancies` was checked before every absence claim.

---

## 1. Seed census (verified)

`neighbour unique:1461 --depth 1` → 1 `unique_in_class` + 4 `unique_modifier_association`.
All four modifiers are **sole-carrier** (`carriers(mod)` → `total=1`, the seed itself):

| Modifier text (API `text` field) | stat granted | carriers of the stat |
|---|---|---|
| **(5-10) to (20-25) Added Attack Chaos Damage per 100 Maximum Mana** | `stat:min_attack_added_chaos_damage_per_100_mana` + `stat:max_attack_added_chaos_damage_per_100_mana` | **1 each — the seed's own modifier** |
| **(60-40)% reduced maximum Mana** | `stat:maximum_mana_+%` (negative roll) | 150 (shared family) |
| **(10-15)% faster start of Energy Shield Recharge** | `stat:energy_shield_delay_-%` | 36 (shared family) |
| **Skills Cost Energy Shield instead of Mana or Life** | `stat:base_skills_cost_es_instead_of_mana_life` | **1 — the seed's own modifier** |

Seed tags on the damage modifier: `attack`, `chaos`, `chaos_damage`, `damage`, `mana`,
`resource`.

**Central structural fact.** The seed's damage output is a *flat added* value proportional to
**maximum mana**, and the seed simultaneously *taxes the same axis* by 40–60 % reduced maximum
mana. Any architecture built on this seed must out-buy that reduction. The seed also swaps the
skill-cost resource from mana/life to **energy shield**, which makes mana a **non-consumed**
pool — mana becomes pure damage currency, and it also makes the whole "mana spent" mechanic
family dead (see §7).

---

## 2. Axis, engine edges, and vocabulary harvest

Vocabulary was harvested from the seed stats' own modifier texts and tags (§5 step 1), then
pattern-mined from `resolve --type Stat` over `mana` (792 stats), `energy_shield` (405),
`intelligence` (70), `Chaos` (623). Mined patterns that survived probing:
`per_N_<unit>`, `<unit>_%`, `%_of_maximum_<pool>`, `per_100_<pool>`, `..._to_add_as_<type>`,
`..._to_convert_to_<type>`, `..._scales_with`, `per_<N>_<attribute>`,
`Transformed to apply to`, `per_<N>_mana_spent_recently`.

**Confirmed engine edges (intrinsic rows, `attribute_grants_stat` out of `stat:intelligence`):**

- `stat:intelligence → stat:base_maximum_mana` (Intelligence grants base maximum mana)
- `stat:intelligence → stat:maximum_energy_shield_+%` (Intelligence grants Energy Shield %)

**`stat:maximum_mana` (the pool stat) → `stat_scales_with` consumers — the complete list:**

| consumer stat | carriers |
|---|---|
| `stat:attack_damage_+%_per_500_maximum_mana` | **0** (recorded empty search) |
| `stat:spell_damage_+%_per_500_maximum_mana` | **0** (recorded empty search) |
| `stat:evasion_rating_+%_per_500_maximum_mana` | 2 mods → **Omeyocan** (Boots, available) |
| `stat:bladefall_volley_frequency_+%_per_100_maximum_mana` | 1 gem → **Bladefall of Trarthus** |

**Axis pivot.** Primary axis **X = maximum mana**; generator pivot **intelligence**
(`attribute_grants_stat`). No re-anchoring was needed: mana is both the seed's stated
scaling base (modifier prose) and the pool stat the KB models
(`attribute_grants_stat` → `stat:base_maximum_mana`).

**Recorded KB gap (seed's own scaling edge is unmodelled).**
`neighbour stat:max_attack_added_chaos_damage_per_100_mana --depth 1` returns **zero edges**
— no `stat_scales_with`, no `rule_*`, no `stat_mechanic_*`. The mana → seed-damage link is
evidenced only by the modifier prose ("per 100 Maximum Mana"), `tag:mana`/`tag:resource`, and
the id-family resemblance to the four consumers above. Treated as **confirmed-by-prose,
missing-as-edge**; no DB was consulted to fill it.

---

## 3. Architecture subgraph

Roles per scaling-discovery §9. **CONFIRMED** = live KB edge / explicit prose.
**HYPOTHESIS** = relation the KB does not bind (engine-formula reasoning).
**UNKNOWN** = fail-closed, no evidence either way.

### A1 — Twice-Mana Bridge · X = maximum mana · output = hit chaos damage · **quadratic CANDIDATE**

- `Intelligence → base maximum mana` (CONFIRMED, engine edge)
- `mana% increases → maximum mana` — `Mana and Spell Damage` (minor), `Prodigal Perfection` (notable), `Deep Thoughts` (notable), Hierophant passives, gear mods (CONFIRMED, 150 carriers)
- `maximum mana → Added Attack Chaos Damage` — **seed** (CONFIRMED by prose, edge missing)
- `maximum mana → increased Spell Damage (up to 60 %)` — **Prodigal Perfection** `stat:spell_damage_+%_per_100_maximum_mana_up_to_60%` (CONFIRMED, 1 carrier)
- `spell damage % → attack damage` — **Crown of Eyes** "Attacks have 150% Arcane Might" (CONFIRMED mod→stat) + **Heavy Strike of Trarthus** grants `stat:active_skill_additive_spell_damage_modifiers_apply_to_attack_damage_at_%_value` (CONFIRMED)
- `stat:spell_damage_+%` is a `stat_mechanic_operand` of the bridge family (CONFIRMED — 6 operand rows)
- **HYPOTHESIS leg:** the *mana-scaling* spell stat is **not** itself a bridge operand. `carriers(stat:spell_damage_+%_per_100_maximum_mana_up_to_60%)` and `neighbour` on it return **no** `stat_mechanic_*` rows; only the canonical `stat:spell_damage_+%` is bound. Whether the bridge picks up conditional/per-mana spell variants is **unknown** — the KB does not say.
- Quadratic shape: mana raises the flat added chaos **and** the spell→attack multiplier of the same hit. Both legs CONFIRMED as mana-fed; the *product* is HYPOTHESIS (engine formula, no KB edge).

### A2 — Intelligence Double-Strike · X = intelligence · output = hit chaos damage · **quadratic CANDIDATE**

- `Intelligence → base maximum mana` → seed → `Added Attack Chaos Damage` (all CONFIRMED)
- `intelligence → chance to deal double damage, per 10 int` — **Heavy Strike of Trarthus** `stat:chance_to_deal_double_damage_%_per_10_intelligence` (CONFIRMED, sole carrier = that gem)
- Same gem also carries flat `stat:chance_to_deal_double_damage_%`, `stat:attack_speed_+%`, `stat:damage_+%`
- Quadratic shape: int drives the flat added chaos (through mana) **and** the double-damage
  chance directly; both legs are direct stat grants, no mechanic binding needed.
  Product = HYPOTHESIS (no KB edge states that double damage multiplies the hit).
- Strongest-evidenced architecture of the run: **zero hypothesis-only legs except the product formula**.

### A3 — Mana-as-Energy-Shield · X = maximum mana → ES · output = sustain · **quadratic CANDIDATE (pool)**

- Seed: `stat:base_skills_cost_es_instead_of_mana_life` — skills are paid in **ES** (CONFIRMED, sole carrier)
- Seed: `(10-15)% faster start of Energy Shield Recharge` → `stat:energy_shield_delay_-%` (CONFIRMED)
- `maximum mana → Extra Maximum ES` — **Mindspiral** (Helmet) "Gain (10-15)% of Maximum Mana as Extra Maximum Energy Shield" (CONFIRMED, sole carrier)
- `reserved mana → base max ES` — **Sanctuary of Thought** (Hierophant notable) `stat:guardian_reserved_mana_%_given_to_you_and_nearby_allies_as_base_maximum_energy_shield` (CONFIRMED)
- `intelligence → ES %` (CONFIRMED engine edge) **and** `intelligence → base mana` (CONFIRMED) → mana → ES (CONFIRMED) ⇒ **two independent int-fed legs into one pool**
- Consumption leg: the ES pool is the *fuel* the seed's cost-swap spends — this is what makes the pool a resource rather than a dead defensive stat
- Ladder: multi-use (mana → chaos damage **and** mana → ES) plus a two-leg int→ES pool.
  The multiplicative pool formula is engine semantics → product = HYPOTHESIS.

### A4 — Two Mana Consumers, One Damage Type · X = maximum mana · output = chaos hit damage · **multi-use + converter**

- seed: `maximum mana → Added Attack Chaos Damage` (CONFIRMED by prose)
- **Kinetic Blast of Clustering** → `stat:added_physical_damage_to_attacks_equal_to_%_maximum_mana` (CONFIRMED, sole carrier = that gem) ⇒ a *second* mana→attack-added-damage consumer, in physical
- **Ming's Heart** (Ring) "Gain (40-60)% of Physical Damage as Extra Chaos Damage" → `stat:physical_damage_%_to_add_as_chaos` (CONFIRMED, 61 carriers; sole-carrier uniques: Ming's Heart 40-60 %, Obliteration 30-40 % on Wand, Spinehail / Maloney's Nightfall 10-15 % on Quiver)
- The converter makes both mana consumers land in the same output type. Honest classification:
  the two chaos legs **add** (both linear in mana) ⇒ **multi-use**, not quadratic. The
  mana × converter-% pair *is* an interacting 2-input product, but it is not one axis.
- `stat:lightning_damage_%_to_convert_to_chaos` → **0 carriers**, so the Mind-of-the-Council
  lightning consumer cannot be funnelled into chaos; recorded empty search.

### A5 — Lowest-of-Pool Fire · X = min(max life, max mana) · output = fire damage · **multi-use + axis tax**

- **The Scales of Justice** (Shield) "Unaffected by Ignite or Shock if Maximum Life and Maximum Mana are within 500" (CONDITIONAL, needs both pools high and close)
- same item: "Has no Energy Shield" — **structurally incompatible with A3** (the seed's ES-cost identity). Documented as a hard conflict; the validator does not model it (ES is a stat, not a slot/ascendancy constraint).
- same item: `(3-4) to (7-8) added Fire Damage per 100 of Maximum Life or Maximum Mana, whichever is lower` → `stat:lowest_max_life_mana_divided_by_100`
- **Seed's role here is negative and load-bearing:** the seed's `(60-40)% reduced maximum Mana`
  lowers the *minimum* of the two pools, so the seed taxes this axis. This is the one
  architecture where the seed is a drag rather than a driver — recorded, not smoothed over.
- Also on the item: `+(40-70) to maximum Life` (raises the other side of the min),
  `(10-15)% increased Spell Damage`.

### Cross-architecture exclusions (why these are not variants of each other)

| | axis | output | engine | key differentiator |
|---|---|---|---|---|
| A1 | max mana | hit chaos | spell→attack bridge | mana-scaling *spell* multiplier |
| A2 | intelligence | hit chaos | double-damage proc | attribute-driven second leg |
| A3 | max mana → ES | sustain | cost-source swap + mana→ES | mana is not consumed |
| A4 | max mana | hit chaos | damage-type converter | physical mana leg converted |
| A5 | min(life,mana) | fire | min-pool + proximity condition | seed taxes the axis |

Distinct weapon classes, distinct ascendancy notables, distinct helm/ring/offhand pressure.

---

## 4. Sweep log

| sweep | what ran | what it added |
|---|---|---|
| 0 | seed resolve + `neighbour` + `carriers` on all 4 mods and all 5 granted stats | seed census; 3 sole-carrier facts |
| 1 | `resolve --type Stat` over `mana` / `intelligence` / `energy_shield` / `Chaos`; `neighbour` on `stat:intelligence`, `stat:maximum_mana`, `stat:base_maximum_mana`; `carriers` on 30+ harvested ids | 2 `attribute_grants_stat` engine rows; 4 mana `stat_scales_with` consumers; seed-edge gap recorded |
| 2 | mechanic space on `stat:spell_damage_+%`; bridge stat carriers; Crown of Eyes / Mindspiral / Ming's Heart / Scales of Justice / Mind of the Council / Indigon neighbour walks | spell→attack bridge family (15 gems, 6 operand rows); Prodigal Perfection mana→spell% ; Mindspiral mana→ES |
| 3 | converter space (`to_convert_to_chaos`, `to_add_as_chaos`), depletion space (Arcane Cloak, Manabond), `Transformed to apply to` pattern, accuracy families, charge families, ailment families | A4 converter; A5 min-pool; accuracy carrier Shaper's Touch; charge + ailment dead-ends |
| 4 | two-hop stat→modifier→unique walk + `unique_in_class` per carrier for the slot audit; re-sweep of the frontier | slot map (§5); Mindspiral/Crown-of-Eyes/Mind-of-the-Council 3-way helmet contention |
| 5 | `validate_addition` per component, `weapon_check` per gem, `validate_build(final=True)` per architecture | all five architectures FINAL valid; two documented INVALID compositions (helmet clash, 2H+shield) |

**Stop reason: fixed point.** Sweep 5 re-probed every frontier node in the subgraph and
produced no new nodes, no new edges, and no reclassifications; the only outputs were validator
verdicts on compositions already known from sweep 4's slot map. 5 of the 10-sweep cap used.

---

## 5. Full-slot audit (§6)

Slot list derived from KB structure (`unique_in_class` on every axis-evidenced carrier), not
assumed. Omeyocan (mana→evasion) is Boots, not Helmet. Evidenced carriers per capacity:

| capacity | axis-evidenced carrier(s) |
|---|---|
| Amulet | **Whispers of Infinity** (seed); mana% alternatives: Atziri's Foible, Voice of the Storm, Choir of the Storm |
| Helmet | **Crown of Eyes** (spell→attack 150 %), **Mindspiral** (mana→ES), **Mind of the Council** (mana→lightning), Indigon (mana-**spent**), Indigon/Mindspiral/Crown of Eyes/Mind of the Council contend for **one** slot — 4-way contention |
| Ring | **Ming's Heart** (phys→chaos 40-60 %), Obliteration is a Wand; Dream Fragments (mana%) |
| Wand | **Reverberation Rod** (int), Obliteration (phys→chaos 30-40 %), Moonsorrow / Midnight Bargain / Amplification Rod (int) |
| Staff / Warstaff | Fencoil (40-50 % global damage + 10-20 % mana + L8 Trap), Dying Breath (18 % damage + 18 % mana) — both VALID for Heavy Strike of Trarthus |
| Quiver | Spinehail, Maloney's Nightfall (phys→chaos 10-15 %) |
| Shield | **The Scales of Justice** — validator: `INVALID` together with any two-handed main hand (`offhand: shield requires a one-handed main weapon`) |
| Gloves | **Shaper's Touch** (accuracy per int, +1 mana per 4 str); Lochtonial Caress |
| Body Armour | Voll's Protector — note its own `50% reduced maximum Mana` (compounds the seed's tax) |
| Belt | Graven's Secret (mana%) |
| Mace | Chober Chaber (mana%) |
| Jewel | **Healthy Mind** (life→mana at 200 % + 15-20 % mana), Spirited Response (unavailable) |
| Body Armour (mana→ES variants) | mutated body armours — **0 unique carriers** |

**Recorded empty searches** (exact queries, `meta.counts` all zero):

`stat:chaos_damage_+%_per_100_max_mana_up_to_80` · `stat:attack_damage_+%_per_500_maximum_mana` ·
`stat:spell_damage_+%_per_500_maximum_mana` · `stat:damage_+%_on_full_mana` ·
`stat:maximum_mana_%_to_convert_to_armour_at_doubled_value` ·
`stat:lightning_damage_%_to_convert_to_chaos` ·
`mod:ClarityManaAddedAsEnergyShield` · `mod:EnergyShieldCostAsManaCostUnique__1` ·
`mod:GainManaPer2IntelligenceUnique_1` (+1 mana per 2 int — **no unique carries it**) ·
`mod:EnergyShieldRechargeApplyToManaUnique__1` ([DNT], 0 carriers) ·
`stat:energy_shield_protects_mana` · `stat:total_added_chaos_damage_from_mana_cost` ·
`stat:curse_effect_+%_if_200_mana_spent_recently` · `stat:skill_gain_es_cost_%_of_mana_cost` ·
`stat:gain_accuracy_rating_equal_to_intelligence` · `stat:life_recoup_also_applies_to_energy_shield`

---

## 6. Coverage fixtures (§13, quarantined — reported, never used as a search strategy)

1. **≥2 simultaneously usable applies-to bridge stats composed together** — **surfaced**:
   Crown of Eyes "Attacks have 150% Arcane Might" **and** Heavy Strike of Trarthus' own
   `stat:active_skill_additive_spell_damage_modifiers_apply_to_attack_damage_at_%_value`
   compose in one validated build (A1).
2. **Single item converting ≥3 attributes into different resources** — **not surfaced**:
   the mined `Transformed to apply to` family returned 6 mods, every one a single-input →
   single-output transform (Fire/ Cold/ Armour / ES / Mana / Evasion). Process gap, no patch.
3. **attribute→resource engine rules via intrinsic rows** — **surfaced, 2 rows**:
   `stat:intelligence → stat:base_maximum_mana`, `stat:intelligence → stat:maximum_energy_shield_+%`.
4. **Stat families with zero unique carriers reaching the CANDIDATE tier with an exact gap reason** — **surfaced**, 15 recorded empty searches (§5), each with its exact `carriers` query.
5. **Accuracy / hit-chance audit for every attack build** — **evidenced carrier**:
   *Shaper's Touch* (Gloves) "+2 Accuracy Rating per 2 Intelligence" (sole carrier of
   `stat:X_accuracy_per_2_intelligence`); also Crown of Eyes "+(300-350) to Accuracy Rating",
   and `mod:MutatedUniqueClaw16AccuracyRatingPercentPer25Intelligence` (0 unique carriers).
6. **Charge generation/consumption families linked to the axis** — family found and then
   **killed by the seed**: Arcane Capacitor (`stat:arcane_surge_effect_+%_per_200_mana_spent_recently_up_to_50%`),
   `stat:gain_X_frenzy_charges_after_spending_200_mana` (1 modifier, 0 uniques). All are
   *mana-spent* gated ⇒ dead under the seed's ES-cost. See §7.
7. **Per-pool consumer families for every pool the axis touches** — mana consumers enumerated
   to 13 (see §7 table); life touched only through A5's min-pool and Healthy Mind's
   life→mana transform.
8. **spell→attack damage bridge when the output is attacks** — **surfaced** (Crown of Eyes +
   the 15-gem bridge family).
   **DoT/ailment multipliers when the output is chaos** — **not surfaced**: the poison family
   is fragmented into conditionals (`per_frenzy_charge`, `per_power_charge`, `vs_bleeding_enemies`,
   `with_over_300_dexterity`) and `stat:ignite_damage_+%` has 6 carriers, all monster/animal-charm
   mods — **zero unique ailment-multiplier carriers**. Every architecture below therefore
   stays on **hit** damage; no DoT output is claimed.

---

## 7. Dead ends and hard conflicts (recorded, not smoothed over)

| item / family | KB fact | verdict |
|---|---|---|
| **Indigon** (Helmet) | "(20-25)% increased Spell Damage for each 200 total Mana you have Spent Recently, up to 2000 %" + "(50-60)% increased Cost of Skills for each 200 total Mana Spent Recently" | **DEAD** — the seed pays skill costs in ES, so no mana is ever spent. Also blocks Mindspiral/Crown of Eyes (helmet). |
| **Dark Bargain / Forbidden Rite** (`stat:added_chaos_damage_%_mana_cost_if_payable`, 6 carriers) | added chaos = % of **Mana Cost, if payable** | **DEAD** — same reason |
| **Manabond** (`stat:mana_void_gain_%_missing_unreserved_mana_as_base_lightning_damage`) | damage from **missing** mana | **DEAD** — no mana is spent, so there is no deficit |
| **Arcane Cloak** (`stat:arcane_cloak_consume_%_of_mana` + `stat:arcane_cloak_gain_%_of_consumed_mana_as_lightning_damage`; enchantments spend an extra 10 % / 15 % of current mana) | deliberate mana drain → lightning | **HYPOTHESIS only** — the gem's drain is explicitly mana, but no KB edge says whether the seed's ES-cost override applies to it. Not built. |
| **Crown of Eyes + Mindspiral** | both `item_class:Helmet` | **INVALID** — `head: capacity 1 exceeded (2 slot units)` (validator) |
| **The Scales of Justice + any two-hander** | shield needs a one-handed main hand | **INVALID** — `offhand: shield requires a one-handed main weapon` (validator) |
| **The Scales of Justice + A3 identity** | "Has no Energy Shield" | hard semantic conflict, not validator-modelled |
| **Voll's Protector** (Body) | "50% reduced maximum Mana" | anti-synergy: a second, independent reduction on top of the seed's own "(60-40)% reduced maximum Mana". The KB models no reduction-arithmetic edge, so the combined figure is **unknown** — not estimated. |
| `mod:MaximumManaUniqueBodyStrInt1` | "50% reduced maximum Mana" | same, body-armour family |
| `stat:mana_%_gained_on_kill`, `stat:maximum_mana_leech_*`, `stat:mana_leech_from_chaos_damage_permyriad` | mana **recovery** families | recorded; not part of any architecture — recovery does not raise maximum mana, so it does not feed the seed |

**The mana-recovery trap, stated once:** nothing in this run raises `maximum mana` by
*leech, regeneration, or recovery*. The seed scales off the **maximum**, so sustain families
are decorative here. Only flat mana, mana %, and `Intelligence` raise it.

---

## 8. Genuine KB / API gaps (fail-closed)

1. **The seed's own scaling edge is unmodelled.** `stat:max/min_attack_added_chaos_damage_per_100_mana`
   has zero outgoing edges — no `stat_scales_with` from `stat:maximum_mana`, unlike its four
   sibling consumers. The mana→damage link rests on modifier prose and id family only.
2. **The bridge binds only the canonical spell-damage stat.** `stat:spell_damage_+%` carries
   6 `stat_mechanic_operand` rows; `stat:spell_damage_+%_per_100_maximum_mana_up_to_60%` and
   `stat:spell_damage_+%_per_500_maximum_mana` carry none. Whether conditional spell-damage
   variants are picked up by "additive spell damage modifiers apply to attack damage" is
   **unknown**; A1's bridge leg is therefore a hypothesis, not a confirmation.
3. **No product/multiplier semantics in the graph.** Double damage, `%` multipliers, and pool
   formulas are engine semantics with no KB edges, so no architecture in this run can be
   promoted above **quadratic CANDIDATE**. The *legs* are confirmed; the *product* is not.
4. **Jewel / flask slot model absent** — Healthy Mind (life→mana at 200 %) surfaces as
   `unknown`, never assumed valid; it appears only in the CANDIDATE tier of A3.
5. **`[DNT]` modifiers** (e.g. Energy Shield Recharge instead applies to Mana) exist as mods
   with zero carriers — availability is not modelled for them.
6. **Alternate-ascendancy exclusions were non-zero on shared families** (`excluded_alternate_ascendancies`
   = 9 on `stat:chaos_damage_+%` and `stat:maximum_mana_+%`, 1 on
   `stat:mana_%_to_add_as_energy_shield`). Checked before each absence claim; no absence in
   this report is asserted while that flag could hide a carrier.

---

## 9. Artifacts

- `builds.md` — five build sheets, two tiers (VALIDATED core / CANDIDATE maximized variant).
- Reproduce: `uv run python santa-maria/tools/research.py resolve "Whispers of Infinity" --type UniqueItem`
  then `neighbour unique:1461 --depth 1`, `carriers <mod>`, `carriers <stat>`,
  `validate '<build-state json>'`.