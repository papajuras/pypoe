# whispers02 — Whispers of Infinity build discovery (clean slate)

**Date:** 2026-09-17 · **Start:** `resolve("Whispers of Infinity")` → `unique:1461`, availability `available` · **Interface:** public Research API only (phase8 `resolve`/`carriers`, phase6 `get_neighbour`, phase7 `validate_addition`/`validate_build`). No DB access, no prior-run reuse.

**Alternate-ascendancy exclusion note:** the mana-passive carrier query reported `excluded_alternate_ascendancies: 9` (Phrecia content suppressed by default). Those 9 carriers are NOT claimed absent — only excluded.

**Rendering limitation (API gap, not worked around):** the public API exposes modifier **ids but no numeric values and no display text**, and gem nodes carry only some display names. Every modifier below is therefore rendered from its KB stat/mod id and marked *(unresolved text)*; all numeric values are **UNKNOWN**. Availability is reported by the validator. Validated states mark which constraints were actually checked; "unknown" below is the validator's own limitation (jewels have no slot model), never assumed away.

---

## Amendment 2026-09-18 (correction of the 09-17 amendment)

The 09-17 amendment claimed **Memory Vault was removed from the game — that was wrong.** Memory Vault (`unique:713`) is in the game; its current mod is *"1% increased Armour per 50 Reserved Mana"* (`mod:GainArmourEqualToManaReservedUnique__1`). Two further corrections:

1. **The wording "gain armour equal to mana reserved" exists nowhere as mod text** — it was fabricated from the mod *id* (ids are fossils; id ≠ text). The per-100 `Divergent*` mod is not a "removed pre-3.16 version" either: Divergent/Anomalous/Phantasmal mods are **active alt-quality implicits** that can be crafted onto items; mod-level liveness is simply not knowable from the dump and is never claimed.
2. The 09-17 fix (manual `availability_overrides.json` + default exclusion of `unavailable` uniques from the API) was **surgically rolled back** — it was built on the misdiagnosis above. Replaced by a **live-only KB invariant**: association staleness is decided at build time (`extract_nodes` live-gate — an association enters the KB only when the mod's text is verifiably present in the unique's *current* PoB block; blockless uniques carry none; method-6/Vestigial associations are retired until separately modelled). The API does no staleness/availability filtering, so an empty carriers result is a true absence. `availability` remains a PoB *obtainability* verdict used by the validator. The public API now also exposes modifier **text** (`resolve` results, `carriers` rows, `meta.subject_text`), closing the id-as-prose gap this run tripped on.

Consequences for this report, re-validated against the rebuilt live-only KB (validator states re-run 2026-09-18): **Build 3 is restored to CANDIDATE** with Memory Vault's real per-50 mod text; **Build 2 is restored to its original committed shape with the Memory Vault helmet** (the post-amendment "generic helmet" variant is discarded). Both re-validate as `unknown` for the Healthy Mind jewel slot-model limitation only — unchanged. The sole-carrier claims in "The item" section were re-verified against the rebuilt KB and still hold (total: 1 each).

---

## The item (KB view)

Whispers of Infinity (`unique:1461`, Amulet, available) carries 4 modifiers:

| Mod id | Grants stat(s) | Tags |
| --- | --- | --- |
| `mod:AttacksGainMinMaxAddedChaosDamageBasedOnManaUnique__1` | `min/max_attack_added_chaos_damage_per_100_mana` *(unresolved text; value UNKNOWN)* | attack, chaos, chaos_damage, damage, mana, resource |
| `mod:SkillsCostEnergyShieldInsteadOfManaLifeUnique__1` | `base_skills_cost_es_instead_of_mana_life` *(unresolved text)* | life |
| `mod:PercentReducedMaximumManaUnique_1` | `maximum_mana_+%` (negative per mod id) *(value UNKNOWN)* | — |
| `mod:ReducedEnergyShieldDelayImplicit1_` | `energy_shield_delay_-%` | defences, energy_shield |

**Central structural fact:** the two stats `max/min_attack_added_chaos_damage_per_100_mana` and `base_skills_cost_es_instead_of_mana_life` are carried by **no other node in the KB** (`carriers` total: 1 each — this item's own mods). Whispers of Infinity is the sole carrier of both.

---

## Scaling analysis

Scaling axis **X = maximum mana** (plus a second pool axis **X₂ = maximum energy shield**).

| Path | Flow | Status |
| --- | --- | --- |
| A | X → attacks gain added **chaos** per 100 mana (Whispers) | confirmed (`modifier_grants_stat`) |
| B | X → attacks gain added **lightning** based on max mana — `mod:AttackLightningDamageMaximumManaUnique__1__` on Mind of the Council (`unique:533`, helmet) | confirmed (mod id + tags attack/mana) |
| A×B | both are flat added damage summed into the same attack hits | **additive in X — linear, NOT X²**. No mechanic in the KB multiplies one by the other. |
| C | X → dodge and spell dodge per max mana — Omeyocan (`unique:795`, boots, `mod:DivergentDodgeAndSpellDodgePerMaximumManaUnique__1`) | multi-use (defense), no damage interaction |
| D | X₂ = max ES → Energy Blade attack lightning (`stat:storm_blade_min/max_lightning_damage_from_es_%`, `gem:EnergyBlade`); quality stat family converts attack lightning → chaos (`stat:storm_blade_quality_attack_lightning_damage_%_to_convert_to_chaos`) | confirmed stats; quality linkage carried by no edges in KB → *quality conversion UNCONFIRMED on the gem* |
| E | skills cost ES instead of mana → mana never spent → unreserved mana pinned at max → Archmage (`gem:SupportArchmage`, `stat:archmage_gain_lightning_damage_%_of_max_unreserved_mana`) and "while not low mana" gates stay live | structural hypothesis, consistent with all carrier data |

**The resource inversion** is the discovery's core: Whispers makes ES the cost resource, which (1) freezes mana-spending engines, (2) keeps mana-fullness gates permanently open, (3) lets mana pool scale damage via paths A/B without ever being paid away.

**Classification: multi-use compound. No confirmed quadratic axis was found in the KB.** Paths A and B feed the same hit but sum flat damage (linear in X); C and E are independent consumers. Per the scaling skill this is reported as-is, not inflated to X².

---

## Build 1 — Dual-pool Energy Blade attacker

Status: **CANDIDATE** — validator `unknown` only for Healthy Mind (jewel: "no slot model for this item class — not checked", a declared validator limitation); slot occupancy, weapon configuration, gem support, ascendancy composition, availability: all valid. Weapon context: one-hand sword equipped; Energy Blade weapon-restriction check passed with it.

Ascendancy: **Hierophant** (evidenced by committed nodes).

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | Whispers of Infinity *(available)* | **attacks gain min/max added chaos damage per 100 mana** (value UNKNOWN, text unresolved); **skills cost ES instead of mana [and life per stat id]**; maximum mana +% (reduced per mod id, value UNKNOWN); ES delay -% |
| Helmet | Mind of the Council *(available)* | **attacks gain lightning damage based on maximum mana** (`mod:AttackLightningDamageMaximumManaUnique__1__`, text unresolved); **lose % of mana when you use an attack skill**; lightning damage % taken from mana before life; physical damage removed from mana before life (mutated variant); chance to be shocked; +local ES; +local evasion and ES |
| Body | — (not committed) | — |
| Gloves | Lochtonial Caress *(available)* | increased attack speed; increased cast speed; **increased mana**; attack speed on full life (divergent variant); power/frenzy or endurance charge on kill (mutated/divergent variants); +local armour |
| Belt | Graven's Secret *(available)* | **gain absorption charges instead of power charges**; maximum absorption charges equals power charges; minimum absorption-charge modifiers equal power charges; **maximum mana +%**; lightning resist; stun recovery (implicit) |
| Ring | Dream Fragments *(available)* | maximum mana +%; mana regeneration; stun recovery (mutated variant) |
| Offhand | Esh's Visage *(available, shield)* | **chaos damage does not bypass ES while not low life or mana** (mutated: "not low mana" variant); damage cannot be reflected (mutated); reflects shock to enemies in radius; +local ES %; spell damage (implicit) |
| Weapon | Rebuke of the Vaal *(available, one-hand sword)* | adds local fire/cold/lightning/chaos/physical damage; accuracy (implicit); trap throw speed (mutated variant) |
| Jewel | Healthy Mind *(available)* | **life passives in radius become mana passives**; maximum mana +% — jewel not validated (no slot model) |
| Skill gem | Energy Blade | grants `base_deal_no_damage`, `storm_blade_min/max_lightning_damage` (flat), **`storm_blade_min/max_lightning_damage_from_es_%`** (lightning from max ES — values UNKNOWN), `storm_blade_energy_shield_+%_final`, `storm_blade_damage_+%_final_with_two_hand_weapon`; tags: lightning. Quality stat family (`storm_blade_quality_*`: attack lightning→chaos conversion, crit chance, shock chance) exists in KB but has **no carrier edges from the gem — quality conversion UNCONFIRMED** |
| Passives | Hierophant ×2 + Mind Drinker | Mana Regeneration/Mana (small, Hierophant); **Divine Guidance** (notable, Hierophant); **Mind Drinker** (notable — mana sustain for MotC's per-attack mana loss) |

**Why it works** — Mind of the Council turns the maximum-mana pool into added lightning on attacks; Whispers of Infinity turns the same pool into added chaos on attacks, and both flat sources ride every attack multiplier together. Energy Blade adds a third added-damage stream scaled by the *energy shield* pool, with the shield doubling as the cost resource Whispers mandates. Esh's Visage and the mana kept full by the ES-cost engine close the chaos-defense gap; Mind Drinker and Hierophant mana-regeneration offset MotC's per-attack mana loss.

**Evidence**
`unique:1461` → chaos per 100 mana → attack hits; `unique:533` → lightning per max mana → same attack hits; `gem:EnergyBlade` → lightning from max ES → same attack hits; `unique:396` → life passives → mana passives → X.

---

## Build 2 — Ivory Tower chaos battery

Status: **CANDIDATE** — validator `unknown` only for Healthy Mind (jewel: "no slot model for this item class — not checked", a declared validator limitation); slot occupancy, weapon configuration, gem support, ascendancy composition, availability: all valid. Weapon context: one-hand sword equipped; Energy Blade weapon-restriction check passed with it.

*Re-amendment 2026-09-18: the 09-17 "removed from the game" correction was itself wrong — Memory Vault is live; the build is restored to its original committed shape with the Memory Vault helmet and re-validated (`unknown` for the jewel limitation only).*

Ascendancy: **Hierophant** (evidenced by committed nodes).

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | Whispers of Infinity *(available)* | as above |
| Body | The Ivory Tower *(available)* | **chaos damage taken from mana before life** (+ divergent duplicate mod); **maximum ES per reserved life** (`mod:MaximumEnergyShieldPerReservedLifeUnique__1`, text unresolved); ES regeneration; increased mana; intelligence |
| Helmet | — (generic ES/mana-regen helmet, not committed) | no unique established by discovery |
| Ring | Dream Fragments *(available)* | as Build 1 |
| Boots | Dance of the Offered *(available)* | **gain onslaught while not on low mana** (+ divergent variant); increased mana |
| Jewel | Healthy Mind *(available)* | as Build 1 (not validated — jewel limitation) |
| Weapon | Rebuke of the Vaal *(available)* | as Build 1 |
| Skill gem | Energy Blade | as Build 1 |
| Passives | Hierophant ×2 | Mana Regeneration/Mana (small nodes) |

**Why it works** — The Ivory Tower converts incoming chaos damage into a mana tax, and Whispers guarantees mana is never spent by skills, so the tax lands on a permanently full pool. The ES-cost engine simultaneously supplies Energy Blade's ES-scaled attack damage, so the same shield pool pays costs and fuels damage. The Hierophant regen nodes refill the mana buffer; Dance of the Offered's onslaught stays live because mana never drops low.

**Evidence**
`unique:1088` → chaos damage taken from mana before life; `unique:1461` → skills cost ES instead of mana → mana full → buffer intact; `gem:EnergyBlade` → damage from max ES; `unique:794` → onslaught while not low mana.

---

## Build 3 — Memory Vault reservation-armour

Status: **CANDIDATE** — re-validated 2026-09-18 against the rebuilt live-only KB: validator `unknown` only for Healthy Mind (jewel: "no slot model for this item class — not checked", a declared validator limitation). The 09-17 REJECTED status was based on the false "removed from the game" claim, retracted in the top amendment.

*Reservation feasibility remains explicitly out of the validator's scope (declared limitation).*

Ascendancy: **Hierophant** (evidenced by committed regen node).

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | Whispers of Infinity *(available)* | as above |
| Helmet | Memory Vault *(available)* | **1% increased Armour per 50 Reserved Mana** (real mod text; the Divergent per-100 form is an active alt-quality implicit twin, not a removed version); mana regeneration; +local ES |
| Boots | Omeyocan *(available)* | **dodge and spell dodge per maximum mana** (+ divergent variant); **lose % of mana per second**; maximum mana +% |
| Jewel | Healthy Mind *(available)* | as Build 1 (not validated — jewel limitation) |
| Weapon | Rebuke of the Vaal *(available, sword)* | as Build 1 |
| Skill gem | Energy Blade | as Build 1 (ES-scaled lightning attacks) |
| Passives | Mana ×2, Arcane Will, Hierophant regen | `passive:mana1647`, `passive:mana1648` (Mana); **Arcane Will** (notable); Mana Regeneration/Mana (small, Hierophant) |

**Why it works** — Memory Vault converts reserved mana into armour, so the reservation that normally starves mana-scaling builds here buys physical defense while the damage engine (Whispers' chaos per max mana + Energy Blade's ES lightning) runs unaffected — Whispers' damage keys on the maximum pool, not the unreserved remainder. Omeyocan adds a second defensive consumer of the same pool (dodge per max mana) and its per-second mana loss is absorbed by regeneration. *Reserved-mana generators (auras) were not established by this discovery — generic; values UNKNOWN.*

**Evidence**
`unique:713` → 1% increased Armour per 50 Reserved Mana (real text); `unique:1461` → chaos per 100 max mana (reservation-independent); `unique:795` → dodge/spell dodge per max mana.

---

## Build 4 — Full-mana Archmage ceiling engine (hypothesis)

Status: **CANDIDATE** — validator `unknown` only for Healthy Mind (jewel limitation); all checked constraints valid, including the Energy Blade+Archmage support chain. **The build's core claim is a hypothesis, not KB-confirmed** (see UNKNOWN below).

Ascendancy: **Hierophant** (evidenced by committed nodes).

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Amulet | Whispers of Infinity *(available)* | as above |
| Boots | Dance of the Offered *(available)* | gain onslaught while not on low mana; increased mana |
| Gloves | Lochtonial Caress *(available)* | as Build 1 |
| Belt | Graven's Secret *(available)* | as Build 1 |
| Ring | Dream Fragments *(available)* | as Build 1 |
| Jewel | Healthy Mind *(available)* | as Build 1 (not validated — jewel limitation) |
| Weapon | Rebuke of the Vaal *(available)* | as Build 1 |
| Gems | **Energy Blade** + **Archmage** (support) | Energy Blade as Build 1; Archmage grants `archmage_gain_lightning_damage_%_of_max_unreserved_mana` (value UNKNOWN) and `manaweave_cost_equals_%_unreserved_mana`; tags: lightning, support |
| Passives | **Sanctuary of Thought** (notable) + Hierophant regen | `stat:hierophant_area_of_effect_+%_per_50_unreserved_mana_up_to_100%` — unreserved-mana payoff |

**Why it works (hypothesis)** — Because Whispers makes skills cost ES instead of mana, nothing spends mana, so unreserved mana stays pinned at its maximum; Archmage's added lightning (% of max unreserved mana) then sits at ceiling permanently, and Sanctuary of Thought's AoE per 50 unreserved mana rides the same pinned variable. The engine's distinctive failure mode — spending mana loses damage — is structurally suppressed by the amulet itself.

**UNKNOWN (not resolved by this discovery):** the KB exposes no skill-type tags on `gem:SupportArchmage` — whether Archmage supports attacks (stacking a fourth added-damage source onto Whispers' hits) or spells only (splitting the engine into two outputs) is **unconfirmed**. Rendered as hypothesis; not presented as fact.

**Evidence**
`gem:SupportArchmage` → lightning = % of max unreserved mana; `unique:1461` → costs paid in ES, not mana → unreserved pinned; `passive:AscendancyHeirophant8` → AoE per 50 unreserved mana.

---

## Rejected / anti-synergistic (evidence-backed, not used)

- **Manabond** (`gem:Manabond`): gains `% missing unreserved mana` as base lightning damage; lightning penetration only **while on low mana**. Whispers freezes mana spending → missing mana stays ≈0. Structurally dead with this amulet.
- **Manaforged Arrows** (`gem:SupportManaforgedArrows`): `support_manaforged_arrows_damage_+%_final_per_mana_spent` — requires mana **spent**; the ES-cost engine spends none. Dead.
- **Indigon** (`unique:748`, helmet, available): `mod:SpellDamagePer200ManaSpentRecentlyUnique__1__` — needs mana spent recently; same freeze. Also helmet slot conflict with MotC/Memory Vault.
- **Voice of the Storm** (`unique:600`), **Choir of the Storm** (`unique:601`), **Atziri's Foible** (`unique:1018`/`unique:945`): all Amulets — slot conflict with Whispers of Infinity.
- **Chaber Cairn** (`unique:868`), **Mirebough** (`unique:893`): validator-reported **unavailable**.

## API gaps encountered (reported, not worked around)

1. **No numeric values / display text for modifiers and stats** via `resolve`/`carriers`/`neighbour` — build sheets could not render exact mod text or ranges; all rendered from ids as *(unresolved)*. *(Closed 2026-09-18: the public API now exposes modifier `text` / `meta.subject_text` — numeric VALUES remain unexposed.)*
2. **Energy Blade quality linkage missing** — `storm_blade_quality_*` stats exist (resolve) but have no carrier edges from `gem:EnergyBlade`; quality conversion left UNCONFIRMED.
3. **Gem skill-type tags not exposed** for `gem:SupportArchmage` — attack/spell supportability UNKNOWN (gap #3 above).
