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
stat_scales_with (conversion-pattern derivations) stays excluded by design:
it is not a carrier relationship. Intrinsic engine mechanics ARE surfaced:
attribute_grants_stat (attribute -> resource conversion, audited artifact)
and the rule_applies_to / rule_negated_by / rule_modified_by family (default
engine rules extracted from PoB source, with their exception mechanisms) all
point INTO the entities they concern, so probing any encountered stat or tag
returns its rules in the standard envelope. Connectivity keeps results
bounded: a rule row appears only where the rule actually applies.

Read-only: opens cache/nodes.db + cache/edges.db through phase6_api only.

Usage:
  python3 phase8_research.py resolve "Marionettes" --type Passive
  python3 phase8_research.py carriers stat:critical_strike_chance_+%
  python3 tests/test_phase8_research.py             # assert-based tests
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import phase6_api as api

RESEARCH_CEILING = 1000
CARRIER_EDGE_TYPES = ('modifier_grants_stat', 'passive_grants_stat',
                      'gem_grants_stat', 'unique_modifier_association',
                      'attribute_grants_stat', 'rule_applies_to',
                      'rule_negated_by', 'rule_modified_by',
                      'stat_mechanic_relation', 'stat_mechanic_operand',
                      'stat_mechanic_variant', 'modifier_has_influence',
                      'influence_spawns_on')


def _ok(results, meta):
    return {'error': None, 'results': results, 'meta': meta}


def _err(code, detail, candidates=None, filter_echo=None):
    return {'error': {'code': code, 'detail': detail,
                      'candidates': candidates or [],
                      'filter_echo': filter_echo or {}},
            'results': [], 'meta': {}}


_INFL_INFO_CACHE = None   # mod id -> (display names, spawn classes); lazy


def _mod_influence_info(nid):
    """(display names, spawn item classes) for a modifier from the phase 5I
    projection edges. Pure read over the public graph adjacency; cached once
    for the whole graph (the projection edge set is small)."""
    global _INFL_INFO_CACHE
    if _INFL_INFO_CACHE is None:
        graph = api.get_graph()
        nodes = graph._load_nodes()
        out = graph._load_edges()[0]
        table = {}
        for src, edges in out.get('modifier_has_influence', {}).items():
            names, classes = [], set()
            for (tgt, _prov) in edges:
                payload = nodes.get(tgt, (None, {}))[1] or {}
                if payload.get('name'):
                    names.append(payload['name'])
                for c in payload.get('item_classes') or []:
                    classes.add(str(c).replace('item_class:', '', 1))
            table[src] = (sorted(names), sorted(classes))
        _INFL_INFO_CACHE = table
    return _INFL_INFO_CACHE.get(nid, ([], []))


def _entry(nid, nodes):
    typ, payload = nodes[nid]
    # _node_name is the canonical display-name projection (same one
    # get_start_seed/get_neighbour use): gems carry display_name, stats their
    # stat_id, uniques their display id — never bypass it for names
    out = {'id': nid, 'type': typ, 'name': api._node_name(nid, payload)}
    if typ == 'UniqueItem':
        # 'available' | 'unavailable' | 'conflict' | None (None = no PoB
        # block -> coverage gap, not checked; never guessed, per phase6)
        out['availability'] = api._unique_availability(payload.get('name') or '')
    elif typ == 'Passive':
        # ascendancy may be None = unknown (conflict payload), never guessed
        out['passive_info'] = api._passive_info(payload)
    elif typ == 'Modifier':
        # mod ids are fossils — always expose the real game text so callers
        # never render an id as prose (whispers02 root cause)
        out['text'] = payload.get('text')
        # influence + spawn classes from the projection edges (phase 5I);
        # absent for non-influenced mods (empty lists, not None)
        inf, cls = _mod_influence_info(nid)
        out['influence'] = inf
        out['spawn_classes'] = cls
    elif typ == 'Influence':
        # first-class influence facts: display name, spawn classes, provenance
        out['influence'] = {k: payload[k] for k in
                            ('tag_suffix', 'name', 'item_classes',
                             'provenance') if payload.get(k) is not None}
    elif typ == 'Rule':
        # rule nodes carry their own semantics; expose formula/value/operands
        # + source anchors so the rule is understandable without extra lookups
        out['rule'] = {k: payload[k] for k in
                       ('kind', 'formula', 'value', 'operands', 'source',
                        'pob_commit', 'artifact_commit') if payload.get(k) is not None}
    elif typ == 'Mechanic':
        # mechanic nodes carry the real semantics (input family, output,
        # value, provenance) — never make callers decode fossil stat ids
        out['mechanic'] = {k: payload[k] for k in
                           ('kind', 'name', 'description', 'input', 'output',
                            'value', 'members', 'pob_flag', 'provenance')
                           if payload.get(k) is not None}
    return out


def resolve(query, type=None, include_alternate_ascendancies=False):
    """Complete, non-sampled lookup of nodes by id/display-name/modifier-text
    substring.

    Case-insensitive on all three (stat ids are lowercase; display names and
    modifier text are not). Text matching is literal normalized substring —
    lowercase + strip non-alphanumeric on both sides — no fuzzy matching or
    synonyms; it applies to any node whose payload carries a `text` field
    (Modifier is the only such type). Duplicate display names are a valid
    lookup case: all matches are returned and meta.ambiguous flags the
    exact-name duplication without removing anything. Alternate (Phrecia)
    ascendancy passives are excluded by default;
    meta.excluded_alternate_ascendancies reports how many were suppressed.
    """
    graph = api.get_graph()
    nodes = graph._load_nodes()
    if not isinstance(query, str) or not query.strip():
        return _err('unknown_filter', 'query must be a non-empty string',
                    filter_echo={'query': query})
    if type is not None and type not in api.NODE_TYPES:
        return _err('unknown_filter', f'unknown node type {type!r}',
                    candidates=api.NODE_TYPES, filter_echo={'type': type})
    if not isinstance(include_alternate_ascendancies, bool):
        return _err('unknown_filter', 'include_alternate_ascendancies must be '
                    'a boolean',
                    filter_echo={
                        'include_alternate_ascendancies':
                            include_alternate_ascendancies})
    q = query.strip().lower()
    # literal normalized form for prose matching only — id/name matching
    # keeps its existing raw-lowercase semantics untouched
    q_norm = re.sub(r'[^a-z0-9]', '', q)
    # match on id OR canonical display name (api._node_name — same projection
    # as get_neighbour/get_start_seed; gem display_name and rule statements
    # are searchable, never a per-type special case) OR normalized modifier
    # text (only payloads that carry a `text` field)
    hits = sorted(
        nid for nid, (t, p) in nodes.items()
        if (type is None or t == type)
        and (q in nid.lower()
             or q in (api._node_name(nid, p) or '').lower()
             or (q_norm and q_norm in re.sub(r'[^a-z0-9]', '',
                                             (p.get('text') or '').lower()))))
    excluded = 0
    if api.EXCLUDE_ALTERNATE_ASCENDANCIES and \
            not include_alternate_ascendancies:
        kept = []
        for nid in hits:
            if api.is_alternate_ascendancy(nid):
                excluded += 1
            else:
                kept.append(nid)
        hits = kept
    total = len(hits)
    returned = hits[:RESEARCH_CEILING]
    exact = sum(1 for nid in hits
                if (api._node_name(nid, nodes[nid][1]) or '').lower() == q)
    meta = {'query': query, 'type': type,
            'total': total, 'returned': len(returned),
            'excluded_alternate_ascendancies': excluded,
            'truncated': None if total <= RESEARCH_CEILING
            else {'returned': len(returned), 'total': total},
            'exact_name_matches': exact, 'ambiguous': exact > 1}
    return _ok([_entry(nid, nodes) for nid in returned], meta)


def carriers(node_id, edge_types=None, include_alternate_ascendancies=False):
    """Depth-1 reverse projection: what grants/carries node_id.

    node_id must be an exact node id (use resolve() first for names). For a
    stat id the question is 'what grants this stat'; for a modifier id with
    edge_types=['unique_modifier_association'] it is 'which uniques carry
    this modifier'. Unknown subjects are input errors with did-you-mean
    candidates, so an empty result can only mean 'exists, genuinely no
    carriers' — and meta.counts makes that absence checkable per edge type.
    Alternate (Phrecia) ascendancy passives are excluded by default;
    meta.excluded_alternate_ascendancies reports how many were suppressed.
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
    if not isinstance(include_alternate_ascendancies, bool):
        return _err('unknown_filter', 'include_alternate_ascendancies must be '
                    'a boolean',
                    filter_echo={
                        'include_alternate_ascendancies':
                            include_alternate_ascendancies})
    inn = graph._load_edges()[1]
    rows, counts, excluded = [], {}, 0
    for et in ets:
        srcs = sorted(src for (src, _prov) in inn.get(et, {}).get(node_id, []))
        if api.EXCLUDE_ALTERNATE_ASCENDANCIES and \
                not include_alternate_ascendancies:
            kept = []
            for s in srcs:
                if api.is_alternate_ascendancy(s):
                    excluded += 1
                else:
                    kept.append(s)
            srcs = kept
        counts[et] = len(srcs)
        for src in srcs:
            row = {'carrier': src, 'edge_type': et}
            row.update({k: v for k, v in _entry(src, nodes).items()
                        if k != 'id'})
            rows.append(row)
    rows.sort(key=lambda r: (r['edge_type'], r['carrier']))
    total = len(rows)
    subj = nodes[node_id]
    meta = {'node_id': node_id, 'edge_types': ets,
            'counts': counts,
            'total': total, 'returned': min(total, RESEARCH_CEILING),
            'excluded_alternate_ascendancies': excluded,
            'truncated': None if total <= RESEARCH_CEILING
            else {'returned': RESEARCH_CEILING, 'total': total}}
    if subj[0] == 'Modifier':
        # mod ids are fossils — surface the subject's real text so callers
        # never render the id as prose (whispers02 root cause)
        meta['subject_text'] = subj[1].get('text')
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
