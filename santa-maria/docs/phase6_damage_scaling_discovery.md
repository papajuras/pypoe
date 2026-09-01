# Phase 6 — Damage-Scaling Discovery Experiment

A second read-only exploration using the Phase 6 API (`get_start_seed` +
`get_neighbour`), focused specifically on **damage scaling** — unusual scaling
stats, conversion interactions, damage-type interplay, and attributes/charges as
damage sources. Ten distinct concepts.

Each entry:

- **Anchor item** — the unique item that anchored the discovery (names, not raw IDs)
- **Graph path** — the confirmed relationships the API returned
- **Facts** — confirmed KB evidence (confirmed edges / stat nodes)
- **Why it could deal damage** — my inference, clearly separate from the facts

> **Facts** = confirmed edges and stat nodes. **Why it could deal damage** = my own
> reasoning about how those confirmed mechanics multiply/convert damage. The graph
> does not claim these are good or meta builds.

---

## 1. Damage-Type Rotation Chain

**Anchor:** **Natural Hierarchy**

**Graph path:**
```
Natural Hierarchy --grants--> Physical Damage added as Lightning
Natural Hierarchy --grants--> Lightning Damage added as Cold
Natural Hierarchy --grants--> Cold Damage added as Fire
Natural Hierarchy --grants--> Fire Damage added as Chaos
```

**Facts:** all four conversion stats confirmed.

**Why it could deal damage:** the ring turns your physical hit into lightning, then
lightning into cold, then cold into fire, then fire into chaos — a full damage-type
rotation. Every step is an "added as" amplifier, so a modest physical hit is
re-presented in every element and ends in chaos (which normal elemental resistance
doesn't stop). Stack conversion bonuses along the chain and each element re-multiplies
the previous one.

---

## 2. Phys→Fire + Random-Element Bow

**Anchor:** **Blackgleam**

**Graph path:**
```
Blackgleam --grants--> Physical Damage % converted to Fire
Blackgleam --grants--> Weapon Physical Damage % added as a Random Element
Blackgleam --grants--> chance to Freeze / Shock / Ignite
Blackgleam --grants--> Elemental Status Ailment Duration
```

**Facts:** all confirmed.

**Why it could deal damage:** your bow's physical damage is both *converted* to fire
and *added as a random element* — so a single hit carries fire plus a bonus element.
With ailment chance and duration, that one hit can freeze, shock and ignite at once:
three ailments feeding from one attack, plus any "damage vs affected enemies" or
ailment-effect scaling on top.

---

## 3. Spirit-Charge Burst Stacking

**Anchor:** **Lightpoacher**

**Graph path:**
```
Lightpoacher --grants--> chance to gain a Spirit Charge on Kill
Lightpoacher --grants--> trigger Spirit Burst on skill use if you have a Spirit Charge
Lightpoacher --grants--> Physical Damage added as EACH Element per Spirit Charge
```

**Facts:** all confirmed.

**Why it could deal damage:** spirit charges (a niche charge type) each add your
physical damage *as every element at once* — the most multiplicative "per charge"
scaling in the graph. The charges are also consumed into a Spirit Burst on skill
use. A build that gains charges from kills and spends them on a burst gets both the
per-charge elemental added damage and the burst trigger.

---

## 4. Poison Proliferation Knife

**Anchor:** **Bino's Kitchen Knife**

**Graph path:**
```
Bino's Kitchen Knife --grants--> spread Poison to nearby enemies on Kill
Bino's Kitchen Knife --grants--> Damage over Time +%
Bino's Kitchen Knife --grants--> Critical Strike Multiplier +, Critical Strike Chance
Bino's Kitchen Knife --grants--> added Physical Damage (local)
```

**Facts:** all confirmed (the poison-spread is a confirmed unique mechanic).

**Why it could deal damage:** killing a poisoned enemy spreads the poison to the
whole pack — proliferation without a gem. Crits scale both the initial hit and the
poison; the confirmed DoT % further multiplies it. A pack-clearing loop where each
kill re-seeds poison onto the next wave.

---

## 5. Frenzy-Charge Offense + Defense

**Anchor:** **The Blood Dance**

**Graph path:**
```
The Blood Dance --grants--> chance to gain a Frenzy Charge on Kill
The Blood Dance --grants--> Attack and Cast Speed per Frenzy Charge
The Blood Dance --grants--> Damage vs Low-Life enemies per Frenzy Charge
The Blood Dance --grants--> Life Regeneration per Frenzy Charge
```

**Facts:** all confirmed.

**Why it could deal damage:** every frenzy charge is simultaneously attack/cast
speed, "damage vs low life", and life regen. Once you have charges up, you hit
faster and hit low-life enemies harder — the speed multiplier compounds the per-hit
damage, and the regen pays for the aggressive low-life positioning.

---

## 6. Power-Charge Elemental Attacks

**Anchor:** **Auxium**

**Graph path:**
```
Auxium --grants--> Elemental Damage with Attack Skills per Power Charge
Auxium --grants--> Mana Leech from Attack Damage per Power Charge
Auxium --grants--> Chill/Freeze Duration based on Energy Shield
```

**Facts:** all confirmed.

**Why it could deal damage:** power charges are a per-charge *elemental attack
damage* multiplier, plus per-charge mana sustain. The ES-based chill duration ties
your defensive layer to how long enemies stay chilled. Stack power charges and the
same stat is both your damage scalar and your leech source.

---

## 7. Rage→Phys-as-Fire Engine

**Anchor:** **Kaom's Primacy**, fueled by **Kaom's Spirit**

**Graph path:**
```
Kaom's Primacy --grants--> Physical Damage % added as Fire per Rage
Kaom's Primacy --grants--> +1 Maximum Endurance Charges
Kaom's Spirit  --grants--> regenerate 1 Rage per X Life Regeneration
Kaom's Spirit  --grants--> Life Recovery from Regeneration is NOT applied
```

**Facts:** all confirmed.

**Why it could deal damage:** rage is the damage scalar — each point adds physical
as fire — and Kaom's Spirit manufactures rage from life regeneration (converting
your regen into a resource instead of healing). The more life regen you stack, the
more rage, the more fire conversion; endurance charges on the axe add defense on
the same item.

---

## 8. Spider-Web DoT Amplifier

**Anchor:** **Fenumus' Weave**

**Graph path:**
```
Fenumus' Weave --grants--> added Chaos Damage per Spider's Web on enemy
Fenumus' Weave --grants--> Hit and Ailment Damage vs enemies with >= 3 Spider's Webs
Fenumus' Weave --grants--> Attack and Cast Speed +%
Fenumus' Weave --grants--> grants Aspect of the Spider
```

**Facts:** all confirmed.

**Why it could deal damage:** each web on an enemy adds chaos damage to your hits,
and crossing the 3-web threshold flips on a further hit-and-ailment multiplier. The
debuff both adds flat chaos and unlocks a % amplifier — a stacking ramp that pays
off once the target is fully webbed.

---

## 9. Warcry-Gated Elemental Amplifier

**Anchor:** **Debeon's Dirge**

**Graph path:**
```
Debeon's Dirge --grants--> Elemental Damage +% if you've used a Warcry recently
Debeon's Dirge --grants--> Movement Speed +% if you've used a Warcry recently
Debeon's Dirge --grants--> Warcries Knock Back Enemies
Debeon's Dirge --grants--> added Cold Damage (local)
```

**Facts:** all confirmed.

**Why it could deal damage:** a warcry becomes a damage switch — after using one,
your elemental damage and movement speed both spike. The knock-back warcries keep
enemies in the sweet spot, and the local added cold makes the amplified elemental
side meaningful. A "shout then strike" cadence build.

---

## 10. Minion-Sacrifice Chaos Bow

**Anchor:** **Spinehail**

**Graph path:**
```
Spinehail --grants--> Physical Damage % added as Chaos
Spinehail --grants--> sacrifice a Minion to fire additional Arrows
Spinehail --grants--> Minion Damage +%
Spinehail --grants--> added Physical Damage (bow), Attack Speed +%
```

**Facts:** all confirmed.

**Why it could deal damage:** it converts physical to chaos (bypassing elemental
resistance) and then *spends your minions as extra arrows* — minion investment
becomes bow volley power. The minion-damage stat feeds the minions you sacrifice,
and the phys→chaos conversion makes every arrow hit a resistance-bypassing element.
A minion-and-bow hybrid where your summons are the ammunition.

---

## Ranking (my own judgment, not graph facts)

1. **Damage-Type Rotation Chain** — a full four-step conversion loop ending in chaos; most multiplicative structure
2. **Spirit-Charge Burst** — "per charge × every element" is the largest per-charge multiplier in the set
3. **Rage→Phys-as-Fire Engine** — rage is a direct damage scalar with a confirmed generator
4. **Spider-Web DoT Amplifier** — flat added damage plus a stacking % unlock
5. **Phys→Fire + Random-Element Bow** — one hit, three ailments
6. **Frenzy-Charge Offense + Defense** — speed × damage compounding
7. **Poison Proliferation** — self-contained pack clearing
8. **Power-Charge Elemental Attacks** — clean per-charge scaling
9. **Warcry-Gated Amplifier** — trigger-cadence build
10. **Minion-Sacrifice Chaos Bow** — most fragile synergy (needs minion economy)

## Method note

Seeds came from `get_start_seed` across multiple node types and seeds; each anchor
was explored with `get_neighbour` (depth 1–2 over `unique_modifier_association`,
`modifier_grants_stat`, `stat_scales_with`). Only confirmed edges and stat nodes are
cited. Scaling stats whose granting modifier has no confirmed owner (e.g. the
`stat_scales_with` operand stats like `attack_damage_+%_per_500_maximum_mana`) were
deliberately NOT used as anchors. Nothing was modified.
