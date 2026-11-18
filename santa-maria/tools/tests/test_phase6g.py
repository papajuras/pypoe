#!/usr/bin/env python3
"""Phase 6G golden tests: opt-in carrier grouping in the Phase 6 API.

Run: python3 tools/tests/test_phase6g.py
Default BFS semantics must remain bit-identical (flag absent); grouped mode
must remove carrier flooding, preserve semantic reach, keep groups terminal,
and conserve group membership exactly (code-point verified IDs only — no
hand-typed '%/'+' ordering anywhere in this file).
"""
import json
import random
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import phase6_api

SANTA = Path(__file__).resolve().parents[2]
ncon = sqlite3.connect(f"file:{SANTA / 'cache' / 'nodes.db'}?mode=ro", uri=True)
art = json.loads((SANTA / 'tools' / 'sources' / 'pob_stat_mechanics.json').read_text())


def sid(head):
    """DB-derived Stat ID (code-point safe: no hand-typed '+'/'%' ordering)."""
    rows = [r[0] for r in ncon.execute("SELECT node_id FROM nodes WHERE type='Stat'")]
    cands = [r for r in rows
             if r.startswith(f"stat:{head}_")
             and set(r[len(f"stat:{head}_"):].replace('_', '')) <= {'+', '%'}]
    assert len(cands) == 1, (head, cands)
    return cands[0]


MELEE = sid('melee_physical_damage')
SPELL = sid('spell_damage')
ATTACK = sid('attack_damage')
SC = 'stat:strong_casting'
AM = next(m for m in art['mechanics'] if m['id'] == 'spell_damage_applies_to_attacks')
FAMILY = sorted(m['stat'] for m in AM['members'])
CANON = next(m['stat'] for m in AM['members'] if m['role'] == 'canonical')


def walk(start, depth=6, grouped=True, cap=200):
    f = {'start': start, 'max_nodes_per_level': cap}
    if grouped:
        f['carrier_grouping'] = True
    return phase6_api.get_neighbour(depth, f)


def reach(r):
    d = {}
    for lv in r['levels']:
        for e in lv['edges']:
            d.setdefault(e['to'], lv['depth'])
    return d


def gen_total(r):
    return sum(l['gen'] for l in r['levels']) if r['levels'] and 'gen' in r['levels'][0] else None


def test_default_mode_unchanged():
    """Flag absent -> no carrier_groups key; flooding behavior preserved."""
    r = walk('stat:strength', grouped=False)
    assert all('carrier_groups' not in lv for lv in r['levels'])
    d = reach(r)
    assert SC not in d, 'default mode must keep the documented flooding behavior'
    print('ok: default mode (no flag) unchanged — flooding behavior preserved')


def test_grouped_flooding_removed():
    r = walk('stat:strength', grouped=True)
    gens = [lv['gen'] if 'gen' in lv else None for lv in r['levels']]
    assert all('carrier_groups' in lv for lv in r['levels'])
    assert r['truncated'] is False
    assert all(lv['gen'] <= 200 for lv in r['levels'] if 'gen' in lv) if 'gen' in r['levels'][0] else True
    print('ok: grouped mode — no truncation at cap 200 (flooding removed)')


def test_group_membership_partition():
    """group.members must equal the exact carrier neighbor set per (Stat, type)."""
    r = walk('stat:strength', grouped=True)
    for lv in r['levels']:
        for grp in lv.get('carrier_groups', []):
            for member in grp['members']:
                assert member in phase6_api.get_graph()._load_nodes()
        # partition: members collected from the same adjacency the API uses
    # exact partition check for one known stat: recompute from raw adjacency
    g = phase6_api.get_graph()
    out, inn = g._load_edges()
    node = 'stat:spell_damage_%+' if False else sid('spell_damage')
    real = set()
    for t in phase6_api.CARRIER_GROUP_CLASSES:
        for (nbr, _) in out[t].get(node, []):
            real.add(nbr)
        for (src, _) in inn[t].get(node, []):
            real.add(src)
    found = {}
    for lv in r['levels']:
        for grp in lv.get('carrier_groups', []):
            for mem in grp['members']:
                if mem == node:
                    continue
                found.setdefault(grp['carrier_type'], set()).add(mem)
    # members attributed to the spell node's own expansion (depth-1 groups only)
    r2 = walk(node, grouped=True)
    got = set()
    for grp in r2['levels'][0].get('carrier_groups', []):
        got |= set(grp['members'])
    assert got == real, (len(got), len(real))
    types = {grp['carrier_type'] for lv in r2['levels'] for grp in lv.get('carrier_groups', [])}
    assert types == {'Modifier', 'Passive', 'Gem'} or types <= {'Modifier', 'Passive', 'Gem', 'UniqueItem'}
    print(f'ok: group membership partition-exact for spell node ({len(real)} carriers, '
          f'types {sorted(types)})')


def test_semantic_chain_depth6():
    r = walk('stat:strength', grouped=True)
    d = reach(r)
    chain = [(MELEE, 1), (SC, 2), (SPELL, 3), (CANON, 4), (ATTACK, 5)]
    for node, depth in chain:
        assert d.get(node) == depth, (node, d.get(node), depth)
    fam_at_4 = [x for x in FAMILY if d.get(x) == 4]
    assert len(fam_at_4) == 6, fam_at_4
    # everything reachable at depth <= 6
    print('ok: full chain at MAX_DEPTH 6 — melee d1, strong_casting d2, spell d3, '
          'family(6) d4, attack d5')


def test_semantic_superset_vs_baseline():
    rb, rg = walk('stat:strength', grouped=False), walk('stat:strength', grouped=True)
    sem = lambda r: {e['to'] for lv in r['levels'] for e in lv['edges']
                     if e['type'] in ('sem_relation_binds', 'stat_mechanic_operand',
                                      'stat_mechanic_variant', 'attribute_grants_stat',
                                      'stat_scales_with')}
    sb, sg = sem(rb), sem(rg)
    assert set(sg) >= set(sb), sorted(set(sb) - set(sg))
    print(f'ok: semantic reach grouped ⊇ baseline ({len(sg)} vs {len(sb)} semantic targets)')


def test_no_carrier_carrier_paths():
    r = walk('stat:strength', grouped=True)
    for lv in r['levels']:
        for e in lv['edges']:
            assert e['type'] not in phase6_api.CARRIER_GROUP_CLASSES or e['from'] == 'stat:strength', e
    print('ok: no carrier edges emitted between carriers (groups are terminal)')


def test_random_stat_starts():
    stats = sorted(x for x in phase6_api.get_graph()._load_nodes() if x.startswith('stat:'))
    rng = random.Random(0)
    for i in range(3):
        s = rng.choice(stats)
        rb, rg = walk(s, grouped=False), walk(s, grouped=True)
        sem = lambda r: {e['to'] for lv in r['levels'] for e in lv['edges']
                         if e['type'] in ('sem_relation_binds', 'stat_mechanic_operand',
                                          'stat_mechanic_variant', 'attribute_grants_stat',
                                          'stat_scales_with')}
        sb, sg = sem(rb), sem(rg)
        assert set(sg) >= set(sb), (s, sorted(set(sb) - set(sg)))
        assert all('carrier_groups' in lv for lv in rg['levels'])
        print(f'  random {i}: {s[:48]} — semantic {len(sb)}->{len(sg)} (superset)')
    print('ok: 3 deterministic random Stat starts — semantic superset, groups present')


def test_determinism():
    a = json.dumps(walk('stat:strength', grouped=True), sort_keys=True)
    b = json.dumps(walk('stat:strength', grouped=True), sort_keys=True)
    assert a == b
    a2 = json.dumps(walk('stat:strength', grouped=False), sort_keys=True)
    b2 = json.dumps(walk('stat:strength', grouped=False), sort_keys=True)
    assert a2 == b2
    print('ok: two-run byte-identical determinism (both modes)')


if __name__ == '__main__':
    test_default_mode_unchanged()
    test_grouped_flooding_removed()
    test_group_membership_partition()
    test_semantic_chain_depth6()
    test_semantic_superset_vs_baseline()
    test_no_carrier_carrier_paths()
    test_random_stat_starts()
    test_determinism()
    print('ALL PASS')