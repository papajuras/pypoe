#!/usr/bin/env python3
"""Phase 5M — applies-to mechanic projection (default pipeline).

Projects the "X also applies to Y at Z% of their value" bridge class as
first-class LLM-readable facts:

  mechanic:applies_to_<id>  nodes   payload carries input family, output,
                                    value, members, pob_flag, provenance
  stat_mechanic_relation    edges   BOTH sides of every bridge:
                                      member/output stat -> mechanic (role=output)
                                      operand/input stat -> mechanic (role=input)

Sources (both committed, auditable artifacts):
  tools/sources/pob_stat_mechanics.json     9 audited PoB mechanics (contract 5.7)
  tools/sources/applies_to_mechanics.json   mechanically generated sweep
                                            (generate_applies_to.py)

stat_mechanic_operand / stat_mechanic_variant (phase 5, structural) stay
untouched as supporting data; this phase owns only the canonical LLM-facing
stat_mechanic_relation rows for the applies_to namespace, plus the
mechanic:applies_to_* nodes. Deletes are scoped to that namespace, so the
phase 7C consumer projection and this projection are order-safe.

Idempotent: deletes its own rows and rewrites meta keys applies_to_* before
inserting. No timestamps — bit-reproducible.

Usage:
  python3 phase5m_applies_to.py            # project + verify
  python3 phase5m_applies_to.py --report   # + per-mechanic listing
  python3 phase5m_applies_to.py --verify-only
"""
import argparse
import json
import sqlite3
from pathlib import Path

TOOL = Path(__file__).resolve().parent
SANTA = TOOL.parent
CACHE = SANTA / 'cache'
AUDITED = TOOL / 'sources' / 'pob_stat_mechanics.json'
GENERATED = TOOL / 'sources' / 'applies_to_mechanics.json'

META_PREFIX = 'applies_to_'
NODE_NS = 'mechanic:applies_to_'
RELATION = 'stat_mechanic_relation'


def _pct(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return f'{round(value * 100) if value <= 1 else round(value)}% of value'
    return str(value)


def _operand_words(sid):
    if not sid:
        return None
    w = sid.split(':', 1)[1].replace('_+%', '').replace('_', ' ')
    return w


def _words(camel):
    """CamelCase PoB field name -> lower-case words ('EnergyShieldRecharge'
    -> 'energy shield recharge')."""
    import re as _re
    return _re.sub(r'(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])', ' ',
                   camel).lower()


def _mechanic_payload(entry, artifact_rel, commit):
    """LLM-readable payload: input family, output, value, members,
    provenance — no stat-id decoding required. The description asserts only
    VERIFIED parts (bound operand/product/handler); when nothing beyond the
    name is bound, the description is the name itself (which, for
    translation-equality entries, is the real game wording)."""
    op = entry.get('operand_stat')
    prod = entry.get('product_stat')
    h = entry.get('handler') or {}
    value = _pct(entry.get('value'))
    name = None
    for m in entry.get('members', []):
        if str(m.get('evidence', '')).startswith('stat_translations'):
            name = m['stat'].split(':', 1)[1].replace('_', ' ')
            break
    if name is None:
        name = entry['pob_flag']
        for pat, repl in (('AppliesTo', ' applies to '),
                          ('Applies', ' applies '),
                          ('TransfigurationOf', ' Transfiguration of ')):
            name = name.replace(pat, repl)
    name = name[0].upper() + name[1:]
    d = f'increases and reductions to {_operand_words(op)}' if op else None
    out = _operand_words(prod) if prod else \
        (_words(h['output_field']) if h.get('output_field') else None)
    desc = None
    if d and out:
        desc = f'{d} also apply to {out}'
    elif out and (op or prod):
        desc = f'also applies to {out}'
    if desc and value:
        desc += f' at {value}'
    if not desc:
        desc = name
    payload = {
        'kind': 'mechanic',
        'name': name,
        'description': desc,
        'input': {'operand_stat': op,
                  'mod_field': h.get('operand_field'),
                  'evidence': entry.get('operand_evidence')},
        'output': {'product_stat': prod,
                   'mod_field': h.get('output_field'),
                   'modflag': h.get('output_modflag')},
        'value': value,
        'members': entry.get('members', []),
        'pob_flag': entry['pob_flag'],
        'provenance': {
            'source_file': artifact_rel,
            'pob_flag': entry['pob_flag'],
            'pattern_lines': entry.get('pattern_lines'),
            'handler': h or None,
            'source_version': commit,
        },
    }
    return {k: v for k, v in payload.items() if v is not None}


def project(report=False):
    aud = json.loads(AUDITED.read_text())
    gen = json.loads(GENERATED.read_text())
    commit = gen['provenance']['pob_commit']

    entries = []
    for m in aud['mechanics']:
        e = dict(m)
        e.setdefault('pattern_lines', None)
        e['_artifact'] = 'tools/sources/pob_stat_mechanics.json'
        e['_class'] = aud['provenance']['provenance_class']
        entries.append(e)
    for m in gen['mechanics']:
        e = dict(m)
        e['_artifact'] = 'tools/sources/applies_to_mechanics.json'
        e['_class'] = gen['provenance']['provenance_class']
        entries.append(e)

    con = sqlite3.connect(CACHE / 'nodes.db')
    stats = {r[0] for r in con.execute("select node_id from nodes where type='Stat'")}
    con.execute("delete from nodes where node_id like ?", (NODE_NS + '%',))
    nodes = []
    for e in entries:
        nid = NODE_NS + e['id']
        payload = _mechanic_payload(e, e['_artifact'], commit)
        nodes.append((nid, 'Mechanic',
                      json.dumps(payload, ensure_ascii=False, sort_keys=True)))
    con.executemany("insert into nodes(node_id, type, payload) values (?,?,?)", nodes)
    con.commit()
    con.close()

    con = sqlite3.connect(CACHE / 'edges.db')
    con.execute("delete from edges where relationship_type=? and "
                "target_node_id like ?", (RELATION, NODE_NS + '%'))
    edges, skipped = [], []
    for e in entries:
        nid = NODE_NS + e['id']
        base_prov = {'source_file': e['_artifact'], 'mechanic_id': e['id'],
                     'pob_flag': e['pob_flag'],
                     'provenance_class': e['_class']}
        for m in e.get('members', []):
            sid = m['stat'] if m['stat'].startswith('stat:') else 'stat:' + m['stat']
            if sid not in stats:
                skipped.append((nid, sid, 'missing stat node'))
                continue
            prov = dict(base_prov, role='output', member_role=m.get('role'),
                        value=m.get('value'), condition=m.get('condition'),
                        evidence=m.get('evidence'))
            edges.append((sid, nid, RELATION, 'confirmed_source_backed', None,
                          'outside_this_vocabulary',
                          json.dumps([prov], ensure_ascii=False, sort_keys=True)))
        op = e.get('operand_stat')
        if op:
            sid = op if op.startswith('stat:') else 'stat:' + op
            if sid not in stats:
                skipped.append((nid, sid, 'missing operand stat node'))
            else:
                prov = dict(base_prov, role='input',
                            evidence=e.get('operand_evidence'))
                edges.append((sid, nid, RELATION, 'confirmed_source_backed', None,
                              'outside_this_vocabulary',
                              json.dumps([prov], ensure_ascii=False, sort_keys=True)))
    con.executemany("insert into edges(source_node_id, target_node_id, "
                    "relationship_type, confidence_status, secondary_status, "
                    "tier, provenance) values (?,?,?,?,?,?,?)", edges)
    con.execute("insert or replace into meta(key, value) values (?,?)",
                (META_PREFIX + 'version', '1'))
    con.execute("insert or replace into meta(key, value) values (?,?)",
                (META_PREFIX + 'nodes', str(len(nodes))))
    con.execute("insert or replace into meta(key, value) values (?,?)",
                (META_PREFIX + 'relations', str(len(edges))))
    con.commit()
    con.close()

    print(f'applies-to projection: {len(nodes)} mechanic nodes, {len(edges)} '
          f'{RELATION} edges (input + output sides)')
    if skipped:
        print(f'  skipped: {skipped}')
    if report:
        con = sqlite3.connect(CACHE / 'nodes.db')
        for nid, payload in con.execute(
                "select node_id, payload from nodes where node_id like ? "
                "order by node_id", (NODE_NS + '%',)):
            p = json.loads(payload)
            print(f"  {nid} — {p['name']}")
            print(f"    {p.get('description')}")
        con.close()
    return len(nodes), len(edges)


def verify():
    aud = json.loads(AUDITED.read_text())
    gen = json.loads(GENERATED.read_text())
    expect_nodes = {NODE_NS + m['id'] for m in aud['mechanics']} | \
                   {NODE_NS + m['id'] for m in gen['mechanics']}
    con = sqlite3.connect(CACHE / 'nodes.db')
    got = {r[0] for r in con.execute(
        "select node_id from nodes where node_id like ?", (NODE_NS + '%',))}
    assert got == expect_nodes, f'node drift: +{sorted(got - expect_nodes)[:3]} ' \
                                f'-{sorted(expect_nodes - got)[:3]}'
    for nid, payload in con.execute(
            "select node_id, payload from nodes where node_id like ?",
            (NODE_NS + '%',)):
        p = json.loads(payload)
        assert p.get('kind') == 'mechanic' and p.get('name'), nid
        assert p.get('description') and p.get('members') is not None, nid
        assert p.get('provenance', {}).get('source_file'), nid
    # fixtures are asserted in tests/test_applies_to.py (the projection code
    # must not name specific mechanics — generic sweep invariant)
    econ = sqlite3.connect(CACHE / 'edges.db')
    rel = econ.execute(
        "select source_node_id, target_node_id, provenance from edges "
        "where relationship_type=? and target_node_id like ?",
        (RELATION, NODE_NS + '%')).fetchall()
    by_mech = {}
    for src, tgt, prov in rel:
        by_mech.setdefault(tgt, []).append((src, json.loads(prov)[0]))
    n_out = sum(1 for rows in by_mech.values() for _s, p in rows
                if p['role'] == 'output')
    n_in = sum(1 for rows in by_mech.values() for _s, p in rows
               if p['role'] == 'input')
    assert n_in > 0, 'no input-side relations projected'
    assert n_out >= len(got), 'output-side relations missing'
    print(f'verify ok: {len(got)} mechanic nodes, {len(rel)} relation edges '
          f'({n_in} input-side, {n_out} output-side), payloads complete')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--report', action='store_true')
    ap.add_argument('--verify-only', action='store_true')
    a = ap.parse_args()
    if not a.verify_only:
        project(report=a.report)
    verify()
