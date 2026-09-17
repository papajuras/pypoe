---
name: scaling-discovery
description: Identify, validate, and pursue genuine scaling axes during PoE build discovery with the santa-maria knowledge base. Primary target: quadratic or higher-order scaling — the same investment in X entering the same output through multiple interacting paths. Use when exploring the KB graph for build concepts, evaluating scaling relationships, or deciding whether a promising interaction warrants deeper exploration.
metadata:
"opencode/autoinvoke": false
---

# Skill: Scaling Discovery

Use during build discovery to identify meaningful scaling, validate it, and decide what deserves deeper exploration.

## 1. Scaling axis

A scaling axis is a variable **X** such that increasing X improves an important build output through an explicit game mechanic:

**increase X → mechanic uses/converts X → output improves**

The output must change **because X changes**. A generic bonus or multiplier is not an axis; a multiplier matters when a scaling axis feeds it.

## 2. Primary target: quadratic or higher-order scaling

The discovery target is X entering the **same meaningful output** through two or more interacting paths:

**X → A, X → B, A × B → output** → X²
**X → A, X → B, X → C, A × B × C → output** → X³

Ladder:

- **single-use** — X → A
- **multi-use** — X → A, X → B, independent outputs (e.g. damage + defense)
- **quadratic / cubic+** — X feeds ≥2 (≥3) interacting inputs of one output

Rules:

- **Multi-use is not double dip.** Damage + defense from X is multi-use; two independent consumers do not interact.
- **Consumer count is not evidence of quadratic scaling.** A fan-out X → A, B, C is multi-use until effects derived from X actually interact toward one output.
- **Degree ≠ practical strength.** A cubic term with a tiny coefficient or hard limit can be weak; never rank candidates by degree alone.
- When claiming, name: X; each path from X; the common output; the combining mechanic; the degree. If any path is unconfirmed, label it a **quadratic/higher-order hypothesis**, not confirmed scaling.

## 3. Validate

For any candidate establish **X → mechanism → output**; for higher-order candidates, establish every path and the interaction. Prefer explicit KB/graph relationships. Do not promote to confirmed when only one side of the causal chain is supported, and do not infer a multiplicative interaction merely because two effects share a stat.

## 4. Explore for the second path

A valid X → output is a **lead**, not a build. Look for:

- another mechanic that scales with X;
- conversion of X into a quantity affecting the output;
- a multiplier whose input X also increases;
- another axis Y interacting with X;
- feedback (X affecting the output more than once);
- generators/enablers that make the interaction practical;
- a coherent defensive layer where appropriate.

An extra node matters only when it adds another interacting layer. Depth for its own sake is worthless.

## 5. Explore proportionally

A branch merits further exploration when there is evidence of:

1. a meaningful scaling axis X;
2. credible generation of X;
3. a meaningful output;
4. a second path by which X reaches that output — or a plausible mechanic that could make such a path interact with the first.

Give particular attention to candidates where the second path would establish X² or higher. If the axis is isolated and no plausible continuation is visible, move on. No arbitrary minimum number of hops.

## 6. Small agenda

Park at most a few candidates, each with one **concrete revisit reason**: a possible second X-path, an unconfirmed multiplier, an unexplored consumer, a pending validation. The agenda is a memory aid, not an algorithm — no scores, quotas, or parallel exploration; never manufacture candidates; drop a parked branch when its reason dies. Before abandoning the current branch, check whether a parked candidate has a more promising unexplored path toward higher-order scaling.

## 7. Roles

**scaling axis** (what the build scales with) · **generator** (creates X) · **consumer/converter** · **enabler** · **multiplier** · **defense**. They interact but are not interchangeable: a generator is not automatically an axis, a multiplier is not a second path, a second consumer is not a double dip.

## 8. Build validation

Graph reasoning and build validity are separate concerns. Commit components via `santa-maria/tools/phase7_build_validity.py`:

**propose component → validate_addition → VALID: commit / INVALID: reject (use the conflict reason to steer alternatives) / UNKNOWN: do not assume valid**

Validate only components actually being added; keep committed state explicit, not in conversational memory; finish with `validate_build`. VALID means only the implemented deterministic constraints passed — never invent missing constraints or move feasibility rules into the semantic graph.

Classify each committed item: core scaling component · scaling enabler · mechanic converter · synergy component · **slot filler** (mark explicitly when chosen only for a slot constraint; a rare may be preferable) · generic placeholder. Prefer builds whose non-defensive components participate in the scaling architecture.

## 9. Evidence discipline and decision

At each promising discovery ask:

> Does increasing X merely provide multiple independent benefits, or does X enter the same output through multiple interacting paths?

Classify the evidence: **isolated → multi-use → quadratic candidate → quadratic confirmed → cubic+ candidate/confirmed**.

Do not manufacture causal links, multiplicative interactions, or higher-order behavior. X appearing in two places is not X² unless both dependencies provably feed the same meaningful output. Partially known relationships stay hypotheses. Never substitute general game knowledge for missing KB evidence when claiming a relationship was discovered from the KB. **Do not force a quadratic interpretation.**

## Objective

Find build concepts where a coherent investment in X produces quadratic or higher-order scaling:

**X → A, X → B, A × B → output** (and analogues)

Multi-use, compound, generator-spender, and deep architectures matter only as steps toward such interacting dependencies. **The primary target is genuine quadratic-or-higher scaling, not many uses of the same stat.**
