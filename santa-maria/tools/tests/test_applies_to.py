#!/usr/bin/env python3
"""Phase 5M applies-to mechanics — assert-based tests.

Run: python3 tools/tests/test_applies_to.py
Covers: mechanic projection completeness + payload semantics, the
input-side discovery acceptance (probing an ordinary input stat surfaces
the mechanic through normal carriers(), without knowing the mechanic name
or output stat), output-side symmetry, the no-curated-list invariant
(fixtures live only in tests), retrieval boundedness, and idempotent
re-projection.
"""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import phase5m_applies_to as M5
import phase6_api as api
import phase8_research as R

SANTA = Path(__file__).resolve().parents[2]


def _artifact_mechanics():
    aud = json.loads((SANTA / 'tools/sources/pob_stat_mechanics.json').read_text())
    gen = json.loads((SANTA / 'tools/sources/applies_to_mechanics.json').read_text())
    return aud, gen


def test_mechanic_nodes_complete():
    aud, gen = _artifact_mechanics()
    expect = {f"mechanic:applies_to_{m['id']}" for m in aud['mechanics']} | \
             {f"mechanic:applies_to_{m['id']}" for m in gen['mechanics']}
    g = api.get_graph()
    nodes = g._load_nodes()
    got = {nid: p for nid, (t, p) in nodes.items()
           if t == 'Mechanic' and nid.startswith('mechanic:applies_to_')}
    assert set(got) == expect, set(got) ^ expect
    for nid, p in got.items():
        assert p.get('name'), nid
        assert p.get('description'), nid
        assert p.get('members') is not None, nid
        assert p.get('provenance', {}).get('source_file'), nid
    # the 9 audited mechanics are still individually present
    for m in aud['mechanics']:
        assert f"mechanic:applies_to_{m['id']}" in got
    print(f'ok: {len(got)} mechanic nodes (9 audited + {len(gen["mechanics"])} '
          f'generated), payloads complete')


def _mechanics_of(stat_id):
    """Normal exploration: neighbour (default both directions) from an
    encountered stat; mechanic rows are stat -> mechanic out-edges and sort
    before mod/passive rows, so they survive level truncation."""
    r = api.get_neighbour(1, {'start': stat_id})
    out = [e['to'] for lv in r['levels'] for e in lv['edges']
           if e['type'] == 'stat_mechanic_relation'
           and e['to'].startswith('mechanic:applies_to_')]
    out.sort()
    return [(nid, _payload(nid)) for nid in out]


def _payload(nid):
    env = R.resolve(nid.replace('mechanic:', 'mechanic:applies_to_' == nid and nid or nid))
    env = R.resolve(nid)
    assert env['error'] is None and len(env['results']) == 1, env
    return env['results'][0]['mechanic']


def test_input_side_discovery():
    """The acceptance criterion: starting from an ordinary input stat, the
    normal exploration path (neighbour with default filters) discovers the
    mechanic without knowing the mechanic name or output stat beforehand."""
    rows = _mechanics_of('stat:maximum_mana_+%')
    mind = [(nid, m) for nid, m in rows
            if m.get('pob_flag') == 'TransfigurationOfMind']
    assert mind, rows
    nid, m = mind[0]
    # the payload states the semantics in prose — no stat-id decoding
    assert 'maximum mana' in m['description'].lower(), m['description']
    assert 'damage' in m['description'].lower(), m['description']
    assert '30%' in (m.get('value') or ''), m.get('value')
    assert m['input']['operand_stat'] == 'stat:maximum_mana_+%'
    # same from the other two input pools
    for stat, flag in (('stat:maximum_life_+%', 'TransfigurationOfBody'),
                       ('stat:maximum_energy_shield_+%', 'TransfigurationOfSoul')):
        hit = [(nid, m) for nid, m in _mechanics_of(stat)
               if m.get('pob_flag') == flag]
        assert hit, stat
    print('ok: input-side discovery — maximum_mana/life/ES probes surface '
          'the Transfiguration mechanics with prose semantics + 30% value')


def test_output_side_symmetry():
    """Probing the generated output-side stat discovers the same mechanic and
    exposes the input family."""
    rows = _mechanics_of('stat:additive_mana_modifiers_apply_to_damage_at_30%_value')
    assert rows, 'output stat must surface its mechanic'
    m = rows[0][1]
    assert m['pob_flag'] == 'TransfigurationOfMind'
    assert m['input']['operand_stat'] == 'stat:maximum_mana_+%', m['input']
    # audited spell-damage bridge from both sides
    hit = [nid for nid, m in _mechanics_of('stat:spell_damage_+%')
           if nid == 'mechanic:applies_to_spell_damage_applies_to_attacks']
    assert hit
    rows = _mechanics_of('stat:additive_spell_damage_modifiers_apply_to_attack_damage')
    assert rows and rows[0][1]['input']['operand_stat'] == 'stat:spell_damage_+%'
    print('ok: output-side symmetry — bridge stat probes expose the input family')


def test_no_curated_list_invariant():
    """The fixtures must come from the generic sweep. The class-boundary
    regexes (AppliesTo / TransfigurationOf flag families) are pattern
    definitions — allowed; what is banned is naming the specific bridge
    mechanics or their stats anywhere in the extraction/projection code."""
    banned = ('transfiguration_of_mind', 'transfiguration_of_body',
              'transfiguration_of_soul', 'additive_mana_modifiers',
              'additive_life_modifiers', 'additive_energy_shield_modifiers',
              'maximum_mana_+%', 'maximum_life_+%',
              'maximum_energy_shield_%')
    for f in ('tools/sources/generate_applies_to.py',
              'tools/phase5m_applies_to.py'):
        text = (SANTA / f).read_text()
        for b in banned:
            assert b not in text, f'{f} curates {b}'
    print('ok: no curated fixture list in generator/projection sources '
          '(class-boundary regexes only)')


def test_retrieval_bounded():
    """Mechanic rows appear only where the mechanic applies (connectivity)."""
    g = api.get_graph()
    nodes = g._load_nodes()
    stats = sorted(nid for nid, (t, _p) in nodes.items() if t == 'Stat')
    flooded = []
    for s in stats:
        env = R.carriers(s)
        n = env['meta']['counts'].get('stat_mechanic_relation', 0)
        if n > 4:
            flooded.append((s, n))
    assert not flooded, f'mechanic flooding: {flooded[:5]}'
    print(f'ok: no mechanic flooding across {len(stats)} stats (max 4 rows per stat)')


def test_resolve_mechanics():
    env = R.resolve('Transfiguration', type='Mechanic')
    ids = {r['id'] for r in env['results']}
    assert {'mechanic:applies_to_transfiguration_of_mind',
            'mechanic:applies_to_transfiguration_of_body',
            'mechanic:applies_to_transfiguration_of_soul'} <= ids, ids
    for r in env['results']:
        assert r['name'], r
    print('ok: resolve(type=Mechanic) finds the bridges by name')


def test_idempotent_reprojection():
    def counts():
        con = sqlite3.connect(SANTA / 'cache' / 'edges.db')
        n = con.execute("select count(*) from edges where relationship_type="
                        "'stat_mechanic_relation' and target_node_id like "
                        "'mechanic:applies_to_%'").fetchone()[0]
        con.close()
        ncon = sqlite3.connect(SANTA / 'cache' / 'nodes.db')
        m = ncon.execute("select count(*) from nodes where node_id like "
                         "'mechanic:applies_to_%'").fetchone()[0]
        ncon.close()
        return n, m
    before = counts()
    M5.project()
    M5.verify()
    assert counts() == before, 're-projection must be idempotent'
    print('ok: re-projection idempotent (same mechanic node/edge counts)')


if __name__ == '__main__':
    test_mechanic_nodes_complete()
    test_input_side_discovery()
    test_output_side_symmetry()
    test_no_curated_list_invariant()
    test_retrieval_bounded()
    test_resolve_mechanics()
    test_idempotent_reprojection()
    print('ALL TESTS PASSED')
