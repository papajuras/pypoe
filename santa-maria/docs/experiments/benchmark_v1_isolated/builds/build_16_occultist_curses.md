# Build 16 — Occultist Curse Stacker (Unholy Authority + Whispers of Doom)

Status: **VALIDATED** (passive layer; item/gem layer limited by KB association gaps — see facts)

Central interaction: raise the curse *limit* (multi-source axis), then ignore hexproof so bosses are not exempt — an offensive-control axis with an enabler.

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |
| Ascendancy | Occultist — Unholy Authority | **number_of_additional_curses_allowed**; **ignore_hexproof** |
| Tree | Whispers of Doom (passive:whispers_of_doom1185) | number_of_additional_curses_allowed |
| Amulet (rare/corrupt, marked: slot filler) | `AdditionalCurseCorrupted` carrier | one of 21 mod carriers of the limit axis |
| Boots (influence, marked: slot filler) | Hunter's/Elevated Hunter's additional-curse mods | influence-mod family of the same axis |
| Gems | Curse zone supports (gem:SupportCursePillarTriggerCurses) | gem carriers of the limit axis (2) |
| Cross-class fact | Hexbearer [Hierophant], Vile Imprecations [Necromancer], Occultist [Ascendant] | passive carriers — axis not Occultist-locked |

**Why it works** — The curse limit is a classic multi-source scaling axis: every additional curse applies the entire curse library again; `ignore_hexproof` (4 mods + 2 passives, incl. Devout of Yugul [Guardian]) makes the stack effective against the targets that matter. Damage consumer: each curse's own effect (curse-tag domain: 21 curse gems, 39 curse mods in the tag view).

**Evidence**
- stat:number_of_additional_curses_allowed ← mgs=21, pgs=5, ggs=2
- stat:ignore_hexproof ← mgs=4, pgs=2
- gem:SupportCursePillarTriggerCurses carries the limit stat (gem carrier)

Validation: `validate_build{passives:[Unholy Authority, Whispers of Doom]}` → **valid**. Item layer: no unique association edges were found for the additional-curse mods (Delve/Influence/Maven carriers are non-unique classes) — rare-gear path is the KB-supported route; no unique anchor available in the KB.
