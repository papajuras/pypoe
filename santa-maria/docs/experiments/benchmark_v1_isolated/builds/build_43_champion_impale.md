# Build 43 — Champion Impale Splitter (Splitting Steel)

Status: **CANDIDATE** — passive + gem layer; final state UNKNOWN (no sword committed; the KB holds **no unique with a confirmed impale-chance mod association** — 8 UMA probes returned 0).

Central interaction: Splitting Steel generates impale chance and projectile-splitting; the impale axis is one of the broadest multi-source attack axes in the KB.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Ascendancy | Champion — Armour and Evasion, Impale Chance (passive:AscendancyChampion13) | **attacks_impale_on_hit_%_chance** |
| Weapon | sword (rare, marked: slot filler) | required by Splitting Steel; no unique sword in the KB carries an impale-chance mod with a confirmed association |
| Skill | **Splitting Steel** (gem:SplittingSteel) | **attacks_impale_on_hit_%_chance**; projectile_number_to_split; modifiers_to_number_of_projectiles_instead_apply_to_splitting |
| Skill (alt) | Lancing Steel / Shattering Steel / Double Strike AltX | other impale gem carriers |
| Tree | Impale Chance / Impale Chance and Attack Speed (impale_node_2905/2906/2907), Impale Chance and Physical Attack Damage | 11 passive carriers |
| Gear (rare, marked: slot filler) | Warlord's/Elevated Warlord's impale mods | influence family of the axis |

**Why it works** — Splitting Steel is simultaneously a generator (its own impale chance + split scaling: `projectile_number_to_split`, split-instead-of-projectile modifiers) and a member of a 58-carrier axis (37 mods + 11 passives + 10 gems). Champion's impale notable joins the reflected-hits / armour-while-impaled sub-axes seen on the Champion ascendancy block. The impale reflect mechanic (impaled_debuff_number_of_reflected_hits, 4 carriers incl. Brutal Skewering) is the payoff layer.

**Evidence**
- stat:attacks_impale_on_hit_%_chance ← mgs=37, pgs=11, ggs=10
- gems granting the stat: SplittingSteel (+AltX), LancingSteel (+AltX), ShatteringSteel (+AltX/Royale), ShrapnelBallistaAltX, DoubleStrikeAltX
- stat:impaled_debuff_number_of_reflected_hits ← mgs=2, pgs=2 (Master of Metal [Champion], Brutal Skewering)
- KB fact: AttackImpaleChanceUnique__1/__2 and 6 eldritch-implicit presence mods have **no unique associations** — no unique weapon anchor available

Validation: `validate_build{gems:[SplittingSteel], passives:[Armour and Evasion, Impale Chance]}` → **unknown** (weapon context skipped — Splitting Steel's sword restriction not checkable without a committed weapon). Passive-only sub-state valid.
