#!/usr/bin/env python3
"""Build the stat-id vocabulary and the exhaustive conversion/scaling-pattern scan.

Input:  santa-maria/data/  (produced by tools/download.py)
Output: santa-maria/cache/stat_vocab.json, santa-maria/cache/conversion_hits.json

Vocabulary = observed/union stat-id vocabulary: the union of stat identifiers
observed across the RePoE stats registry (repoe/stats.json keys), modifiers
(repoe/mods.json stats[].id), gems (repoe/gems.json constant_stats /
per_level_stats / static), and passive-tree data (passive_skill_trees/*.json
passives stats). It is NOT exclusively the canonical registry from stats.json.

Every stat id is scanned for conversion/scaling substrings; a stat id is
recorded under EVERY matching pattern (an id may match several patterns,
consistent with analyze.py — no first-match bucketing).
"""
import json, collections, os
from pathlib import Path
from common import CONVERSION_PATTERNS as PATTERNS

SANTA = Path(__file__).resolve().parents[1]
ROOT = SANTA / 'data'
CACHE = SANTA / 'cache'


def collect_ids():
    ids = set(json.load(open(ROOT / 'repoe/stats.json')).keys())
    m = json.load(open(ROOT / 'repoe/mods.json'))
    for v in m.values():
        for s in v['stats']:
            ids.add(s['id'])
    for root, _, fs in os.walk(ROOT / 'repoe/passive_skill_trees'):
        for f in fs:
            d = json.load(open(os.path.join(root, f)))
            for p in d.get('passives', {}).values():
                ids.update((p.get('stats') or {}).keys())
    g = json.load(open(ROOT / 'repoe/gems.json'))
    for v in g.values():
        if not isinstance(v, dict):
            continue
        for cs in v.get('constant_stats', []) or []:
            ids.add(cs[0])
        for i in v.get('per_level_stats', []) or []:
            ids.add(i[0])
        ids.update((v.get('static', {}) or {}).keys())
    return ids


def bucket_hits(ids, patterns):
    """Every matching pattern per id (an id can appear under several)."""
    hits = collections.defaultdict(list)
    for i in ids:
        for p in patterns:
            if p in i:
                hits[p].append(i)
    return {p: hl for p, hl in hits.items()}


def main():
    ids = collect_ids()
    CACHE.mkdir(parents=True, exist_ok=True)
    json.dump(sorted(ids), open(CACHE / 'stat_vocab.json', 'w'))
    hits = bucket_hits(ids, PATTERNS)
    json.dump({p: hl for p, hl in hits.items()}, open(CACHE / 'conversion_hits.json', 'w'))
    print(f"stat id vocabulary: {len(ids)}")
    for p in PATTERNS:
        print(f"  {p}: {len(hits.get(p, []))}")


if __name__ == '__main__':
    main()
