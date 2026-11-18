#!/usr/bin/env python3
"""Stat classification — reasoning/candidate layer.

Implements the deterministic rule from docs/experiments/phase7_item_internal_keystones/README.md
over the existing graph, without touching the graph, the Phase 6 API, or
traversal. Read-only: nodes.db/edges.db are never written.

Rule (structural, derived from existing edges — no ID lists, no degree,
no carrier-count, no translation-format heuristics):

    keystone_* family (internal implementation tokens of keystone mechanics):
      item_only_internal_keystone = has modifier/gem_grants_stat in-edge
                                    AND has no passive_grants_stat in-edge
                                    AND no Passive-tree node represents the stat
      shared_tree_item            = passive_grants_stat in-edge AND item carriers
      tree_only                   = passive_grants_stat in-edge, no item carriers
      unused                      = no carriers at all (dead vocabulary)

    any other stat (ordinary gem/item stats are NOT internal):
      item_only_stat              = has item/gem carriers, no passive_grants_stat
      shared_tree_item / tree_only / unused = same structural rules as above

"Item-only" is NOT synonymous with "internal implementation stat": only the
keystone family carries that meaning; generic gem/item-only stats classify as
item_only_stat.

The Passive display-name / id-suffix comparison is retained ONLY as secondary
validation evidence (`name_match`), never as the classifier: the authoritative
tree-representation signal is the `passive_grants_stat` relationship itself.

Usage:
  python3 phase7_stat_classification.py                     # self-check
  python3 -m tests.test_stat_classification          # assert-based tests
"""
import json, re
from pathlib import Path

import phase6_api

SANTA = Path(__file__).resolve().parents[1]
TRANSLATIONS = SANTA / 'data' / 'repoe' / 'stat_translations.json'

ITEM_ONLY_INTERNAL_KEYSTONE = 'item_only_internal_keystone'
ITEM_ONLY_STAT = 'item_only_stat'
SHARED_TREE_ITEM = 'shared_tree_item'
TREE_ONLY = 'tree_only'
UNUSED = 'unused'

_names_cache = None


def _norm(s):
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())


def _display_names():
    """stat_id -> list of user-facing strings from stat_translations.json."""
    global _names_cache
    if _names_cache is None:
        names = {}
        for rec in json.loads(TRANSLATIONS.read_text()):
            for sid in rec.get('ids', []):
                names[sid] = [e.get('string') for e in rec.get('English', [])
                              if e.get('string')]
        _names_cache = names
    return _names_cache


def _passive_name_index(g):
    """Normalized Passive-node names, cached on the graph instance (read-only)."""
    cached = getattr(g, '_passive_name_idx', None)
    if cached is None:
        cached = set()
        for nid, (typ, payload) in g._load_nodes().items():
            if typ == 'Passive' and payload.get('name'):
                cached.add(_norm(payload['name']))
        g._passive_name_idx = cached
    return cached


def classify_stat(node_or_stat_id, graph=None):
    g = graph or phase6_api.get_graph()
    stat_id = node_or_stat_id.split(':', 1)[1] if ':' in node_or_stat_id else node_or_stat_id
    nid = f'stat:{stat_id}'
    nodes = g._load_nodes()
    if nid not in nodes:
        raise ValueError(f'stat node not found: {nid!r}')
    _out, inn = g._load_edges()

    mod_grants = inn['modifier_grants_stat'].get(nid, [])
    gem_grants = inn['gem_grants_stat'].get(nid, [])
    pas_grants = inn['passive_grants_stat'].get(nid, [])
    has_carriers = bool(mod_grants or gem_grants)
    has_tree_grant = bool(pas_grants)

    if has_tree_grant and has_carriers:
        cls = SHARED_TREE_ITEM
    elif has_tree_grant:
        cls = TREE_ONLY
    elif has_carriers:
        cls = ITEM_ONLY_INTERNAL_KEYSTONE if stat_id.startswith('keystone_') else ITEM_ONLY_STAT
    else:
        cls = UNUSED

    names = _display_names().get(stat_id, [])
    passive_idx = _passive_name_index(g)
    suffix = _norm(stat_id.replace('keystone_', '', 1)) if stat_id.startswith('keystone_') else None
    name_match = bool([n for n in names if _norm(n) in passive_idx]
                      or (suffix and suffix in passive_idx))

    return {
        'node_id': nid,
        'stat_id': stat_id,
        'classification': cls,
        'mechanic': names[0] if names else None,
        'evidence': {
            'item_carriers': len(mod_grants) + len(gem_grants),
            'passive_granters': sorted(src for src, _ in pas_grants),
            'name_match': name_match,
        },
    }


def classify_all_keystones(graph=None):
    g = graph or phase6_api.get_graph()
    out = {}
    for nid in sorted(g._load_nodes()):
        if nid.startswith('stat:keystone_'):
            r = classify_stat(nid, g)
            out[r['stat_id']] = r
    return out


def name_match_conflicts(result):
    """Secondary validation: an item-only internal keystone must not name-match a Passive."""
    return result['classification'] == ITEM_ONLY_INTERNAL_KEYSTONE and result['evidence']['name_match']


def demo():
    g = phase6_api.GraphDB()
    allk = classify_all_keystones(g)
    dist = {}
    for r in allk.values():
        dist[r['classification']] = dist.get(r['classification'], 0) + 1
    print('keystone distribution:', dict(sorted(dist.items())))
    conflicts = [s for s, r in allk.items() if name_match_conflicts(r)]
    print('name-match conflicts:', conflicts or 'none')
    assert conflicts == [], 'item-only internal keystones must not name-match a Passive node'
    sample = sorted(allk)[0]
    r = allk[sample]
    print(f'{r["node_id"]} -> {r["classification"]} -> mechanic: {r["mechanic"]}')


if __name__ == '__main__':
    demo()
