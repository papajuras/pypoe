# Serle's Masterwork — Disabled/Unavailable Item Fix (2026-09-16)

## 1. Diagnosis

**Where Serle's comes from:** RePoE `uniques.json` key 1458 (name/item_class/visual only —
**no availability field**) + PoB block `data/pob/Uniques/mace.json` whose header carries
`Source: No longer obtainable` (League: Settlers of Kalguur, then delisted).

**Authoritative signal:** the PoB unique blocks' `Source:` header line.
`Source: No longer obtainable` = disabled/unavailable content. Absence of a Source line =
normal obtainment (PoB omits it for standard drops). Distribution: 168 distinct unique
names marked unavailable (82 of them jewels; e.g. Bisco's Collar, Hrimburn,
The Goddess Unleashed, Ngamahu Tiki).

**What the KB preserved:** nothing — `extract_uniques` (extract_nodes.py:615) copies only
RePoE fields; the PoB block text is used for modifier template resolution
(`load_pob_blocks`), never surfaced. So the flag existed in source data, was dropped at
extraction, and no build-validity layer consumed it. Serle's validated as a normal item.

**Layer classification:** KB representation gap (flag dropped) + missing build-validity
filter. NOT a source-data problem (signal present), NOT discovery behaviour.

## 2. Fix (no graph changes; raw data untouched)

- `phase6_api.py` now owns `_pob_availability()`: lazy map name →
  `available | unavailable | conflict` parsed from `data/pob/Uniques/*.json` (Source line
  within first 6 lines). `get_start_seed` entries for UniqueItem seeds expose
  `availability` (`'unavailable' / 'available' / None`); None = no PoB block → not
  checked (83/1382 RePoE unique names lack blocks — PoB coverage gap, absence is NOT
  evidence of unavailability; e.g. Demigod's Eye).
- `phase7_build_validity.py` reuses that map: `validate_build` gains `availability_checks`
  — any `unavailable` item → **INVALID** ("Source: No longer obtainable — disabled/
  unavailable content, cannot be a build component"); `conflict` (mixed sources) →
  UNKNOWN, never guessed. `validate_addition` attributes rejection to the candidate.
  `checked` list gains `item_availability` (appended last); LIMITATIONS updated.
- Graph: nodes/edges/payloads untouched (sha256-stable in tests).

## 3. Tests

New `tools/tests/test_availability.py` (6):
1. Serle's detected unavailable + build INVALID;
2. `validate_addition` rejects and attributes ("candidate ... no longer obtainable"),
   state unmutated;
3. normal available unique (Soul Tether) VALID; mixed list poisoned → INVALID;
4. **no graph mutation:** nodes.db/edges.db sha256 identical around validate calls;
5. API seeds expose availability (Serle's=unavailable, Soul Tether=available,
   Demigod's Eye=None);
6. CLI `build Serle's Masterwork` → invalid.

Updated `tools/tests/test_build_validity.py`: `checked` expectation now includes
`item_availability`; `checked[-1] == 'gem_support'` → `'gem_support' in checked`
(contract grew, check semantics preserved).

**Results:** test_availability 6 PASS; regressions test_build_validity,
test_build_feasibility, test_consumer_projection, test_phase6, test_phase6_passive_info,
test_build_validity_ascendancy, test_variants — ALL PASS.

## 4. Broader impact

- 168 unique names affected (out of 1300 PoB-covered): mostly older-league jewels,
  some weapons/armor; examples above. Fix generalizes cleanly — one Source-line rule,
  no per-item logic.
- Run-1 discovery conclusions NOT invalidated: all three committed builds used
  available items (Roth's Reach, The Gluttonous Tide, The Green Dream, Soul Tether —
  all `available`). A9's Conqueror's Longevity (already dismissed as "no scaling core")
  is additionally `unavailable` — dismissal now stronger, conclusion unchanged.

## 5. Verification summary

- Files changed: `tools/phase6_api.py`, `tools/phase7_build_validity.py`,
  `tools/tests/test_availability.py` (new), `tools/tests/test_build_validity.py`
  (2 assertions).
- DB/schema/graph data: **unchanged** (digest-proven).
- Availability signal: PoB `Source: No longer obtainable` header, name-keyed, fail-closed
  on conflicts; missing PoB block = not checked (documented limitation).
- Serle's Masterwork is now prevented from being a valid build component at
  validate_build, validate_addition, CLI, and is labeled at seed selection.
