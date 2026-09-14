---
name: scaling-discovery
description: Identify, validate, and pursue genuine scaling axes during PoE build discovery with the santa-maria knowledge base. Use when exploring the KB graph for build concepts, evaluating scaling relationships, deciding whether a promising interaction warrants deeper architectural exploration, or managing several promising branches (parking and revisiting candidates) during discovery.
metadata:
    "opencode/autoinvoke": false
---
# Skill: Scaling Discovery

Use this skill during build discovery to identify meaningful scaling opportunities, validate them, and decide whether a promising interaction deserves deeper exploration.

## 1. Identify the scaling axis

A scaling axis is a variable **X** such that increasing X improves an important build output through an explicit game mechanic.

Think:

**increase X → mechanic uses/converts X → output improves**

The important property is that the build's output changes **because X changes**.

A generic bonus, multiplier, or conditional effect is not automatically a scaling axis.

For example, `20% more damage` is a multiplier, not a scaling axis. It improves a build, but does not identify **what the build scales with**.

## 2. Validate the relationship

When a possible scaling relationship appears, identify:

* **X** — what increases;
* **mechanism** — how X affects something;
* **output** — what becomes better because of X.

Apply this test:

> If I increase X, does the relevant output improve because of X?

Prefer explicit KB/graph relationships over assumptions or general game knowledge.

Do not promote an interaction to a confirmed scaling relationship when only one side of the causal chain is supported.

## 3. Do not stop at the first valid scaling relationship

Finding a valid:

**X → output**

relationship is a **lead**, not necessarily a finished build concept.

When an axis is promising, investigate whether it can participate in a larger interacting system.

Look for graph-supported ways to:

* generate or increase X;
* convert X into another useful quantity;
* make one effect feed another mechanic;
* create or expose another scaling axis;
* find multiple meaningful consumers of X;
* create a feedback relationship;
* find enablers that materially change what the interaction can do;
* connect the core interaction to a coherent defensive layer.

The goal is not to maximize traversal depth.

The goal is to determine whether the initial scaling relationship is part of a **larger build architecture**.

## 4. Generator-spender loops are not sufficient complexity

Do not treat a simple generator → spender/resource-consumer → payoff loop as a deep architecture by itself.

For example:

**generate X → spend X → damage**

is still fundamentally one resource interaction.

A generator and a spender may be important components of a build, but their existence alone does not establish a second scaling system or meaningful architectural depth.

Continue exploring when the interaction exposes additional independent mechanics, scaling axes, conversions, feedback relationships, or other meaningful layers.

Do not reject a build merely because it contains a generator-spender interaction; reject it only when that interaction is effectively the **whole architecture**.

## 5. Look for interacting layers and fan-out

When a promising scaling axis has been identified, actively test whether other mechanics can interact with it.

Particularly valuable structures include:

**X → A → B → output**

**Y → X → output**

**X → output A**
**X → output B**

**X → A → Y → output**

or other structures where one mechanic meaningfully changes the role or value of another.

One structure deserves special attention: a single meaningful axis with **several meaningful consumers or interacting layers** — rather than a single output, or a lone generate → spend → damage chain. When the graph shows hints of such fan-out, treat it as strong evidence that the branch is worth deeper exploration. It is a reason to investigate further, not a requirement every build must meet, and never a criterion a final architecture must satisfy.

An additional node is not automatically an additional layer. The relationship must create a meaningful interaction.

Prefer **interacting systems** over a collection of unrelated bonuses.

## 6. Explore promising branches proportionally

Do not spend the entire exploration budget on every scaling-looking modifier.

A promising branch deserves additional exploration when there is evidence of:

1. a meaningful scaling axis;
2. a credible way to generate, increase, or sustain it;
3. a meaningful consumer or output;
4. a plausible connection to another mechanic or scaling layer — especially signs that several mechanics could consume the same axis.

If the axis is isolated and no useful continuation is visible, move on.

If the graph exposes a plausible continuation, prioritize exploring it before abandoning the branch.

Do not impose an arbitrary minimum number of hops. **Depth is valuable only when it represents additional interacting mechanics.**

## 7. Keep a small exploration agenda

Do not commit permanently to the first promising candidate. When more than one candidate looks promising, it is fine to **park** one and continue with the other.

Keep a small mental agenda of parked candidates — a few at most, with no fixed number. For each parked candidate, hold one **concrete reason to revisit it**: an interaction the graph hinted at but that was never explored, a consumer or layer not yet checked, a validation step still pending.

Revisit a parked branch when:

* the current branch becomes weak, exhausted, or clearly less promising than the parked one;
* or new evidence makes the parked candidate's unexplored interaction look richer.

Prefer returning to a parked candidate with evidence of **unexplored interaction** over starting a fresh candidate from nothing.

Rules:

* The agenda is a memory aid, not an algorithm. No scores, no rankings, no quotas, no breadth requirements, no parallel exploration.
* Park only with a concrete revisit reason. "Might be good" is not a reason.
* Never manufacture candidates just to keep the agenda populated. An empty agenda is normal.
* When one branch is clearly the best, follow it deeply and ignore the agenda.
* A parked candidate may simply die. Drop it when its revisit reason no longer holds.

Before abandoning the current branch, check:

> Do I have a parked candidate whose unexplored interaction is stronger than anything left here?

## 8. Keep roles distinct

Separate these roles when reasoning:

* **scaling axis** — what the build scales with;
* **generator** — creates or increases the scaling variable;
* **consumer/converter** — uses or transforms it;
* **enabler** — makes the interaction possible;
* **multiplier** — improves the resulting output;
* **defense** — keeps the build alive.

These roles can interact, but they are not interchangeable.

A multiplier is not automatically a scaling axis.

A generator is not automatically a second scaling axis.

A defensive layer is not automatically part of the scaling chain.

## 9. Prefer genuine architectural depth

When comparing possible directions, prefer a candidate where multiple mechanics **depend on, transform, reinforce, or otherwise materially interact with the core scaling axis**.

A strong architecture may contain several layers such as:

**scaling axis → generator/accumulation → consumer/converter → secondary effect → additional scaling/payoff → enabler/defense**

It does not need to contain all of these.

A short chain can still be strong if the interaction is unusually meaningful.

Conversely, a long chain of weak or unrelated relationships is not valuable merely because it is long.

## 10. Exploration decision

At each promising discovery, ask:

> Is this merely a valid scaling relationship, a simple generator-spender loop, or evidence of a deeper interacting system?

If it is only an isolated scaling relationship or generator-spender loop and no useful continuation is visible, consult the agenda (§7) and move on.

If the graph exposes a plausible additional layer, prioritize exploring it.

The purpose of further exploration is to discover whether the candidate can become a **coherent multi-mechanic architecture**, not to artificially increase its complexity.

## 11. Evidence discipline

Do not manufacture connections to make a candidate appear deeper or more novel — and do not manufacture parked candidates to fill the agenda.

Important relationships in the proposed architecture should be supported by the KB or by an explicitly available feasibility/mechanics check.

If a potentially useful relationship cannot be confirmed, mark it as uncertain rather than silently treating it as established. If a parked candidate rests on an uncertain relationship, its revisit reason inherits that uncertainty.

Do not substitute general game knowledge for missing graph evidence when claiming that a relationship was discovered from the KB.

## Objective

Find build concepts that are more than isolated scaling modifiers or simple generator-spender loops.

When the graph provides evidence for it, pursue **multiple interacting mechanics around a coherent scaling core** — and when several such cores appear, remember the promising ones instead of losing them.

Do not force complexity.

**Discover architectural depth when the evidence supports it.**
