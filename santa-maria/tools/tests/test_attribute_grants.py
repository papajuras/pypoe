#!/usr/bin/env python3
"""Round A golden tests: pinned attribute-mechanics source + attribute_grants_stat.

Run: python3 tools/tests/test_attribute_grants.py
Read-only against real cache/ artifacts (plus the committed source artifact).
Contract 5.6; provenance_class audited_pinned_external_source.
"""
import json
import sqlite3
from pathlib import Path

SANTA = Path(__file__).resolve().parents[2]
ARTIFACT = SANTA / 'tools' / 'sources' / 'pob_attribute_mechanics.json'
EDGES_DB = SANTA / 'cache' / 'edges.db'
MARKERS = json.loads((SANTA / 'cache' / 'semantic_markers.json').read_text())

art = json.loads(ARTIFACT.read_text())
con = sqlite3.connect(f"file:{EDGES_DB}?mode=ro", uri=True)

EXPECTED = {
    ('stat:strength', 'stat:melee_physical_damage_+%'),
    ('stat:strength', 'stat:base_maximum_life'),
    ('stat:dexterity', 'stat:accuracy_rating'),
    ('stat:dexterity', 'stat:evasion_rating_+%'),
    ('stat:intelligence', 'stat:base_maximum_mana'),
    ('stat:intelligence', 'stat:maximum_energy_shield_+%'),
}


def test_artifact_shape():
    p = art['provenance']
    assert p['provenance_class'] == 'audited_pinned_external_source'
    assert p['pob_commit'] and p['source_file'] == 'src/Modules/CalcPerform.lua'
    assert p['function'] == 'doActorAttribsConditions' and p['lines']
    assert len(art['mechanics']) == 6
    print('ok: artifact shape (6 mechanics, audited_pinned_external_source provenance)')


def test_no_iron_will_semantics():
    # semantic test: no mechanic ENTRY (id/attribute/target_stat/pob_mod) may
    # refer to Iron Will / strong_casting / strDmgBonus; documentation prose
    # elsewhere in the artifact is allowed.
    banned = ('iron will', 'iron_will', 'strong_casting', 'strong casting', 'strdmgbonus')
    for mech in art['mechanics']:
        entry = json.dumps({'id': mech['id'], 'attribute': mech['attribute'],
                            'target_stat': mech['target_stat'],
                            'pob_mod': mech['pob_mod']})
        low = entry.casefold()
        for b in banned:
            assert b not in low, (mech['id'], b)
    assert {m['id'] for m in art['mechanics']} == {
        'strength_melee_physical_damage', 'strength_life', 'dexterity_accuracy',
        'dexterity_evasion', 'intelligence_mana', 'intelligence_energy_shield'}
    print('ok: no mechanic entry refers to Iron Will / strong_casting / strDmgBonus')


def test_edges_exact():
    rows = con.execute(
        "SELECT source_node_id, target_node_id, confidence_status, provenance "
        "FROM edges WHERE relationship_type='attribute_grants_stat'").fetchall()
    pairs = {(s, t) for s, t, _, _ in rows}
    assert pairs == EXPECTED, pairs ^ EXPECTED
    assert len(rows) == 6
    for s, t, status, prov in rows:
        assert status == 'confirmed_source_backed'
        f = json.loads(prov)[0]
        assert f['provenance_class'] == 'audited_pinned_external_source'
        assert f['source_version'] == art['provenance']['pob_commit']
        assert f['source_file'] == 'tools/sources/pob_attribute_mechanics.json'
        assert f['formula'] and f['ratio'] and f['pob_source_file'] and f['pob_lines']
    print('ok: 6 attribute_grants_stat edges, exact endpoints + provenance')


def test_artifact_edge_consistency():
    # every artifact fact yields exactly one edge; no extra attribute edges
    for mech in art['mechanics']:
        n = con.execute(
            "SELECT count(*) FROM edges WHERE relationship_type='attribute_grants_stat' "
            "AND source_node_id=? AND target_node_id=?",
            ('stat:' + mech['attribute'], 'stat:' + mech['target_stat'])).fetchone()[0]
        assert n == 1, mech['id']
    assert con.execute("SELECT count(*) FROM edges WHERE relationship_type='attribute_grants_stat'").fetchone()[0] == len(art['mechanics'])
    print('ok: artifact <-> edges 1:1 consistency')


def test_no_other_attribute_edges():
    n = con.execute("SELECT count(*) FROM edges WHERE relationship_type='attribute_grants_stat' "
                    "AND (source_node_id LIKE '%strong%' OR target_node_id LIKE '%strong%' "
                    "OR source_node_id='stat:iron_will' OR target_node_id LIKE '%iron%')").fetchone()[0]
    assert n == 0
    print('ok: no Iron Will / strong_casting edges in the attribute layer')


def test_4m_vocabulary_correction():
    sc = next(m for m in MARKERS['markers'] if m['sid'] == 'strong_casting')
    f = sc['relations'][0]['fields']
    assert f['from'] == 'Melee Physical Damage', f
    assert f['to'] == 'all Spell Damage'
    assert len(MARKERS['markers']) == 201 and MARKERS['meta']['relations_total'] == 219
    print('ok: 4M strong_casting from-phrase corrected; marker contract intact (201/219)')


def test_meta_contract_version():
    cv = con.execute("SELECT value FROM meta WHERE key='contract_version'").fetchone()[0]
    assert cv in ('5.6', '5.7'), cv  # 5.7 added the stat-mechanics classes (Round C)
    assert cv >= '5.6', cv
    print('ok: edges.db meta contract_version', cv)


if __name__ == '__main__':
    test_artifact_shape()
    test_no_iron_will_semantics()
    test_edges_exact()
    test_artifact_edge_consistency()
    test_no_other_attribute_edges()
    test_4m_vocabulary_correction()
    test_meta_contract_version()
    print('ALL PASS')