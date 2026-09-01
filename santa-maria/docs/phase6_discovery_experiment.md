# Phase 6 — Graph Discovery Experiment

A read-only exploration using the Phase 6 API (`get_start_seed` + `get_neighbour`)
against the factual KB graph. Ten build concepts discovered from seeded starting
points — not from any predefined build list.

For each concept:

- **Anchor item** — the unique item that started the discovery
- **Graph path** — the confirmed relationships the API returned (item names, not raw IDs)
- **Facts** — what the KB actually proves
- **Why it's interesting** — the human explanation (downstream reasoning,
  separate from the facts)

> Everything under **Facts** is confirmed KB evidence (confirmed edges / stat
> nodes). Everything under **Why it's interesting** is my own reasoning on top of
> those facts — the graph does not claim these are good builds.

---

## 1. Life-Regen → Rage Engine

**Anchor:** **Kaom's Spirit** + **Kaom's Primacy**

**Graph path:**
```
Kaom's Spirit  --grants--> regenerate 1 Rage per X Life Regeneration
Kaom's Spirit  --grants--> Life Recovery from Regeneration is NOT applied
Kaom's Spirit  --grants--> Rage Loss Delay
Kaom's Primacy --grants--> Physical Damage % added as Fire per Rage
Kaom's Primacy --grants--> +1 Maximum Endurance Charges
```

**Facts:** all of the above are confirmed `unique_modifier_association` →
`modifier_grants_stat` edges.

**Why it's interesting:** the gloves turn your life regeneration into a Rage
generator — your regen stops healing you and starts fueling rage instead. And the
axe converts that rage into fire conversion plus extra endurance charges. A pure
resource-conversion loop: life regen → rage → fire damage + tankiness.

---

## 2. Power↔Frenzy Charge Swap + Elusive

**Anchor:** **Badge of the Brotherhood**

**Graph path:**
```
Badge of the Brotherhood --grants--> Maximum Frenzy Charges equals Maximum Power Charges
Badge of the Brotherhood --grants--> Elusive Effect +% per Power Charge
Badge of the Brotherhood --grants--> % chance to lose a Power Charge when you gain Elusive
Badge of the Brotherhood --grants--> Travel Skill cooldown recovery per Frenzy Charge
```

**Facts:** all confirmed edges.

**Why it's interesting:** power charges secretly double as frenzy charges (the
equality stat), power charges scale how strong your Elusive is, and gaining
Elusive burns a power charge. So you're constantly cycling charges into Elusive
while keeping frenzy generation online — a charge-currency economy on one amulet.

---

## 3. Simulated Rampage — Stacks Without the Kill Chain

**Anchor:** **Null and Void**

**Graph path:**
```
Null and Void --grants--> Simulated Rampage (gain Rampage stacks)
Null and Void --grants--> Physical Damage Immunity at Rampage threshold
Null and Void --grants--> Dispel Status Ailments at Rampage threshold
(per-stack scaling stats exist as nodes but have no confirmed granting mod:
  attack_speed_+%_per_10_rampage_stacks, damage_+%_per_10_rampage_stacks,
  minion_damage_+%_per_10_rampage_stacks)
```

**Facts:** stack generation + the two threshold payoffs are confirmed. The
per-stack damage/attack-speed scaling exists as Stat nodes but is **not** linked
to any confirmed modifier — treat that part as a lead, not a fact.

**Why it's interesting:** Rampage normally needs a 1,000-kill chain; this unique
hands you stacks directly, and at the stack threshold you get temporary physical
damage immunity and ailment cleansing — a defensive burst on a timer.

---

## 4. Conditional Crimson Dance Bleed

**Anchor:** **Sanguine Gambol**

**Graph path:**
```
Sanguine Gambol --grants--> Crimson Dance if you've dealt a Critical Strike recently
Sanguine Gambol --grants--> chance to Bleed on Critical Strike
Sanguine Gambol --grants--> attack damage vs Bleeding enemies
Sanguine Gambol --grants--> local Physical Damage %
```

**Facts:** all confirmed.

**Why it's interesting:** the dagger grants a *keystone* (Crimson Dance — the
"up to 8 bleeds" mechanic) only while you've crit recently, and it also makes
crits bleed. It's a fully self-contained bleed-on-crit package: crit → keystone
on → crit bleeds → bonus damage vs bleeding.

---

## 5. Self-Skitterbot Ailment Support

**Anchor:** **The Arkhon's Tools**

**Graph path:**
```
The Arkhon's Tools --grants--> Summon Fire Skitterbot
The Arkhon's Tools --grants--> Skitterbot auras also affect you
The Arkhon's Tools --grants--> Skitterbot non-damaging ailment effect +%
The Arkhon's Tools --grants--> Trap and Mine throw speed +%
```

**Facts:** all confirmed.

**Why it's interesting:** Skitterbots normally buff traps/mines with shock/chill
auras — here those auras also hit *you*. That's a self-shock / self-chill angle
(the belt even boosts the non-damaging ailment effect), combined with trap/mine
throw speed. A trap-mine build that weaponizes its own minion auras on the player.

---

## 6. Cold → Fire Ignite Explosion

**Anchor:** **Pyre**

**Graph path:**
```
Pyre --grants--> Cold Damage % converted to Fire
Pyre --grants--> Ignited Enemies explode on Kill
Pyre --grants--> Burn Damage +%
Pyre --grants--> Cold Damage taken as Fire
```

**Facts:** all confirmed.

**Why it's interesting:** cold damage turns into fire (feeding ignites), and
ignited enemies explode when they die — a clear ignite-chaining explosion loop.
The defensive side (cold taken as fire) is a bonus that dovetails with fire
resistance stacking.

---

## 7. All-Attribute Hybrid Scaling

**Anchor:** **Shaper's Touch**

**Graph path:**
```
Shaper's Touch --grants--> Energy Shield per Strength
Shaper's Touch --grants--> Evasion per Intelligence
Shaper's Touch --grants--> Melee Physical Damage per Dexterity
Shaper's Touch --grants--> Life per Dexterity, Mana per Strength, Accuracy per Intelligence
Strength      --scales-with--> energy_shield_+%_per_10_strength
Dexterity     --scales-with--> melee_physical_damage_+%_per_10_dexterity
Intelligence  --scales-with--> evasion_+%_per_10_intelligence
```

**Facts:** all confirmed (the per-attribute links are `stat_scales_with` edges).

**Why it's interesting:** one pair of gloves rewards *every* attribute with a
different defensive or offensive layer — Str→ES, Int→Evasion, Dex→Melee phys,
plus life/mana/accuracy. Stack all three attributes and you scale six stats at
once: a tri-attribute hybrid where no single attribute is the "main" one.

---

## 8. Damage-Taken-As-Cold Chill Defense

**Anchor:** **Crystal Vault**

**Graph path:**
```
Crystal Vault --grants--> Physical Damage taken as Cold
Crystal Vault --grants--> Fire Damage taken as Cold
Crystal Vault --grants--> Cannot be Chilled
Crystal Vault --grants--> Cold Ailment Effect +%
Crystal Vault --grants--> Chill Duration +%
```

**Facts:** all confirmed.

**Why it's interesting:** it converts incoming physical AND fire damage into
cold — but you can't be chilled, so the cold conversion is pure defense with no
slowdown downside — while the body armour also boosts how strong your own cold
ailments are. "Eat physical and fire, pay in cold, stay un-chillable."

---

## 9. Hex-Consumption Curse Loop

**Anchor:** **Coiling Whisper**

**Graph path:**
```
Coiling Whisper --grants--> Eat Soul when Hex expires
Coiling Whisper --grants--> Targets unaffected by your Hexes
Coiling Whisper --grants--> Curse Area of Effect +%
```

**Facts:** all confirmed.

**Why it's interesting:** your hexes expire into a "soul" payoff, while targets
are literally unaffected by your hexes — a self-contained curse that consumes
itself. **Honest caveat:** the apparent contradiction (unaffected yet consumed)
can't be resolved from the graph; this is the strangest, least-safe concept.

---

## 10. Ward + Flask Sustain

**Anchor:** **Medved's Challenge**

**Graph path:**
```
Medved's Challenge --grants--> local Ward +%
Medved's Challenge --grants--> gain Flask Charges every second if you hit a Unique Enemy
Medved's Challenge --grants--> Flask Charges gained from Kills +%
```

**Facts:** all confirmed.

**Why it's interesting:** Ward (the ES-style defensive layer for non-ES builds)
plus reliable flask charge generation *while bossing* (hitting uniques) — a
defensive layer that pays for its own flask uptime in exactly the fights where
you need it.

---

## Ranking (my own judgment, not graph facts)

1. **Life-Regen → Rage Engine** — most coherent conversion loop, both halves confirmed
2. **Power↔Frenzy Charge Swap + Elusive** — genuine build-around economy
3. **All-Attribute Hybrid Scaling** — scales six stats off one item, links confirmed
4. **Conditional Crimson Dance Bleed** — self-contained keystone-grant package
5. **Simulated Rampage** — novel stack source; per-stack scaling unconfirmed (lead only)
6. **Self-Skitterbot Ailment Support** — unusual self-ailment angle
7. **Cold → Fire Ignite Explosion** — clean but more conventional
8. **Damage-Taken-As-Cold Chill Defense** — solid but niche
9. **Ward + Flask Sustain** — utility loop, modest ceiling
10. **Hex-Consumption Curse Loop** — genuinely strange; unresolved tension, risky

## Method note

Seeds came from `get_start_seed` across several node types and seeds; anchors were
explored with `get_neighbour` (depth 1–2, `unique_modifier_association` +
`modifier_grants_stat` + `stat_scales_with`). No code, database, contract, or API
was modified. Candidate-only resolution was never used as evidence.
