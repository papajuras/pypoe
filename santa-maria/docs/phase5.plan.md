# Phase 5 — Relationship Graph

## 0. TEST — TDD first

Before implementation, define expected relationships and tests.

### Baseline tests

* `Strength → FireMin/FireMax → relevant rare modifiers`
* `Endurance Charge → FireMin/FireMax → relevant modifiers`
* `Hopeshredder → relevant scaling/mechanics`
* `Unique ↔ rare modifier` through a shared mechanic/stat

### Adversarial integration test

Expected structural path for:

* `Whispers of Infinity`
* `Intelligence stacking`
* `Lightning damage per Intelligence`
* `Unholy Trinity`

The graph does **not** need to discover the quantitative hypothesis about damage volatility / changing highest damage type.

It **must** contain and make traversable all structural relationships required to reach the combo.

---

## 1. Edge contract

Define:

* allowed relationship types
* allowed source/target node types
* edge direction
* provenance/evidence requirements
* confidence/status where source evidence differs in strength
* explicitly forbidden relationships

Core rule:

> Phase 5 materializes relationships supported by source data and approved deterministic rules. It does not invent mechanics or perform independent semantic inference.

---

## 2. Deterministic edge extraction

Build the edge extractor from `nodes.db` plus retained raw/lookup data.

Priority relationships:

* Modifier ↔ Stat
* Modifier ↔ ModifierGroup
* Modifier ↔ Tag
* Passive ↔ Stat
* Gem ↔ Stat
* UniqueItem ↔ Modifier / Passive
* other approved structural relationships

No semantic inference.

---

## 3. Mechanic / scaling bridges

Add approved relationships that allow traversal through the graph:

```text
scaling source
    ↓
mechanic / stat
    ↓
modifier
    ↓
item / passive / gem
```

Add mechanic-to-mechanic bridges only where they are deterministically supported by the data.

Avoid generic shared-tag explosions where a tag creates thousands of meaningless relationships.

---

## 4. Unique resolution edges

Materialize only safe associations:

* methods 1 / 3 / 4 → edges
* method-2 candidates → **not confirmed edges**

Method-2 text matches remain candidates until explicitly validated.

---

## 5. Graph validation

Independently validate:

* edge counts
* duplicate edges
* orphan edges
* node IDs
* edge directions
* provenance
* determinism
* allowed relationship types
* absence of semantic inference

Most importantly:

> Verify that the predefined test paths actually exist in the resulting graph.

---

## 6. Adversarial discovery validation

Do not only test:

> "Did the extractor produce what we told it to produce?"

Also test:

> "Can the graph actually traverse from useful seeds to the expected synergies?"

### Required adversarial test

```text
Whispers of Infinity
        ↓
Intelligence
        ↓
Lightning damage per Intelligence
        ↓
Lightning damage
        ↓
Unholy Trinity
```

And from Unholy Trinity:

```text
Unholy Trinity
    ↓
Lightning
Physical
Chaos
```

The graph is **not** expected to encode the final reasoning step:

```text
damage roll variance
        ↓
highest damage type can change between hits
        ↓
Unholy Trinity resonance interaction
```

That is reasoning performed later over the retrieved graph context.

---

## 7. Phase 5 exit criterion

Phase 5 is complete only when:

> The graph is a deterministic, provenance-backed representation of the approved relationships and passes both unit tests and adversarial discovery tests.

Only then proceed to Phase 6.

---

# Phase 6 — Minimal Graph API

Initial API surface should contain only:

```text
get_start_seed(filters[])
get_neighbour(depth, filters[])
```

No broader API should be designed until actual discovery use demonstrates a need for it.
