#!/usr/bin/env python3
"""Phase 5S golden tests: sem_relation_binds (semantic binding extraction).

Run: python3 tools/tests/test_phase5s.py
Assert-based, mirrors test_phase1.py/test_phase6.py style. Read-only against
real cache/ artifacts except the write/idempotency test, which uses a temp DB.
Contract: docs/phase5s_semantic_binding_contract.json (v5S.1).
"""
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import phase5s_semantic_bind as sem

SANTA = Path(__file__).resolve().parents[2]
NODES_DB = SANTA / 'cache' / 'nodes.db'
MARKERS = json.loads((SANTA / 'cache' / 'semantic_markers.json').read_text())['markers']

tags = sem.load_tags()
node_ids = sem.load_node_ids()
stat_ids = sem.load_stat_ids()
label_index = sem.build_label_index()
edges, coverage = sem.extract_bindings(MARKERS, tags, label_index, node_ids, stat_ids)
cov = coverage['summary']


def test_normalization():
    assert sem.m1_forms('Physical Damage') == ['physical_damage']
    assert sem.m1_forms('Flasks') == ['flasks', 'flask']
    assert sem.m2_key('Mana.') == 'mana'
    assert sem.m2_key('  Base   Spell  Crit ') == 'base spell crit'
    print('ok: frozen normalization')


def test_resolve_participant():
    o = sem.resolve_participant('Flasks', tags, label_index, stat_ids)
    assert o[0] == 'M1_tag' and o[1] == 'tag:flask', o
    assert sem.resolve_participant('Mana', tags, label_index, stat_ids)[1] == 'tag:mana'
    assert sem.resolve_participant('Physical Damage', tags, label_index, stat_ids)[1] == 'tag:physical_damage'
    o = sem.resolve_participant('Attributes', tags, label_index, stat_ids)
    assert o[0] == 'M1_tag' and o[1] == 'tag:attribute' and o[2] == 'singular'
    assert sem.resolve_participant('the number of times to Chain', tags, label_index, stat_ids)[0] == 'unresolved'
    # M2b golds (5S.2): unique stat-grammar binds
    o = sem.resolve_participant('Melee Physical Damage', tags, label_index, stat_ids)
    assert o[0] == 'M2b_stat' and o[1] == 'stat:melee_physical_damage_+%', o
    o = sem.resolve_participant('all Spell Damage', tags, label_index, stat_ids)
    assert o[0] == 'M2b_stat' and o[1] == 'stat:spell_damage_+%', o
    # magnitude-tail rejection: non-tail continuations never bind
    assert sem.m2b_candidates('Spell Damage', ['spell_damage_taken_+%', 'spell_damage_+%']) == ['spell_damage_+%']
    # ambiguity gate: two tail-OK stats -> no binding
    assert sem.m2b_stat('Foo Bar', ['foo_bar_+%', 'foo_bar_%']) is None, 'ambiguity must not bind'
    # M2-label ambiguity case replaced by M2b: 'projectiles Fork' now binds uniquely via stat grammar
    o = sem.resolve_participant('projectiles Fork', tags, label_index, stat_ids)
    assert o[0] == 'M2b_stat' and o[1] == 'stat:projectiles_fork', o
    assert sem.resolve_participant('#%', tags, label_index, stat_ids)[0] == 'placeholder'
    idx = {'foo': {('stat:a', 'f.json'), ('stat:b', 'f.json')}}
    assert sem.resolve_participant('Foo', tags, idx, stat_ids)[0] == 'ambiguous'
    print('ok: M1/M2b/M2 resolution incl. tail rejection + ambiguity gates')


def test_edge_shape_invariants():
    assert edges, 'no semantic edges extracted'
    for (src, tgt, typ), e in edges.items():
        assert typ == 'sem_relation_binds'
        assert src.startswith('stat:') and src in node_ids
        assert tgt.startswith(('tag:', 'stat:')) and tgt in node_ids
        assert e['status'] in {'confirmed', 'resolved_not_validated'}
        assert e['tier'] == 'outside_this_vocabulary' and e['secondary'] is None
        assert e['prov'], 'every edge carries provenance'
    print(f'ok: shape invariants on {len(edges)} edges')


def test_blood_magic_family():
    bm = [e for (s, t, _), e in edges.items() if s == 'stat:keystone_blood_magic']
    tgts = {(s, t) for (s, t, _) in edges if s == 'stat:keystone_blood_magic'}
    assert ('stat:keystone_blood_magic', 'tag:mana') in tgts, 'SUPPRESS Mana missing'
    assert ('stat:keystone_blood_magic', 'tag:life') in tgts, 'SUBSTITUTE to Life missing'
    mana = edges[('stat:keystone_blood_magic', 'tag:mana', 'sem_relation_binds')]
    ops = {f['operator'] for f in mana['prov']}
    assert ops == {'SUPPRESS', 'SUBSTITUTE'}, ops
    assert len(mana['prov']) == 3, f'expected 3 merged prov facts, got {len(mana["prov"])}'
    assert all(f['matched'] == 'tag:mana' for f in mana['prov'])
    life = edges[('stat:keystone_blood_magic', 'tag:life', 'sem_relation_binds')]
    assert life['status'] == 'confirmed'
    print('ok: Blood Magic SUPPRESS + 2x SUBSTITUTE -> tag:mana/tag:life (merged prov)')


def test_eldritch_battery_attributes_survive():
    eb = edges[('stat:keystone_eldritch_battery', 'tag:energy_shield', 'sem_relation_binds')]
    orders = [f['relation_fields'].get('order') for f in eb['prov'] if f['relation_fields'].get('order')]
    assert orders and orders[0] == {'consumed_before': ['Energy Shield', 'Mana']}, orders
    assert eb['status'] == 'confirmed'
    print('ok: Eldritch Battery binds Mana->ES; order attribute preserved in provenance')


def test_all_or_nothing_redirect_dropped():
    sid = 'local_unique_jewel_life_increases_applies_to_mana_doubled'
    assert not any(s == 'stat:' + sid for (s, t, _) in edges), 'partial relation must emit nothing'
    drops = [r for r in coverage['participants'] if r['outcome'] == 'partial_binding_dropped']
    assert any(r['sid'] == sid for r in drops), drops[:5]
    print('ok: REDIRECT with one unbound side dropped (all-or-nothing)')


def test_zero_binding_markers():
    for sid in ('base_spell_critical_chance_equal_to_the_critical_strike_chance_of_main_weapon',
                'active_skill_beam_splits_instead_of_chaining'):
        assert not any(s == 'stat:' + sid for (s, t, _) in edges), sid
    print('ok: EQUAL + chain-REDIRECT markers emit nothing (gaps preserved)')


def test_prose_only_silent():
    prose = {m['sid'] for m in MARKERS if m.get('prose_only')}
    assert prose and not any(s.split(':', 1)[1] in prose for (s, t, _) in edges)
    print('ok: prose_only markers emit nothing')


def test_uncertainty_never_confirmed():
    n = 0
    for e in edges.values():
        for f in e['prov']:
            if 'classification_uncertainty' in f:
                n += 1
                assert e['status'] == 'resolved_not_validated', f
                assert f['classification_uncertainty'], 'uncertainty copied verbatim'
    print(f'ok: {n} uncertain-relation bindings capped at resolved_not_validated')


def test_write_idempotent_and_traversal():
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / 'edges.db'
        con = sqlite3.connect(db)
        con.execute("""CREATE TABLE edges (source_node_id TEXT NOT NULL,
            target_node_id TEXT NOT NULL, relationship_type TEXT NOT NULL,
            confidence_status TEXT NOT NULL, secondary_status TEXT, tier TEXT NOT NULL,
            provenance TEXT NOT NULL, PRIMARY KEY (source_node_id, target_node_id,
            relationship_type))""")
        con.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
        con.execute("INSERT INTO edges VALUES ('passive:royale_life_4','stat:attacks_use_life_in_place_of_mana','passive_grants_stat','confirmed',NULL,'1','[]')")
        # discovery substrate: mods tagged mana (reverse fan-out candidates at depth 2)
        con.execute("INSERT INTO edges VALUES ('mod:SyntheticManaUser','tag:mana','modifier_has_tag','confirmed',NULL,'2','[]')")
        con.execute("INSERT INTO edges VALUES ('mod:SyntheticManaMod2','tag:mana','modifier_has_tag','confirmed',NULL,'2','[]')")
        con.commit(); con.close()
        n1 = sem.write_db(edges, node_ids, db)
        h1 = sqlite3.connect(db).execute("SELECT value FROM meta WHERE key='sem_canonical_hash'").fetchone()[0]
        n2 = sem.write_db(edges, node_ids, db)
        h2 = sqlite3.connect(db).execute("SELECT value FROM meta WHERE key='sem_canonical_hash'").fetchone()[0]
        assert n1 == n2 == len(edges) and h1 == h2, 'write must be deterministic+idempotent'
        # structural rows untouched, reverse index exists
        con = sqlite3.connect(db)
        assert con.execute("SELECT count(*) FROM edges WHERE relationship_type='passive_grants_stat'").fetchone()[0] == 1
        assert con.execute("SELECT count(*) FROM sqlite_master WHERE name='idx_edges_target'").fetchone()[0] == 1
        con.close()
        # Phase 6 API traversal (temp edges db + real nodes db)
        sys.path.insert(0, str(SANTA / 'tools'))
        import phase6_api
        g = phase6_api.GraphDB(nodes_db=NODES_DB, edges_db=db)
        r = g.get_neighbour(1, {'start': 'stat:keystone_blood_magic',
                                'edge_types': ['sem_relation_binds']})
        got = {(e['to'], e['type']) for e in r['levels'][0]['edges']}
        assert ('tag:mana', 'sem_relation_binds') in got and ('tag:life', 'sem_relation_binds') in got
        # discovery fan-out depth 2: marker -> bound tag -> tagged mods (candidates)
        r2 = g.get_neighbour(2, {'start': 'stat:keystone_blood_magic',
                                 'edge_types': ['sem_relation_binds', 'modifier_has_tag'],
                                 'max_nodes_per_level': 200})
        mods2 = {e['to'] for e in r2['levels'][1]['edges']}
        assert 'mod:SyntheticManaUser' in mods2 and 'mod:SyntheticManaMod2' in mods2, \
            'reverse tag fan-out must produce candidates'
    print('ok: write idempotent; Phase 6 API traverses + fans out over sem_relation_binds')


if __name__ == '__main__':
    print(f"coverage summary: {json.dumps(cov)}")
    test_normalization()
    test_resolve_participant()
    test_edge_shape_invariants()
    test_blood_magic_family()
    test_eldritch_battery_attributes_survive()
    test_all_or_nothing_redirect_dropped()
    test_zero_binding_markers()
    test_prose_only_silent()
    test_uncertainty_never_confirmed()
    test_write_idempotent_and_traversal()
    print('ALL PASS')