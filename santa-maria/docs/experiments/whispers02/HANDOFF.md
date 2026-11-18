# HANDOFF — Whispers of Infinity thread (whispers02) → next session

**Date:** 2026-09-17 (evening) · **Status:** ✅ **RESOLVED 2026-09-18.** The surgical rollback was executed, and the user replaced the planned API-filtering architecture with a **live-only KB invariant**: staleness is decided at build time (`extract_nodes` live-gate), the API does no filtering, and what lands in the KB is live by definition. Vestigial (method 6, alt-quality implicits) is retired from the KB until separately modelled — that future modelling is the remaining open thread. Sections below are the historical record from the pause point; the "Decisions" and "Next steps" have been superseded as described here.

## 0.1. What was actually done (2026-09-18)

1. **Surgical rollback** of the entire availability layer (`_availability_overrides`, `availability_reason`, `EXCLUDE_UNAVAILABLE`, `include_unavailable` kwargs/CLI/meta, override-reason validator text, test hunks); `data/availability_overrides.json` was already gone. Alt-asc exclusion preserved untouched.
2. **Live-only gate** in `extract_nodes.resolve_unique_all`: method-6 emission removed entirely; m1/m4 targets are emitted only when the mod text is token-subsequence-contained (number-preserving, formatting-insensitive: decimals canonicalized, ranges ordered, `[id|display]` collapsed, `reduced`==`increased`, trailing-s stripped) in a current-variant block line; blockless uniques carry no association targets. Drop counts reported by the build (`m1_blockless: 104, m1_text: 801, m4_text: 1`).
3. **Acceptance gates all met**: 0/4135 m5-resolved pairs would be flagged; MV per-50 present (`carriers` → unique:713), MV per-100 Divergent absent; Taryn's stale line and Goldrim's pre-buff text absent; Goldrim current res present; 98 blockless uniques carry zero association targets. Pinned in `tools/tests/test_live_gate.py` (6 tests).
4. **Mod `text` exposure** in phase8 (`resolve` rows, `carriers` rows, `meta.subject_text`) + SKILL.md rules: never render mod ids as prose; live-only KB documented.
5. **Variant membership degraded as predicted**: `confirmed_edge` 768→58 (m6 retirement), displaced to source-derived classes; `test_variants.py` re-pinned (Foulborn mutated-mod KB parity still holds).
6. **whispers02 REPORT.md re-amended**: all "removed" claims retracted; Build 3 back to CANDIDATE with real per-50 text; Build 2 restored to its original committed shape; both re-validated (`unknown` = jewel limitation only); sole-carrier facts re-verified against the rebuilt KB.
7. Full rebuild via `tools/run_pipeline.sh`; 17 fast suites + new gate test green (`test_stat_classification` stays skipped/slow).

## 0. Read first — corrections that invalidate earlier claims

Earlier in this thread (and in some project memory entries) I wrongly claimed:

1. ~~"Memory Vault was removed from the game"~~ — **FALSE.** Memory Vault (`unique:713`) is in the game. Its current PoB block (post-3.16 rework) grants *"1% increased Armour per 50 Reserved Mana"*.
2. ~~"The Divergent per-100 variant is the removed pre-3.16 version"~~ — **FALSE.** Per user: the `Divergent*` mods are **vestigial versions of additional implicits you can put on items** — an **active** game mechanic. Out of scope for this discussion. Mod-level liveness is **UNKNOWN from the dump** and must never be claimed.
3. The wording **"Gain Armour equal to Mana Reserved"** (whispers02 Build 3, and my id→prose renders throughout) **exists nowhere as mod text** — I fabricated it from the mod **id** `GainArmourEqualToManaReservedUnique__1`. The id name is a fossil; the mod's actual text/stat are the per-50 form. Only real "Armour equal to … Reserved Mana" mods are the Animal Charm auras.

Root cause of the whole thread: the public API doesn't expose mod `text`, so ids got rendered as prose. Any fix must close that gap.

## 1. Verified data facts (re-derive nothing tomorrow)

- Corpus (`data/repoe/mods.json`) mod family:
  - `GainArmourEqualToManaReservedUnique__1` → text **"1% increased Armour per 50 Reserved Mana"**, stat `gain_X%_armour_per_50_mana_reserved` — **current** on Memory Vault (method-5 resolved vs PoB block).
  - `DivergentGainArmourEqualToManaReservedUnique__1` → text **"1% increased Armour per 100 Reserved Mana"**, stat `…_per_100_…`, `required_level: 68` — **zero** of 1307 current blocks render it; only trace is `Vestigial.json` → Memory Vault. **Active mechanic (alt-quality implicits) per user — do NOT label historic.**
  - No mod text contains "Gain Armour equal to Mana Reserved".
- `data/pob/Vestigial.json`: **472/472 keys** are `Divergent/Anomalous/Phantasmal*` (alt-quality implicit twins). Method 6 (Vestigial ownership) is therefore **not** a "historic" signal by itself.
- PoB blocks (`data/pob/Uniques/*.json`, 1307 blocks): versioned variants (`Variant: Pre X / Current` + `{variant:N}`); `extract_nodes.parse_unique_block` keeps max variant = current. 170 blocks carry `Source: No longer obtainable` (item-obtainability signal, `_pob_availability`). 633 blocks have no `Source:` line — normal (absence = no drop doc, e.g. Goldrim, The Anvil).
- Association edge population (`resolved`, methods 1/4/5/6): **7314** edges = m1 2744, m4 10, m5 4135, m6 425.
- Detector probe numbers (combined rule: no per-line range-normalized text containment in current block AND no builder m2/m5 evidence, text exists, block parsed): **672 edges / 642 pairs** flagged, 314 evidence-spared. **FP on the 4135 m5-resolved pairs: 263 → 39** after per-line + range-order fixes (residual class: "8.00/sec" vs "8/second" formatting). **CAVEAT: this set includes alt-quality-implicit (Vestigial) associations that are ACTIVE mechanics — the set needs semantic re-derivation, see §3.**
- Unverified buckets (must stay UNKNOWN): 98 uniques without parsed block; 2685 textless unique-domain mods; 11 timeless-jewel texts with literal `Historic` trailer (flavor line, never a verdict signal).
- Example proof of association-staleness that IS real: Taryn's Shiver "(50-60)% increased Spell Damage" = `{variant:2,3,4}` line, stripped from Current variant; Goldrim "+20% all res" = pre-buff text (current block: 30-40%).

## 2. Repo state RIGHT NOW (uncommitted — handle carefully)

**Surgical rollback required (my wrong-granularity work this session):**
- `santa-maria/tools/phase6_api.py` — availability overrides loader (`_availability_overrides`, `availability_reason`), `EXCLUDE_UNAVAILABLE` + seed/neighbour filtering + `meta.excluded_unavailable`. **Do NOT `git restore` this file — the alternate-ascendancy exclusion (earlier session, also uncommitted) lives in the same file and must be preserved.** Reverse only the availability-layer hunks.
- `santa-maria/tools/phase8_research.py` — `include_unavailable` kwargs on resolve/carriers + meta fields.
- `santa-maria/tools/research.py` — CLI `--include-unavailable` flags + docstring.
- `santa-maria/tools/phase7_build_validity.py` — `_availability_reason` alias + override-reason text in `_item_availability_checks` + one LIMITATIONS line.
- `santa-maria/tools/tests/test_availability.py`, `tests/test_phase8_research.py` — my edits (override tests, Corona Solaris default-excluded expectations).
- `santa-maria/data/availability_overrides.json` — **delete** (contains the false "Memory Vault unavailable" entry).
- `.opencode/skills/discovery-api-usage/SKILL.md` — remove the "Unavailable-unique exclusion — default ON" section I added.

**Keep from this session:** whispers02 run artifacts (`santa-maria/docs/experiments/whispers02/REPORT.md` — needs re-amendment, see §4), memory entries (one contains false claims — corrected via new memory + this file).

**Pre-existing uncommitted work (NOT ours, preserve):** alt-asc exclusion (phase6_api etc.), `AGENTS.md`, `scaling-discovery/SKILL.md`, `seed_corpus_v1/build_corpus.py`, `test_build_validity_ascendancy.py`, `test_phase6_passive_info.py`, benchmark dirs, `.opencode/plans/`.

## 3. Decisions taken + architecture direction (as of pause)

- **User decision:** full surgical rollback of the item-availability layer (it was built on a misdiagnosis). Manual override lists **rejected** — "there is a deterministic way to find which mods are historic".
- **Pipeline rebuild is cheap** (<1 min per user) — rebuild cost must not influence architecture.
- **Precedent to follow:** `extract_nodes.unique_filter_mod` (:380) — legacy/dummy stat ids (`old_do_not_use_*`/`dummy_*`, 88 mods / 456 nodes) are filtered at the **build-time resolver** (candidate generation), annotated at stat layer (`flags`, :297), mirrored at API variants layer (`phase6_api.foulborn_ok`, :389). Data is flagged/retained, never silently deleted.
- **Final architecture shape (pending tomorrow's re-derivation):**
  1. Keep `_pob_availability` + validator rejection (item-obtainability class) — unchanged; semantics documented as PoB attribution, not present-day fact.
  2. **Mod `text` exposure** in phase8 resolve/carriers rows (root fix for the id-as-prose hazard) + hard rule in SKILL.md: never render mod ids as text.
  3. Association-level staleness detection **at build time** (extract_nodes resolver owns all sources; verdict stored on resolved_targets / edge payload, data retained), API default-filtering with meta counts + opt-in kwarg — same never-silent pattern as alt-asc.
  4. **OPEN (tomorrow):** the verdict taxonomy must distinguish at least: (a) legacy item-version association (Taryn's Shiver-style), (b) **alt-quality-implicit / Vestigial associations — ACTIVE mechanics, must stay** (the 472-key class!), (c) genuinely-removed. Text-truth alone does not separate (b) from (a)/(c). The 642-pair probe set must be re-derived under this taxonomy before any filtering ships. Mod-level liveness stays UNKNOWN, always.
- **whispers02 re-amendment (pending):** remove all "item removed" claims; Build 2 restores Memory Vault helmet; Build 3 back to CANDIDATE with real-text details (per-50 mod; drop the fabricated wording); re-validate both builds (states + `research.py validate`).

## 4. Suggested next steps (tomorrow) — ✅ DONE 2026-09-18 except the deferred Vestigial modelling

1. ~~Surgical rollback~~ ✅ 2. ~~Class-B taxonomy~~ ✅ (user decision: live-only KB, no API filtering, Vestigial deferred) 3. ~~Build-time verdicts~~ ✅ (live-gate shipped, gates met) 4. ~~whispers02 re-amendment, memory, SKILL.md~~ ✅.
5. **REMAINING (separate session): Vestigial/alt-quality modelling** — the 472-key alt-quality implicit twins (Divergent/Anomalous/Phantasmal) are an ACTIVE mechanic with no KB representation now. Needs its own model (e.g. a dedicated variant-implicit edge family), not a bolt-on to `unique_modifier_association`.

## 5. Suggested skills for the next agent

- `discovery-api-usage` — **mandatory** before any KB/graph work (public-API-only rule, API-gap protocol, meta-count duties).
- `build-output` — if amending/regenerating build sheets (anti-hallucination rules: text unresolved → mark unresolved; never id-as-prose).
- `ponytail` — mode was active all session (lazy/minimal edits; `ponytail:` comments for deliberate shortcuts).
- `scaling-discovery` — only if resuming build discovery.

## 6. Key file references

- Resolver/methods: `santa-maria/tools/extract_nodes.py` (`parse_unique_block` :396, `resolve_unique_all` :421, `unique_filter_mod` :380, `norm` :35)
- Edge extraction: `santa-maria/tools/phase5_extract_edges.py` (:203 `ext_unique_modifier_association` — methods 1/4/5/6, `status=='resolved'` only)
- Availability: `santa-maria/tools/phase6_api.py` `_pob_availability` (reads `Source:` headers); validator: `phase7_build_validity.py` `_item_availability_checks`
- Research API: `santa-maria/tools/phase8_research.py`, CLI `research.py`
- Run artifacts: `santa-maria/docs/experiments/whispers02/REPORT.md` (contains the false "removed" amendment — fix, don't trust)
- Pipeline: `santa-maria/tools/run_pipeline.sh` (nodes.db ← extract_nodes, edges.db ← phase5; rerunnable)
