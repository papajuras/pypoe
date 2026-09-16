#!/usr/bin/env python3
"""Phase 8 Research API — assert-based tests.

Run: python3 tools/tests/test_phase8_research.py
Covers: the Phase 7C adjacency-direction regression (ascendancy crit bindings
must be reachable through carriers(), and the hand-rolled probe shape that
failed must demonstrably return nothing), carrier projection contents,
zero-carrier-as-fact, input-error feedback, resolve completeness/ambiguity/
truncation, and read-only behavior (KB file digests stable).
"""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import phase6_api as api
import phase8_research as R

CRIT_STAT = 'stat:critical_strike_chance_+%'


def test_7c_adjacency_direction_regression():
    """The Phase 7C incident: a hand probe iterated the in-adjacency (index 1)
    as if it were the out-adjacency and filtered sources by node type
    'Passive' — on the in-adjacency the keys are stats, so the filter matched
    nothing and the scan silently reported 'no ascendancy grants crit'. The
    KB always contained the relationship. carriers() must surface it, and the
    buggy probe shape must demonstrably yield the false negative."""
    env = R.carriers(CRIT_STAT, edge_types=['passive_grants_stat'])
    assert env['error'] is None, env
    rows = {r['carrier'] for r in env['results']}
    assert 'passive:AscendancyAssassin1' in rows, \
        'ascendancy crit binding must be reachable (7C false negative)'
    assert 'passive:AscendancyAssassin7' in rows
    n_pgs = env['meta']['counts']['passive_grants_stat']
    assert n_pgs == len(rows) and n_pgs > 10, \
        f'expected a real ascendancy carrier set, got {n_pgs}'
    # the 7C probe shape, reproduced verbatim: wrong index + impossible filter
    N = api.get_graph()._load_nodes()
    buggy_out = api.get_graph()._load_edges()[1]        # [1] is the IN adjacency
    found = []
    for s, l in buggy_out.get('passive_grants_stat', {}).items():
        if s not in N or N[s][0] != 'Passive':          # never true on in-adjacency
            continue
        for d, _ in l:
            if d == CRIT_STAT:
                found.append(s)
    assert found == [], 'the 7C probe shape must stay a demonstrated false negative'
    assert n_pgs > 0
    print('ok: 7C regression — carriers() reaches ascendancy crit bindings, '
          f'hand-probe shape yields 0 (n_pgs={n_pgs})')


def test_carriers_counts_consistency():
    env = R.carriers(CRIT_STAT)
    assert env['error'] is None
    m = env['meta']
    assert m['total'] == sum(m['counts'].values()) == len(env['results'])
    assert m['truncated'] is None and m['returned'] == m['total']
    assert set(m['counts']) == set(R.CARRIER_EDGE_TYPES)
    print('ok: carriers meta counts consistent, complete result')


def test_carriers_edge_type_uma():
    env = R.carriers('mod:AnimatedGuardianDamagePerAnimatedWeaponUnique__1__',
                     edge_types=['unique_modifier_association'])
    assert env['error'] is None
    rows = env['results']
    assert [r['carrier'] for r in rows] == ['unique:775'], rows
    assert rows[0]['edge_type'] == 'unique_modifier_association'
    assert rows[0]['name'] == 'Chains of Command'
    assert rows[0]['availability'] == 'available'
    print('ok: carriers via unique_modifier_association, availability attached')


def test_carriers_zero_carriers_is_a_fact():
    g = api.get_graph(); N = g._load_nodes()
    inn = g._load_edges()[1]
    carried = set()
    for et in R.CARRIER_EDGE_TYPES:
        carried.update(inn.get(et, {}).keys())
    empty = sorted(nid for nid, (t, _) in N.items()
                   if t == 'Stat' and nid not in carried)
    assert empty, 'KB must contain uncarried stats for this test to be meaningful'
    env = R.carriers(empty[0])
    assert env['error'] is None
    assert env['results'] == []
    assert set(env['meta']['counts'].values()) == {0}
    assert env['meta']['total'] == 0 and env['meta']['truncated'] is None
    print(f'ok: zero-carrier stat {empty[0]} returns a checkable fact, not an error')


def test_carriers_input_errors():
    env = R.carriers('stat:critical_strike_chance')
    assert env['error']['code'] == 'unknown_subject'
    assert CRIT_STAT in env['error']['candidates']
    env = R.carriers(CRIT_STAT, edge_types=['stat_scales_with'])
    assert env['error']['code'] == 'unknown_filter'
    assert 'stat_scales_with' not in env['error']['candidates']
    env = R.carriers(None)
    assert env['error']['code'] == 'unknown_subject'
    print('ok: unknown subject/filter feedback with candidates')


def test_resolve_exact_and_ambiguity():
    env = R.resolve('Marionettes', type='Passive')
    assert env['error'] is None and len(env['results']) == 1
    hit = env['results'][0]
    assert hit['id'] == 'passive:AscendancyCustomHeirophant12'
    assert hit['passive_info']['ascendancy'] == 'Hierophant'
    assert hit['passive_info']['kind_flags']['is_notable'] is True
    # duplicate names are a valid lookup: all results, flagged, not blocked
    env = R.resolve('intelligence', type='Passive')
    assert env['error'] is None
    assert env['meta']['exact_name_matches'] >= 2 and env['meta']['ambiguous'] is True
    assert len(env['results']) >= env['meta']['exact_name_matches']
    assert env['meta']['truncated'] is None
    print('ok: resolve exact hit + ambiguity flag without result removal')


def test_resolve_case_insensitive_and_type_filter():
    a = R.resolve('MARIONETTES', type='Passive')
    b = R.resolve('marionettes', type='Passive')
    assert [r['id'] for r in a['results']] == [r['id'] for r in b['results']]
    env = R.resolve('Marionettes', type='Bogus')
    assert env['error']['code'] == 'unknown_filter'
    assert 'Passive' in env['error']['candidates']
    env = R.resolve('   ')
    assert env['error']['code'] == 'unknown_filter'
    print('ok: resolve case-insensitive, type/empty-query validation')


def test_resolve_truncation_reports_total():
    env = R.resolve('damage')
    m = env['meta']
    assert len(env['results']) == R.RESEARCH_CEILING
    assert m['total'] > R.RESEARCH_CEILING, m
    assert m['truncated'] == {'returned': R.RESEARCH_CEILING, 'total': m['total']}
    print(f'ok: resolve truncation explicit (total={m["total"]})')


def test_availability_and_unknown_passive_info_surface():
    env = R.resolve('Corona Solaris', type='UniqueItem')
    assert env['results'][0]['availability'] == 'unavailable', \
        'unavailable content must surface as a fact (7C live catch)'
    print('ok: availability surfaced on resolve results')


def test_readonly_kb_digests():
    def digest():
        h = hashlib.sha256()
        for f in ('nodes.db', 'edges.db'):
            h.update((Path(__file__).resolve().parents[2] / 'cache' / f).read_bytes())
        return h.hexdigest()
    before = digest()
    R.resolve('crit')
    R.carriers(CRIT_STAT)
    R.carriers('mod:AnimateGuardianDamagePerAnimatedWeaponUnique__1__')
    R.resolve('intelligence', type='Passive')
    api.get_neighbour(1, {'start': 'passive:AscendancyAssassin1'})
    assert digest() == before, 'research layer must never write the KB'
    print('ok: KB file digests unchanged across research calls')


if __name__ == '__main__':
    test_7c_adjacency_direction_regression()
    test_carriers_counts_consistency()
    test_carriers_edge_type_uma()
    test_carriers_zero_carriers_is_a_fact()
    test_carriers_input_errors()
    test_resolve_exact_and_ambiguity()
    test_resolve_case_insensitive_and_type_filter()
    test_resolve_truncation_reports_total()
    test_availability_and_unknown_passive_info_surface()
    test_readonly_kb_digests()
    print('ALL TESTS PASSED')
