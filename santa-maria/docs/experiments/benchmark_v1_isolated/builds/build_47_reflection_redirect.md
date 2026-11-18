# Build 47 — Commandment of Reflection + Spiritual Aid (Minion-Damage Redirect)

Status: **CANDIDATE** — gem + passive layer; final state UNKNOWN (weapon context skipped for the enchantment gem).

Central interaction: the reflection sentinel is a minion; minion-damage investment is redirected to the player through the "minion damage also affects you" family — one scaling axis, two consumers (your hits and the sentinel's).

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Helmet enchant | **Commandment of Reflection** (gem:EnchantmentOfReflectionWhenHit4) | **active_skill_minion_damage_+%_final**; minion_damage_+%; minion_maximum_life_+%; number_of_monsters_to_summon; cast_when_hit_% — summons the Reflection sentinel when hit |
| Keystone | **Spiritual Aid** (passive:player_and_minion_notable2240) | **minion_damage_increases_and_reductions_also_affects_you** (the redirect consumer) |
| Ascendancy | Necromancer — Commander of Darkness (passive:AscendancyNecromancer12) | ascendancy anchor (aura-ally synergy secondary) |
| Gloves (veiled, marked: slot filler) | Catarina's veiled minion-damage-also-affects-you | 1 of 2 mod carriers of the redirect stat |
| Gear (rare, marked: slot filler) | minion_damage_+% mass | 328-mod carrier group seen at depth 2 in this session |

**Why it works** — In the KB, `minion_damage_+%` is linked by stat-mechanic *operand* edges to the redirect stats (`additive_minion_damage_modifiers_apply_to_you_at_%_value` and its 150% variant, `minion_damage_increases_and_reductions_also_affects_you`) — the mechanic layer explicitly models minion-damage investment flowing to the player. Spiritual Aid is one of only 2 carriers of the redirect stat, making it the linchpin; the Commandment sentinel gives the minion axis an on-hit trigger that does not require active summoning. KB fact: `MinionDamageAlsoAffectsYouUnique__1` has **no unique association** — the unique-anchor for the redirect is unresolved in the KB.

**Evidence**
- gem:EnchantmentOfReflectionWhenHit4 → minion_damage_+% (stat_mechanic_operand → redirect stats; stat_mechanic_relation → mechanic:minion)
- mechanic:minion: 200 related stats (truncated) — redirect/consumer/effect/immunity roles
- stat:minion_damage_increases_and_reductions_also_affects_you ← 1 mod (Catarina's) + 1 passive (Spiritual Aid)
- stat:additive_minion_damage_modifiers_apply_to_you_at_%_value ← 0 mod carriers (payload-linked only — recorded)

Validation: `validate_build{gems:[EnchantmentOfReflectionWhenHit4], passives:[Spiritual Aid, Commander of Darkness]}` → **unknown** (weapon context not determined). Passives-only sub-state valid (keystone + ascendancy mix legal).
