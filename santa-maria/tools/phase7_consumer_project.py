#!/usr/bin/env python3
"""Consumer/mechanic graph projection (contract pilot-1) — behind a feature flag.

Materializes the VALID relationships from the consumer-extraction pilots as
Mechanic nodes + stat_mechanic_relation edges (Stat -> Mechanic), following the
approved minimal contract (docs/experiments/phase7_consumer_graph_contract/).

Fail-closed: an edge is emitted only if the stat id (a) is classified VALID with
emit=true in the versioned artifact, (b) exists as a Stat node, and (c) is still
attached to >=1 mod in data/repoe/mods.json. AMBIGUOUS/INVALID/monster-domain
rows emit nothing.

Idempotent: deletes its own rows (mechanic:* nodes, stat_mechanic_relation
edges) and rewrites meta keys consumer_* before inserting. No timestamps —
output is bit-reproducible.

Usage:
  python3 phase7_consumer_project.py            # project + verify
  python3 phase7_consumer_project.py --report   # + counts by family/role
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parent
SANTA = TOOL.parent
CACHE = SANTA / 'cache'
DATA = SANTA / 'data'
ARTIFACT = TOOL / 'sources' / 'consumer_mechanics.json'

NODE_TYPE = 'Mechanic'
EDGE_TYPE = 'stat_mechanic_relation'
META_PREFIX = 'consumer_'


def project(report=False):
    art = json.loads(ARTIFACT.read_text())
    version = art['version']
    assert art['contract'] == 'consumer_mechanics_projection'

    mods = json.load(open(DATA / 'repoe' / 'mods.json'))
    hosts = {}
    for k, v in mods.items():
        for s in v['stats']:
            hosts.setdefault(s['id'], []).append(k)

    con = sqlite3.connect(CACHE / 'nodes.db')
    stats = {r[0] for r in con.execute("select node_id from nodes where type='Stat'")}
    con.execute("delete from nodes where node_id like 'mechanic:%'")
    mechanics = []
    for token, meta in art['mechanics'].items():
        payload = json.dumps({'kind': 'mechanic', 'token': token,
                              'description': meta['description'],
                              'contract_version': version},
                             ensure_ascii=False, sort_keys=True)
        con.execute("insert into nodes(node_id, type, payload) values (?,?,?)",
                    (f'mechanic:{token}', NODE_TYPE, payload))
        mechanics.append(f'mechanic:{token}')
    con.commit()
    con.close()

    con = sqlite3.connect(CACHE / 'edges.db')
    con.execute("delete from edges where relationship_type=?", (EDGE_TYPE,))
    edges, skipped = [], []
    for c in art['classifications']:
        if not c.get('emit'):
            if c['verdict'] == 'VALID':
                skipped.append((c['stat_id'], c['scope']))
            continue
        sid = c['stat_id']
        nid = f'stat:{sid}'
        if nid not in stats or not hosts.get(sid):
            skipped.append((sid, 'fail-closed: missing stat node or attachment'))
            continue
        prov = [{'source_file': 'tools/sources/consumer_mechanics.json',
                 'field': 'stat_id', 'stat_id': sid, 'family': c['family'],
                 'role': c['role'], 'state_owner': c['state_owner'],
                 'label': c['label'], 'hosting_mods': len(hosts[sid]),
                 'attribute': c.get('attribute'),
                 'relation': c['relation'],
                 'rule_id': 'stat_id_grammar_pilot',
                 'contract_version': version}]
        edges.append((nid, f"mechanic:{c['family']}", EDGE_TYPE,
                      'confirmed_source_backed', None,
                      'outside_this_vocabulary',
                      json.dumps(prov, ensure_ascii=False, sort_keys=True)))
    con.executemany("insert into edges(source_node_id, target_node_id, "
                    "relationship_type, confidence_status, secondary_status, "
                    "tier, provenance) values (?,?,?,?,?,?,?)", edges)
    con.execute("insert or replace into meta(key, value) values (?,?)",
                (META_PREFIX + 'version', version))
    con.execute("insert or replace into meta(key, value) values (?,?)",
                (META_PREFIX + 'edges', str(len(edges))))
    con.execute("insert or replace into meta(key, value) values (?,?)",
                (META_PREFIX + 'mechanics', str(len(mechanics))))
    con.commit()
    con.close()

    print(f'consumer projection: {len(mechanics)} mechanic nodes, '
          f'{len(edges)} {EDGE_TYPE} edges (contract {version})')
    if skipped:
        print(f'  not emitted: {len(skipped)} '
              f'(monster/tower domain or fail-closed)')
    if report:
        from collections import Counter
        pc = Counter(json.loads(e[6])[0]['role'] for e in edges)
        fc = Counter(e[1] for e in edges)
        print('  by role:', dict(sorted(pc.items())))
        print('  by mechanic:', dict(sorted(fc.items())))
    return len(mechanics), len(edges)


def verify():
    """Assert the projection matches the artifact exactly (no drift, no dups)."""
    art = json.loads(ARTIFACT.read_text())
    expect = {c['stat_id'] for c in art['classifications'] if c.get('emit')}
    con = sqlite3.connect(CACHE / 'edges.db')
    rows = con.execute("select source_node_id, target_node_id, provenance from edges "
                       "where relationship_type=?", (EDGE_TYPE,)).fetchall()
    got = {r[0][5:] for r in rows}
    assert got == expect, f'set drift: +{sorted(got - expect)[:3]} -{sorted(expect - got)[:3]}'
    assert len(rows) == len(expect), 'duplicate edges present'
    for src, tgt, prov in rows:
        p = json.loads(prov)[0]
        assert all(k in p for k in ('role', 'state_owner', 'family', 'label',
                                    'hosting_mods', 'relation', 'rule_id',
                                    'contract_version', 'source_file')), src
    mcon = sqlite3.connect(CACHE / 'nodes.db')
    mechs = {r[0] for r in mcon.execute(
        "select node_id from nodes where type='Mechanic'")}
    assert mechs == {f'mechanic:{t}' for t in art['mechanics']}, mechs
    print(f'verify ok: {len(rows)} edges, {len(mechs)} mechanic nodes, '
          f'provenance complete, no duplicates')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--report', action='store_true')
    ap.add_argument('--verify-only', action='store_true')
    a = ap.parse_args()
    if not a.verify_only:
        project(report=a.report)
    verify()
