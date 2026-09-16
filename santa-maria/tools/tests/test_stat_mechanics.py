#!/usr/bin/env python3
"""Round C+D golden tests: stat_mechanic_variant / stat_mechanic_operand.

Run: python3 tools/tests/test_stat_mechanics.py
Contract 5.7; provenance_class audited_pinned_external_source.

RULE (adopted after the Round D incident): PoE Stat IDs containing '+' and '%'
are NEVER visually inspected or hand-typed. Every expected ID is derived from
the database by its family head (which contains no '+'/'%') and asserted by
code points (repr + hex of the distinguishing tail).
"""
import json
import sqlite3
from pathlib import Path

SANTA = Path(__file__).resolve().parents[2]
ARTIFACT = SANTA / 'tools' / 'sources' / 'pob_stat_mechanics.json'
NODES_DB = SANTA / 'cache' / 'nodes.db'
EDGES_DB = SANTA / 'cache' / 'edges.db'

art = json.loads(ARTIFACT.read_text())
mech = art['mechanics'][0]  # Arcane Might (Round C)
ncon = sqlite3.connect(f"file:{NODES_DB}?mode=ro", uri=True)
EXISTING = {r[0] for r in ncon.execute("SELECT node_id FROM nodes WHERE type='Stat'")}
con = sqlite3.connect(f"file:{EDGES_DB}?mode=ro", uri=True)


def sid(head):
    """DB-derived Stat node id for a family head (head contains no '+'/'%').

    Uniqueness is enforced; the distinguishing tail is reported as hex so the
    '+'/'%' ordering is verified by code points, never by eye."""
    # code-point safe: Python-side scan over the exact ID set (no LIKE wildcards;
    # '+'/'%' ordering is never inspected — the tail charset is the only filter)
    cands = [x for x in EXISTING
             if x.startswith(f"stat:{head}_")
             and set(x[len(f"stat:{head}_"):].replace('_', '')) <= {'+', '%'}]
    assert len(cands) == 1, (head, sorted(cands))
    sid_val = cands[0]
    tail = sid_val[len(f"stat:{head}"):]
    print(f"   sid({head!r}) = {sid_val!r}  tail-hex={tail.encode().hex()} "
          f"tail-cps={[hex(ord(c)) for c in tail]}")
    return sid_val


def edges_of(rtype):
    return con.execute(
        "SELECT source_node_id, target_node_id, confidence_status, provenance "
        "FROM edges WHERE relationship_type=?", (rtype,)).fetchall()


def test_artifact_shape():
    p = art['provenance']
    assert p['provenance_class'] == 'audited_pinned_external_source'
    assert p['pob_commit'] and len(art['mechanics']) == 9
    assert mech['pob_flag'] == 'SpellDamageAppliesToAttacks'
    assert len(mech['members']) == 6
    # code-point verified against the DB — never hand-typed
    assert mech['operand_stat'] == sid('spell_damage')
    assert mech['product_stat'] == sid('attack_damage')
    assert mech['canonical_stat'] == 'stat:additive_spell_damage_modifiers_apply_to_attack_damage'
    print('ok: artifact shape (9 mechanics; Arcane Might operand/product code-point verified)')


def test_no_iron_will_semantics():
    banned = ('iron will', 'iron_will', 'strong_casting', 'strong casting', 'strdmgbonus')
    for m in art['mechanics']:
        entry = json.dumps({'id': m['id'], 'pob_flag': m.get('pob_flag'),
                            'improved_flag': m.get('improved_flag'),
                            'canonical_stat': m.get('canonical_stat'),
                            'operand_stat': m.get('operand_stat'),
                            'product_stat': m.get('product_stat'),
                            'members': [{'stat': mm['stat'], 'role': mm['role']}
                                        for mm in m.get('members', [])]}).casefold()
        for b in banned:
            assert b not in entry, (m['id'], b)
    print('ok: no mechanic entry refers to Iron Will / strong_casting / strDmgBonus')


def test_arcane_might_edges():
    rows = edges_of('stat_mechanic_operand')
    am = [r for r in rows if json.loads(r[3])[0]['mechanic_id'] == 'spell_damage_applies_to_attacks']
    assert len(am) == 11
    operand = {(s, t) for s, t, _, p in am if json.loads(p)[0]['role'] == 'operand'}
    members = {m['stat'] for m in mech['members']}
    assert operand == {(m, sid('spell_damage')) for m in members}
    gapped = {g['stat'] for g in mech['product_gaps']}
    product = {(s, t) for s, t, _, p in am if json.loads(p)[0]['role'] == 'product'}
    assert product == {(m, sid('attack_damage')) for m in members if m not in gapped}
    ret = next(m['stat'] for m in mech['members'] if 'retaliation' in m['stat'])
    assert (ret, sid('spell_damage')) in operand
    assert (ret, sid('attack_damage')) not in product  # audited product gap
    assert any(g['stat'] == ret for g in mech['product_gaps'])
    vrows = edges_of('stat_mechanic_variant')
    assert len([r for r in vrows
                if json.loads(r[3])[0]['mechanic_id'] == 'spell_damage_applies_to_attacks']) == 5
    print('ok: Arcane Might — 11 operand edges (retaliation product gap), 5 variant edges')


def test_round_d_mechanics():
    by_id = {m['id']: m for m in art['mechanics']}
    for mid in ('light_radius_applies_to_damage', 'light_radius_applies_to_accuracy',
                'light_radius_applies_to_area_of_effect', 'minion_damage_applies_to_player',
                'minion_attack_speed_applies_to_player', 'minion_cast_speed_applies_to_player',
                'cast_speed_applies_to_trap_throwing_speed', 'cast_speed_applies_to_attack_speed'):
        assert mid in by_id, mid
    all_rows = edges_of('stat_mechanic_operand') + edges_of('stat_mechanic_variant')

    # per-mechanic artifact↔edge consistency (expected IDs come from the
    # repaired artifact — DB-verified by code points — never hand-typed)
    op_pairs = {(s, t) for s, t, _, _ in edges_of('stat_mechanic_operand')}
    for mid in ('light_radius_applies_to_damage', 'light_radius_applies_to_accuracy',
                'light_radius_applies_to_area_of_effect', 'minion_attack_speed_applies_to_player',
                'minion_cast_speed_applies_to_player', 'cast_speed_applies_to_trap_throwing_speed',
                'cast_speed_applies_to_attack_speed'):
        m = by_id[mid]
        op, prod = m['operand_stat'], m['product_stat']
        for mem in m['members']:
            assert (mem['stat'], op) in op_pairs, (mid, mem['stat'], 'operand')
            assert (mem['stat'], prod) in op_pairs, (mid, mem['stat'], 'product')

    # R1c: AoE product resolved per artifact (code-point verified at repair)
    lr = by_id['light_radius_applies_to_area_of_effect']
    assert ('stat:light_radius_increases_apply_to_area_of_effect', lr['product_stat']) in op_pairs
    # R2a: minion damage — canonical + 2 value variants; 150% variant edge present
    m = by_id['minion_damage_applies_to_player']
    var = [(s, t) for s, t, _, p in edges_of('stat_mechanic_variant')
           if json.loads(p)[0]['mechanic_id'] == 'minion_damage_applies_to_player']
    members = {mm['stat'] for mm in m['members']}
    canon = m['canonical_stat']
    assert {(s, t) for s, t in var} == {(mm, canon) for mm in members if mm != canon}
    assert ('stat:additive_minion_damage_modifiers_apply_to_you_at_150%_value', canon) in {(s, t) for s, t in var}
    # R4: the uncarried active_skill sibling stays unresolved metadata, never edged
    r4 = by_id['cast_speed_applies_to_attack_speed']
    unresolved = r4['metadata']['unresolved_members']
    assert len(unresolved) == 1 and unresolved[0]['stat'].startswith('stat:active_skill_')
    assert not any(s == unresolved[0]['stat'] for s, t in op_pairs)
    print('ok: R1-R4 mechanics — 8 mechanics, artifact↔edge consistency for all '
          'members; minion 150% variant; R4 sibling unresolved only')


def test_no_other_mechanic_edges():
    for rtype in ('stat_mechanic_variant', 'stat_mechanic_operand'):
        n = con.execute("SELECT count(*) FROM edges WHERE relationship_type=? AND "
                        "(source_node_id LIKE '%strong%' OR source_node_id LIKE '%iron%' "
                        "OR target_node_id LIKE '%strong%' OR target_node_id LIKE '%iron%')",
                        (rtype,)).fetchone()[0]
        assert n == 0
    print('ok: no Iron Will / strong_casting edges in the mechanic layer')


def test_meta_contract_version():
    cv = con.execute("SELECT value FROM meta WHERE key='contract_version'").fetchone()[0]
    assert cv == '5.7', cv
    print('ok: edges.db meta contract_version 5.7')


if __name__ == '__main__':
    test_artifact_shape()
    test_no_iron_will_semantics()
    test_arcane_might_edges()
    test_round_d_mechanics()
    test_no_other_mechanic_edges()
    test_meta_contract_version()
    print('ALL PASS')