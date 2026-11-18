---
name: build-output
description: Formats discovered Path of Exile builds into human-readable, auditable build sheets. Every build is rendered as a separate table with complete modifier lists, bolded synergy-critical mods, human-readable influenced modifiers, and explicit preservation of UNKNOWN/unavailable information. Use whenever a research agent presents a discovered build, synergy, or build candidate to a human.
metadata:
  "opencode/autoinvoke": false
---

# Skill: Build Output

Convert a validated or proposed PoE build into a compact, human-readable build sheet. The output is for **human inspection and auditing**, not further machine reasoning. The build must be understandable without reading raw JSON, node IDs, or API responses.

**One build = one Markdown table.** Never merge builds. Never invent or infer a modifier, gem property, ascendancy, slot, influence, or compatibility fact. UNKNOWN stays visibly UNKNOWN.

## Structure

### Build N — <short descriptive name>

One or two sentences on the central interaction, then:

| Slot | Item / Gem / Passive | Details |
| ---- | -------------------- | ------- |

Only render rows that actually exist in the build — no invented slots.

- **Equipment**: `Details` = the **complete relevant modifier list** (see completeness below).
- **Gems**: exact name, level/quality if known, established support relationships.
- **Ascendancy**: name + selected notables. Exactly one per build — never guess from a passive name; if the source does not establish it, write **Ascendancy: UNKNOWN**.
- **Jewels**: only if part of the build; never assign an unknown socket position.

## Modifiers

- Complete list means: every modifier in the build/item representation — explicit, implicit, crafted, fractured, enchantment, influenced. Do not omit generic mods just because they are not the discovery target; do not manufacture mods absent from the API result.
- Preserve the source's human-readable wording; do not paraphrase in a way that changes mechanical meaning.
- **Bold** the modifier(s) that establish this build's key interaction — bolding marks why the item matters *here*, not global importance. Bold all members of a joint interaction.
- If the source distinguishes modifier categories, preserve the distinction when useful.

Influenced modifiers: render the human-readable text with the influence when known —
`**+X% to Critical Strike Chance** *(Hunter)*` — never an internal ID alone (`Mod: Hunter_...`),
never an influence inferred from wording. If the readable form is unavailable, mark the
modifier **unresolved** rather than inventing it.

## Availability & validation

- Availability is 4-valued: available (normal), unavailable (marked), conflict (marked), unknown/null (**UNKNOWN**). Never silently substitute another item.
- Status line near the table: **VALIDATED** (passed available checks — no stronger claims than the validator makes), **CANDIDATE** (discovery not fully validated). **REJECTED** builds are not rendered unless asked.

## Explanation & evidence

After each table:

**Why it works** — 2–5 plain sentences covering: initiating mechanic; carrier/consumer; the scaling or conversion relationship; why these components belong together. Only mechanics present in the discovery evidence.

**Evidence** (when the research result exposes it) — compact arrows, human-readable names first, node IDs parenthetically when useful for auditing:

- `<item/stat>` → `<relationship>`

Never dump raw API JSON unless asked.

## Multiple builds

Same structure per build, same column layout where practical, own descriptive title each — kept visually comparable.

## Priority when dense

Exact item name → complete modifier list → bold key mods → ascendancy/passives → availability/validation → concise explanation. Completeness wins over brevity. No decorative prose. The reader's question: *"What exactly is this build using, and which exact mechanics make the discovery work?"*

## Anti-hallucination (hard rules)

The output layer never repairs incomplete research:

- UNKNOWN → output UNKNOWN. Unavailable → output unavailable. Unresolved → output unresolved.
- Truncated evidence → never present as exhaustive.
- Never fill missing mods from memory, infer a hidden influence, invent a typical-for-item modifier, or turn an approximate description into an exact modifier.

The rendered sheet is a faithful representation of the research result, never a reconstruction from general game knowledge.
