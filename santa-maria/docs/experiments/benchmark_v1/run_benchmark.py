#!/usr/bin/env python3
"""Benchmark v1 runner — drives the PUBLIC Research API over the frozen corpus.

Per entry, uniformly:
  1. phase8 resolve(node_id)          — starting-point resolvability record
  2. phase8 carriers(node_id)         — depth-1 reverse projection (fan-in)
  3. phase6 get_neighbour(depth=1)    — forward traversal (fan-out, bounded)

Raw envelopes are archived under raw/. No KB internals are touched; cache
file hashes are recorded before/after to prove read-only behavior.
"""

import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "santa-maria" / "tools"))

import phase8_research as p8  # noqa: E402
import phase6_api as p6  # noqa: E402

CORPUS = REPO / "santa-maria/docs/experiments/seed_corpus_v1/corpus.json"
OUT = Path(__file__).resolve().parent / "raw"
CACHE_FILES = ["nodes.db", "edges.db", "raw_records.db"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def cache_hashes() -> dict:
    out = {}
    for f in CACHE_FILES:
        p = REPO / "santa-maria/cache" / f
        if p.exists():
            out[f] = sha(p)
    return out


def slug(node_id: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", node_id).strip("_")
    return s[:60]


def main():
    corpus = json.loads(CORPUS.read_text())
    OUT.mkdir(exist_ok=True)
    before = cache_hashes()
    print("cache before:", json.dumps(before))

    for e in corpus["entries"]:
        idx, nid = e["index"], e["node_id"]
        base = f"{idx:03d}_{slug(nid)}"
        rec = {"index": idx, "node_id": nid, "type": e["type"]}

        env = p8.resolve(nid)
        (OUT / f"{base}.resolve.json").write_text(json.dumps(env, indent=1))
        rec["resolve_error"] = env["error"]["code"] if env.get("error") else None

        env = p8.carriers(nid)
        (OUT / f"{base}.carriers.json").write_text(json.dumps(env, indent=1))
        rec["carriers_error"] = env["error"]["code"] if env.get("error") else None
        rec["carrier_counts"] = env["meta"]["counts"] if not env.get("error") else None

        try:
            env = p6.get_neighbour(1, {"start": nid, "max_nodes_per_level": 200})
        except Exception as ex:  # noqa: BLE001 — record, don't crash the run
            env = {"error": {"code": "exception", "detail": str(ex)}}
        (OUT / f"{base}.neighbour.json").write_text(json.dumps(env, indent=1))
        n_err = env.get("error") if isinstance(env, dict) else None
        rec["neighbour_error"] = n_err.get("code") if isinstance(n_err, dict) else None

        (OUT / f"{base}.record.json").write_text(json.dumps(rec, indent=1))
        print(f"[{idx:3d}] {nid}: resolve={rec['resolve_error']} "
              f"carriers={rec['carrier_counts']} neighbour={rec['neighbour_error']}")

    after = cache_hashes()
    print("cache after: ", json.dumps(after))
    print("read-only:", "OK" if before == after else "CHANGED — INVESTIGATE")


if __name__ == "__main__":
    main()
