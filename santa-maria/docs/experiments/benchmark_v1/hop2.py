#!/usr/bin/env python3
"""Benchmark v1 hop-2: chase layer-1 targets of each corpus entry through the
public API to expose shared scaling axes / chains.

Targets per entry (bounded, deduped):
  - stats reached via passive_grants_stat / gem_grants_stat / modifier_grants_stat
    -> carriers(stat)  (who ELSE grants/consumes this stat)
  - mods reached via unique_modifier_association
    -> get_neighbour(mod, 1)  (what stats does that mod grant)
  - mechanics/tags reached via stat_mechanic_relation / gem_has_tag: sampled
    stats -> carriers(stat) (build-facing sources of the mechanic)

All calls go through phase8/phase6 public API only.
"""

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "santa-maria" / "tools"))

import phase8_research as p8  # noqa: E402
import phase6_api as p6  # noqa: E402

RAW = Path(__file__).resolve().parent / "raw"
MAX_TARGETS = 12


def edges_of(nid):
    try:
        n = p6.get_neighbour(1, {"start": nid, "max_nodes_per_level": 200})
    except Exception:  # noqa: BLE001
        return []
    return [e for lvl in n.get("levels", []) for e in lvl.get("edges", [])]


def carriers_counts(nid):
    env = p8.carriers(nid)
    if env.get("error"):
        return None
    return {
        "counts": env["meta"]["counts"],
        "carriers": [r["carrier"] for r in env.get("results", [])][:15],
        "total": env["meta"].get("total", len(env.get("results", []))),
    }


def targets_for(nid):
    """Ordered hop-2 target list for a corpus node."""
    stats, mods, tags = [], [], []
    for e in edges_of(nid):
        t, to = e["type"], e["to"]
        if t in ("passive_grants_stat", "gem_grants_stat", "modifier_grants_stat") and to.startswith("stat:"):
            stats.append(to)
        elif t == "unique_modifier_association" and to.startswith("mod:"):
            mods.append(to)
        elif t in ("stat_mechanic_relation", "gem_has_tag"):
            tags.append((t, to))
    prio = []
    prio += [("stat", s) for s in stats]
    prio += [("mod", m) for m in mods]
    prio += tags[:4]
    seen, out = set(), []
    for kind, t in prio:
        if t not in seen:
            seen.add(t)
            out.append((kind, t))
    return out[:MAX_TARGETS]


def main():
    corpus = json.loads((REPO / "santa-maria/docs/experiments/seed_corpus_v1/corpus.json").read_text())
    for e in corpus["entries"]:
        idx, nid = e["index"], e["node_id"]
        targets = targets_for(nid)
        report = {"index": idx, "node_id": nid, "targets": {}}
        for kind, t in targets:
            if kind == "stat":
                report["targets"][t] = {"kind": "stat", **(carriers_counts(t) or {"error": "carriers"})}
            elif kind == "mod":
                m = {"kind": "mod"}
                es = edges_of(t)
                m["grants_stats"] = [x["to"] for x in es if x["type"] == "modifier_grants_stat"]
                m["tags"] = [x["to"] for x in es if x["type"] == "modifier_has_tag"]
                report["targets"][t] = m
            else:  # tag/mechanic relation: chase the stat side
                if t[0] == "stat_mechanic_relation":
                    continue  # 'to' is the mechanic itself; stats handled via entry L1 below
                report["targets"][t[1]] = {"kind": "tag"}
        # mechanics: sample up to 5 related stats and check their carriers
        if nid.startswith("mechanic:"):
            rel = [x["to"] for x in edges_of(nid) if x["type"] == "stat_mechanic_relation"]
            sample = rel[:5]
            report["related_stats_sample"] = {"total": len(rel), "sample": sample}
            for s in sample:
                report["targets"][s] = {"kind": "mech_stat", **(carriers_counts(s) or {"error": "carriers"})}
        out = RAW / f"{idx:03d}.hop2.json"
        out.write_text(json.dumps(report, indent=1))
        nz = {t: v.get("counts", v) for t, v in report["targets"].items() if isinstance(v, dict) and v.get("counts")}
        print(f"[{idx:3d}] {len(report['targets'])} targets, non-zero: {json.dumps(nz)[:200]}")

    print("hop2 done")


if __name__ == "__main__":
    main()
