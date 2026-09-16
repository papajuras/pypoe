#!/usr/bin/env python3
"""Phase 8 — Research API: agent-facing lookup layer over phase6_api.

Two operations, both derived from repeated Phase 6-7 session evidence:

  resolve(query, type=None)
      Complete (non-sampled) node lookup by id/name substring. get_start_seed
      samples; research lookups need every match plus ambiguity information.

  carriers(node_id, edge_types=None)
      Depth-1 reverse projection: what grants/carries this node. Returns the
      assembled carrier view (names, availability, passive_info, per-edge-type
      counts) that Phases 6-7 sessions re-implemented by hand on the raw
      adjacency — including the Phase 7C incident, where a hand scan read the
      wrong adjacency direction and silently returned no matches. carriers()
      has NO direction parameter by design: it is inherently reverse, and
      choosing an adjacency index must stay impossible at this layer.

Shared envelope (never raises; the caller always gets JSON):

  {'error':   None | {'code': 'unknown_subject'|'unknown_filter',
                      'detail', 'candidates', 'filter_echo'},
   'results': [...],
   'meta':    {...}}

A zero-result answer is a KB fact, not a failure: meta.counts states how many
carriers exist per requested edge type, meta.total is always present.
meta.truncated is null iff the result is complete; if
meta.truncated.total > len(results) the result is incomplete and must be
refined, never mistaken for exhaustive. Hard ceiling: RESEARCH_CEILING.

Edge-type/source-type mapping is 1:1 in this KB (measured: each carrier edge
type has exactly one source node class), so there is no source_type parameter.
attribute_grants_stat / stat_scales_with (stat->stat derivations) are excluded
by design: they are not carrier relationships.

Read-only: opens cache/nodes.db + cache/edges.db through phase6_api only.

Usage:
  python3 phase8_research.py resolve "Marionettes" --type Passive
  python3 phase8_research.py carriers stat:critical_strike_chance_+%
  python3 tests/test_phase8_research.py             # assert-based tests
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import phase6_api as api

RESEARCH_CEILING = 1000
CARRIER_EDGE_TYPES = ('modifier_grants_stat', 'passive_grants_stat',
                      'gem_grants_stat', 'unique_modifier_association')


def _ok(results, meta):
    return {'error': None, 'results': results, 'meta': meta}


def _err(code, detail, candidates=None, filter_echo=None):
    return {'error': {'code': code, 'detail': detail,
                      'candidates': candidates or [],
                      'filter_echo': filter_echo or {}},
            'results': [], 'meta': {}}


def _entry(nid, nodes):
    typ, payload = nodes[nid]
    out = {'id': nid, 'type': typ, 'name': payload.get('name')}
    if typ == 'UniqueItem':
        # 'available' | 'unavailable' | 'conflict' | None (None = no PoB
        # block -> coverage gap, not checked; never guessed, per phase6)
        out['availability'] = api._unique_availability(payload.get('name') or '')
    elif typ == 'Passive':
        # ascendancy may be None = unknown (conflict payload), never guessed
        out['passive_info'] = api._passive_info(payload)
    return out


def resolve(query, type=None):
    """Complete, non-sampled lookup of nodes by id/display-name substring.

    Case-insensitive on both (stat ids are lowercase; display names are not).
    Duplicate display names are a valid lookup case: all matches are returned
    and meta.ambiguous flags the exact-name duplication without removing
    anything.
    """
    graph = api.get_graph()
    nodes = graph._load_nodes()
    if not isinstance(query, str) or not query.strip():
        return _err('unknown_filter', 'query must be a non-empty string',
                    filter_echo={'query': query})
    if type is not None and type not in api.NODE_TYPES:
        return _err('unknown_filter', f'unknown node type {type!r}',
                    candidates=api.NODE_TYPES, filter_echo={'type': type})
    q = query.strip().lower()
    hits = sorted(
        nid for nid, (t, p) in nodes.items()
        if (type is None or t == type)
        and (q in nid.lower() or q in (p.get('name') or '').lower()))
    total = len(hits)
    returned = hits[:RESEARCH_CEILING]
    exact = sum(1 for nid in hits
                if (nodes[nid][1].get('name') or '').lower() == q)
    meta = {'query': query, 'type': type,
            'total': total, 'returned': len(returned),
            'truncated': None if total <= RESEARCH_CEILING
            else {'returned': len(returned), 'total': total},
            'exact_name_matches': exact, 'ambiguous': exact > 1}
    return _ok([_entry(nid, nodes) for nid in returned], meta)


def carriers(node_id, edge_types=None):
    """Depth-1 reverse projection: what grants/carries node_id.

    node_id must be an exact node id (use resolve() first for names). For a
    stat id the question is 'what grants this stat'; for a modifier id with
    edge_types=['unique_modifier_association'] it is 'which uniques carry
    this modifier'. Unknown subjects are input errors with did-you-mean
    candidates, so an empty result can only mean 'exists, genuinely no
    carriers' — and meta.counts makes that absence checkable per edge type.
    """
    graph = api.get_graph()
    nodes = graph._load_nodes()
    if not isinstance(node_id, str) or node_id not in nodes:
        hint = node_id if isinstance(node_id, str) else ''
        cands = sorted(nid for nid in nodes if hint and hint.lower() in nid.lower())
        return _err('unknown_subject', f'node not found: {node_id!r}',
                    candidates=cands[:20], filter_echo={'node_id': node_id})
    if edge_types is None:
        ets = list(CARRIER_EDGE_TYPES)
    else:
        bad = [t for t in edge_types if t not in CARRIER_EDGE_TYPES]
        if bad:
            return _err('unknown_filter',
                        f'unknown carrier edge type(s): {bad}',
                        candidates=list(CARRIER_EDGE_TYPES),
                        filter_echo={'edge_types': edge_types})
        ets = list(edge_types)
    inn = graph._load_edges()[1]
    rows, counts = [], {}
    for et in ets:
        srcs = sorted(src for (src, _prov) in inn.get(et, {}).get(node_id, []))
        counts[et] = len(srcs)
        for src in srcs:
            row = {'carrier': src, 'via': et}
            row.update({k: v for k, v in _entry(src, nodes).items()
                        if k != 'id'})
            rows.append(row)
    rows.sort(key=lambda r: (r['via'], r['carrier']))
    total = len(rows)
    meta = {'node_id': node_id, 'edge_types': ets,
            'counts': counts,
            'total': total, 'returned': min(total, RESEARCH_CEILING),
            'truncated': None if total <= RESEARCH_CEILING
            else {'returned': RESEARCH_CEILING, 'total': total}}
    return _ok(rows[:RESEARCH_CEILING], meta)


def demo():
    """Runnable self-check of the two operations."""
    env = resolve('Marionettes', type='Passive')
    assert env['error'] is None and len(env['results']) == 1, env
    assert env['results'][0]['passive_info']['ascendancy'] == 'Hierophant'
    env = carriers('stat:critical_strike_chance_+%')
    assert env['error'] is None, env
    assert env['meta']['counts']['passive_grants_stat'] > 0
    assert any(r['carrier'] == 'passive:AscendancyAssassin1' for r in env['results']), \
        'Phase 7C regression: ascendancy crit binding must be reachable'
    env = resolve('intelligence', type='Passive')
    assert env['meta']['ambiguous'] and len(env['results']) > 1
    print('demo ok: resolve + carriers behave; 7C regression fact reachable')


if __name__ == '__main__':
    demo()
