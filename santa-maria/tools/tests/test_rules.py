#!/usr/bin/env python3
"""Phase 5R intrinsic rules — assert-based tests.

Run: python3 tools/tests/test_rules.py
Covers: rule-node/edge projection matches the sources (artifact + PoB Lua
anchors), artifact/attribute_grants_stat operand consistency, idempotent
re-projection, and the LLM-facing retrieval path: probing an encountered
stat/tag through carriers()/neighbour/resolve surfaces its intrinsic rules
in the standard envelope — with no rule flooding on unrelated entities.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import phase5r_rules as R5
import phase6_api as api
import phase8_research as R

EXPECTED_RULES = {
    'rule:strength_life', 'rule:strength_melee_physical_damage',
    'rule:dexterity_accuracy', 'rule:dexterity_evasion',
    'rule:intelligence_mana', 'rule:intelligence_energy_shield',
    'rule:chaos_damage_bypasses_energy_shield',
    'rule:energy_shield_recharge_delay',
}


def test_rule_nodes_complete():
    g = api.get_graph()
    nodes = g._load_nodes()
    rules = {nid: p for nid, (t, p) in nodes.items() if t == 'Rule'}
    assert set(rules) == EXPECTED_RULES, set(rules) ^ EXPECTED_RULES
    for nid, p in rules.items():
        assert p.get('name'), nid
        assert p.get('kind') == 'intrinsic_rule', nid
        src = p.get('source') or []
        assert src and src[0].get('file'), nid
        assert p.get('pob_commit') or p.get('artifact_commit'), nid
    # rule names are human statements, resolvable without knowing ids
    env = R.resolve('per 2 Intelligence', type='Rule')
    assert 'rule:intelligence_mana' in {r['id'] for r in env['results']}, env
    env = R.resolve('bypasses Energy Shield', type='Rule')
    assert [r['id'] for r in env['results']] == \
        ['rule:chaos_damage_bypasses_energy_shield'], env
    print('ok: 8 rule nodes, names are resolvable human statements')


def test_rule_edges_shape():
    econ = __import__('sqlite3').connect(
        Path(__file__).resolve().parents[2] / 'cache' / 'edges.db')
    edges = econ.execute("select source_node_id, target_node_id, "
                         "relationship_type from edges where relationship_type "
                         "like 'rule_%'").fetchall()
    applies = {(s, t) for s, t, et in edges if et == 'rule_applies_to'}
    negated = {(s, t) for s, t, et in edges if et == 'rule_negated_by'}
    assert ('rule:intelligence_mana', 'stat:base_maximum_mana') in applies
    assert ('rule:intelligence_mana', 'stat:intelligence') in applies
    assert ('rule:chaos_damage_bypasses_energy_shield', 'tag:chaos') in applies
    assert ('rule:chaos_damage_bypasses_energy_shield',
            'stat:maximum_energy_shield') in applies
    assert ('rule:chaos_damage_bypasses_energy_shield',
            'stat:chaos_damage_does_not_bypass_energy_shield') in negated
    assert ('rule:intelligence_mana',
            'stat:gain_no_maximum_mana_from_intelligence') in negated
    assert all(s.startswith('rule:') for s, _t in
               [(s, t) for s, t, _e in edges]), 'rule edges are rule -> other'
    assert not [(s, t) for s, t, et in edges if et == 'rule_modified_by'], \
        'no modified_by edges are sourced yet'
    # artifact/edge operand consistency (rule view vs canonical traversal edges)
    ags = {(s, t) for s, t in econ.execute(
        "select source_node_id, target_node_id from edges "
        "where relationship_type='attribute_grants_stat'")}
    art = json.loads((Path(__file__).resolve().parents[2] / 'tools' / 'sources'
                      / 'pob_attribute_mechanics.json').read_text())
    for m in art['mechanics']:
        assert (R5.ATTR_STAT[m['attribute']], 'stat:' + m['target_stat']) in ags
    print(f'ok: {len(edges)} rule edges, shape + artifact consistency')


def test_llm_path_carriers_surfaces_rules():
    # resource side: probing the pool stat returns the conversion edge AND the
    # rule with its exceptions, in the standard envelope
    env = R.carriers('stat:base_maximum_mana')
    assert env['error'] is None, env
    rows = {r['carrier']: r['edge_type'] for r in env['results']}
    assert rows.get('stat:intelligence') == 'attribute_grants_stat', rows
    assert rows.get('rule:intelligence_mana') == 'rule_applies_to', rows
    rule_rows = [r for r in env['results'] if r['carrier'] == 'rule:intelligence_mana']
    assert rule_rows[0]['name'] == '1 Mana per 2 Intelligence'
    assert rule_rows[0]['rule']['operands'] == {
        'attribute': 'stat:intelligence',
        'attribute_quantity_nodes': ['stat:base_intelligence',
                                     'stat:additional_intelligence'],
        'resource': 'stat:base_maximum_mana'}
    # the negating exception is reachable from the rule side via neighbour
    # (carriers is reverse-only; rules are edge sources, so their content is
    # traversed outward — an empty carriers() on a rule node is a true fact)
    env = R.carriers('rule:intelligence_mana')
    assert env['error'] is None and env['results'] == []
    env = api.get_neighbour(1, {'start': 'rule:intelligence_mana'})
    rows = {e['to']: e['type'] for lv in env['levels'] for e in lv['edges']}
    assert rows.get('stat:gain_no_maximum_mana_from_intelligence') == \
        'rule_negated_by', rows
    assert rows.get('stat:base_maximum_mana') == 'rule_applies_to', rows
    # and from the exception stat side, carriers() surfaces the rule that
    # this stat negates
    env = R.carriers('stat:gain_no_maximum_mana_from_intelligence')
    rows = {r['carrier']: r['edge_type'] for r in env['results']}
    assert rows.get('rule:intelligence_mana') == 'rule_negated_by', rows
    # chaos: probing the damage-type tag surfaces the default rule
    env = R.carriers('tag:chaos')
    rows = {r['carrier'] for r in env['results']}
    assert 'rule:chaos_damage_bypasses_energy_shield' in rows
    env = api.get_neighbour(1, {'start': 'rule:chaos_damage_bypasses_energy_shield'})
    rows = {e['to']: e['type'] for lv in env['levels'] for e in lv['edges']}
    assert rows.get('tag:chaos') == 'rule_applies_to'
    assert rows.get('stat:maximum_energy_shield') == 'rule_applies_to'
    assert rows.get('stat:chaos_damage_does_not_bypass_energy_shield') == \
        'rule_negated_by'
    print('ok: carriers() surfaces intrinsic rules on encountered entities '
          '(pool stat, attribute, chaos tag, rule nodes)')


def test_no_rule_flooding_on_unrelated_entities():
    # rules must appear only where they apply — bounded by connectivity
    env = R.carriers('stat:critical_strike_chance_+%')
    assert env['meta']['counts'].get('rule_applies_to', 0) == 0
    assert env['meta']['counts'].get('rule_negated_by', 0) == 0
    assert not any(r['carrier'].startswith('rule:') for r in env['results'])
    g = api.get_graph()
    nodes = g._load_nodes()
    stats = sorted(nid for nid, (t, _p) in nodes.items() if t == 'Stat')
    flooded = []
    for s in stats:
        env = R.carriers(s)
        n = env['meta']['counts'].get('rule_applies_to', 0) + \
            env['meta']['counts'].get('rule_negated_by', 0)
        if n > 2:
            flooded.append((s, n))
    assert not flooded, f'unexpected rule flooding: {flooded[:5]}'
    print(f'ok: no rule flooding across {len(stats)} stats (max 2 rule rows per stat)')


def test_neighbour_traverses_rules():
    r = api.get_neighbour(1, {'start': 'stat:intelligence',
                              'max_nodes_per_level': 50})
    reached = {e['to'] for lv in r['levels'] for e in lv['edges']}
    assert 'rule:intelligence_mana' in reached, reached
    assert 'stat:base_maximum_mana' in reached
    # BFS continues through rule nodes. stat:base_maximum_mana has ~200 mod
    # carriers, so an unfiltered depth-2 BFS truncates before the rule rows
    # (reported via meta) — the documented refinement is to focus edge types.
    r = api.get_neighbour(2, {'start': 'stat:base_maximum_mana',
                              'edge_types': ['rule_applies_to',
                                             'rule_negated_by',
                                             'attribute_grants_stat']})
    assert not r['truncated'], r['truncated']
    d = {}
    for lv in r['levels']:
        for e in lv['edges']:
            d.setdefault(e['to'], lv['depth'])
    assert d.get('rule:intelligence_mana') == 1
    assert d.get('stat:gain_no_maximum_mana_from_intelligence') == 2
    print('ok: neighbour traverses rule edges in both directions; '
          'focused BFS reaches exceptions at depth 2')


def test_idempotent_reprojection():
    def counts():
        con = __import__('sqlite3').connect(
            Path(__file__).resolve().parents[2] / 'cache' / 'edges.db')
        n = con.execute("select count(*) from edges where relationship_type "
                        "like 'rule_%'").fetchone()[0]
        con.close()
        ncon = __import__('sqlite3').connect(
            Path(__file__).resolve().parents[2] / 'cache' / 'nodes.db')
        m = ncon.execute("select count(*) from nodes where type='Rule'").fetchone()[0]
        ncon.close()
        return n, m
    before = counts()
    R5.project()
    R5.verify()
    assert counts() == before, 're-projection must be idempotent'
    print('ok: re-projection idempotent (same rule node/edge counts)')


if __name__ == '__main__':
    test_rule_nodes_complete()
    test_rule_edges_shape()
    test_llm_path_carriers_surfaces_rules()
    test_no_rule_flooding_on_unrelated_entities()
    test_neighbour_traverses_rules()
    test_idempotent_reprojection()
    print('ALL TESTS PASSED')
