#!/usr/bin/env python3
"""Consumer projection (contract pilot-1) — read-only assert tests.

Run: python3 tools/tests/test_consumer_projection.py
Covers: artifact integrity (verdict/role/owner/emit counts pinned from the
pilots); graph/artifact set equality via phase7_consumer_project.verify();
role preservation in DB edges; AMBIGUOUS/INVALID/artifact absence; provenance
completeness; API reachability of mechanic:ignite with distinguishable roles.
Requires the projection to be materialized (run the pipeline with
--consumer-projection first).
"""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import phase6_api as api
import phase7_consumer_project as cp

ROLES = {'consumer', 'trigger', 'conditional', 'immunity', 'generator',
         'negate', 'effect', 'redirect', 'scaling'}


def test_artifact_integrity():
    art = json.load(open(cp.ARTIFACT))
    cls = art['classifications']
    assert art['version'] == 'pilot-1' and len(art['mechanics']) == 6
    v = {r['verdict'] for r in cls}
    assert v <= {'VALID', 'AMBIGUOUS', 'INVALID'}, v
    counts = {x: sum(1 for r in cls if r['verdict'] == x) for x in v}
    assert counts == {'VALID': 752, 'AMBIGUOUS': 9, 'INVALID': 7}, counts
    emit = [r for r in cls if r.get('emit')]
    assert len(emit) == 716, len(emit)
    assert all(r['role'] in ROLES for r in emit), 'role outside allowed set'
    assert all(r['state_owner'] in set(art['state_owner_values']) | {None}
               for r in emit), 'state_owner outside allowed set'
    assert all(r['state_owner'] is None for r in emit if r['role'] == 'scaling')
    ids = [r['stat_id'] for r in cls]
    assert len(ids) == len(set(ids)), 'duplicate stat classifications'
    print('ok: artifact integrity (768 rows, 752 VALID, 716 emit, roles/owners valid)')


def test_graph_matches_artifact():
    cp.verify()  # set equality + provenance completeness + no duplicates
    con = sqlite3.connect(cp.CACHE / 'edges.db')
    rows = con.execute("select source_node_id, provenance from edges "
                       "where relationship_type=?", (cp.EDGE_TYPE,)).fetchall()
    by_role = {}
    for src, prov in rows:
        p = json.loads(prov)[0]
        by_role.setdefault(p['role'], []).append(src)
    assert sorted(by_role) == sorted(ROLES), sorted(by_role)
    expect = {c['stat_id']: c['role'] for c in
              json.load(open(cp.ARTIFACT))['classifications'] if c.get('emit')}
    for role, srcs in by_role.items():
        assert all(expect[s[5:]] == role for s in srcs), role
    excluded = {c['stat_id'] for c in json.load(open(cp.ARTIFACT))['classifications']
                if not c.get('emit')}
    got = {s[5:] for s, _ in rows}
    assert not (got & excluded), 'AMBIGUOUS/INVALID/monster-domain leaked into edges'
    print(f'ok: graph matches artifact; roles preserved '
          f'({ {k: len(v) for k, v in sorted(by_role.items())} }); '
          f'excluded rows absent')


def test_api_smoke():
    g = api.GraphDB()
    r = g.get_neighbour(1, {'start': 'mechanic:ignite', 'include_provenance': True,
                            'max_nodes_per_level': 200})
    edges = [e for lv in r['levels'] for e in lv['edges']]
    assert len(edges) == 127 and not r['truncated'], (len(edges), r['truncated'])
    assert all(e['type'] == 'stat_mechanic_relation' for e in edges)
    roles = {e['provenance']['role'] for e in edges}
    assert roles == {'consumer', 'trigger', 'conditional', 'immunity',
                     'generator', 'negate', 'effect'}, roles
    owners = {e['provenance']['state_owner'] for e in edges}
    assert owners <= {'enemy', 'self', 'event'}, owners
    cons = [e['to'] for e in edges if e['provenance']['role'] == 'consumer'
            and e['provenance']['state_owner'] == 'enemy']
    assert 'stat:damage_+%_vs_ignited_enemies' in cons
    print('ok: API smoke — mechanic:ignite fan-out 127, roles/owners distinguishable')


if __name__ == '__main__':
    test_artifact_integrity()
    test_graph_matches_artifact()
    test_api_smoke()
    print('ALL TESTS PASSED')
