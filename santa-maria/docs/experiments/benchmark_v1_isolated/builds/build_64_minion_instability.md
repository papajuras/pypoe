# Build 64 — Minion Instability Necromancer (Explosive Minion Spam)

Status: **VALIDATED** (passive layer); gem state UNKNOWN (weapon context skipped for Absolution)

Central interaction: the Minion Instability keystone (minions detonate on death) becomes a spam engine with Absolution's transient minions — and the KB shows the keystone has 7 acquisition sources, an unusually broad multi-source footprint for a keystone.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Keystone | **Minion Instability** (passive:minion_instability1133) | **keystone_minion_instability** |
| Ascendancy | Necromancer — Commander of Darkness (passive:AscendancyNecromancer12) | ascendancy anchor |
| Skill | Absolution (gem:Absolution) | transient minion explosion engine (minion-tag gem family, 79 members) |
| Item (uncommitted) | KeystoneMinionInstabilityUnique__1 carrier | a unique carries the keystone stat; **its association edge exists but the unique's identity was not individually probed this session** — one of the 6 mod sources |
| Sources (fact) | Hellscape upside / Recombinator 'of the Sentinel' / Sanctum special corruption / weapon-tree / monster mod | the 6 non-tree acquisition routes for the keystone |

**Why it works** — Minion Instability converts minion *deaths* into fire damage; transient minion generators (Absolution's converts) make death rate the scaling variable. The KB models the keystone acquisition itself as the multi-source axis: the same keystone stat is granted by 6 item-system mods plus the tree keystone — a recombination/corruption-driven entry point that is unusual among keystones.

**Evidence**
- stat:keystone_minion_instability ← mgs=6 (HellscapeUpside, KeystoneMinionInstabilityUnique__1, MonsterMinionInstability, RecombinatorSpecial 'of the Sentinel', SanctumSpecialCorruption, WeaponTree) + pgs=1 (tree keystone)
- gem:Absolution (+AltX, Vaal) resolved in-session; Absolution appears as a minion-stat carrier in this session's BFS chains
- minion-tag domain: 79 minion gems, 22 minion-tagged mods (tag view of this session)

Validation: `validate_build{passives:[Minion Instability, Commander of Darkness]}` → **valid**. With gem:Absolution added → **unknown** (weapon context not determined). No ascendancy conflict.
