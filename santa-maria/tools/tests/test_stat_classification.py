#!/usr/bin/env python3
"""Stat classification — assert-based tests.

Run: python3 tools/tests/test_stat_classification.py
Proves: keystone_quiet_might is item_only_internal_keystone with its user-facing
mechanic name; the 10 confirmed item-only internal keystones classify correctly;
shared/tree-only/unused keystones keep their classes; ordinary gem/item-only
stats classify as item_only_stat (NOT as internal keystones); graph edges,
traversal and carrier grouping are unchanged; classification is deterministic
and requires no hardcoded ID list in the classifier itself.
"""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import phase6_api as api
import phase7_stat_classification as sc

SANTA = Path(__file__).resolve().parents[2]

# Test fixture from docs/experiments/phase7_item_internal_keystones/README.md section 3.
# Used ONLY here to verify the classifier; the classifier itself derives
# everything from graph edges.
ITEM_ONLY_TEN = sorted([
    'keystone_quiet_might', 'keystone_corrupted_defences', 'keystone_divine_flesh',
    'keystone_soul_tether', 'keystone_prismatic_bulwark', 'keystone_emperors_heart',
    'keystone_herald_of_doom', 'keystone_hollow_palm_technique',
    'keystone_shared_suffering', 'keystone_secrets_of_suffering',
])


def test_quiet_might():
    g = api.GraphDB()
    r = sc.classify_stat('stat:keystone_quiet_might', g)
    assert r['classification'] == sc.ITEM_ONLY_INTERNAL_KEYSTONE, r
    assert r['mechanic'] == 'Inner Conviction', r
    assert r['evidence']['item_carriers'] == 2
    assert r['evidence']['passive_granters'] == []
    assert not r['evidence']['name_match']
    print('ok: keystone_quiet_might -> item_only_internal_keystone (Inner Conviction)')


def test_all_ten_item_only_internal_keystones():
    g = api.GraphDB()
    for sid in ITEM_ONLY_TEN:
        r = sc.classify_stat(sid, g)
        assert r['classification'] == sc.ITEM_ONLY_INTERNAL_KEYSTONE, (sid, r)
        assert r['mechanic'], (sid, 'mechanic name must be resolved')
    print('ok: all 10 confirmed item-only internal keystones classified correctly')


def test_shared_tree_item_keystones():
    g = api.GraphDB()
    for sid in ['keystone_eternal_youth', 'keystone_eldritch_battery',
                'keystone_blood_magic', 'keystone_ghost_reaver']:
        r = sc.classify_stat(sid, g)
        assert r['classification'] == sc.SHARED_TREE_ITEM, (sid, r)
        assert r['evidence']['passive_granters'], sid
    print('ok: shared tree+item keystones not internal')


def test_tree_only_keystones():
    g = api.GraphDB()
    for sid in ['keystone_chaos_inoculation',
                'keystone_sacrifice_of_blood_if_at_least_8_corrupted_items_equipped']:
        r = sc.classify_stat(sid, g)
        assert r['classification'] == sc.TREE_ONLY, (sid, r)
    print('ok: tree-only keystones not internal')


def test_unused_keystones():
    g = api.GraphDB()
    for sid in ['keystone_tempered_by_war', 'keystone_vampirism', 'keystone_zealots_oath']:
        r = sc.classify_stat(sid, g)
        assert r['classification'] == sc.UNUSED, (sid, r)
    print('ok: unused keystone vocabulary not classified item-only')


def test_generic_item_only_stat():
    g = api.GraphDB()
    for sid in ['skill_physical_damage_%_to_convert_to_lightning',
                'holy_hammers_num_additional_hammerslams_if_consuming_power_charge']:
        r = sc.classify_stat(sid, g)
        assert r['classification'] == sc.ITEM_ONLY_STAT, (sid, r)
        assert r['classification'] != sc.ITEM_ONLY_INTERNAL_KEYSTONE, sid
    print('ok: ordinary gem/item-only stats -> item_only_stat, not internal keystone')


def test_generic_shared_stat():
    g = api.GraphDB()
    for sid in ['attack_speed_+%', 'base_maximum_mana']:
        r = sc.classify_stat(sid, g)
        assert r['classification'] == sc.SHARED_TREE_ITEM, (sid, r)
    print('ok: generic stats with tree implementation remain shared_tree_item')


def test_keystone_partition():
    g = api.GraphDB()
    allk = sc.classify_all_keystones(g)
    assert len(allk) == 99, f'expected 99 keystone stats, got {len(allk)}'
    item_only = sorted(s for s, r in allk.items()
                       if r['classification'] == sc.ITEM_ONLY_INTERNAL_KEYSTONE)
    assert item_only == ITEM_ONLY_TEN, item_only
    for cls in (sc.ITEM_ONLY_INTERNAL_KEYSTONE, sc.SHARED_TREE_ITEM, sc.TREE_ONLY, sc.UNUSED):
        assert any(r['classification'] == cls for r in allk.values()), cls
    for sid, r in allk.items():
        assert set(r) == {'node_id', 'stat_id', 'classification', 'mechanic', 'evidence'}
        assert not sc.name_match_conflicts(r), sid
    print('ok: all 99 keystone stats partitioned, 10 item-only internal, no name-match conflicts')


def test_global_partition():
    g = api.GraphDB()
    nodes = g._load_nodes()
    counts = {}
    for nid in nodes:
        if not nid.startswith('stat:'):
            continue
        cls = sc.classify_stat(nid, g)['classification']
        counts[cls] = counts.get(cls, 0) + 1
    # frozen-KB pin (data snapshot c7175e76...); derived, not hardcoded in the classifier
    assert counts == {sc.ITEM_ONLY_INTERNAL_KEYSTONE: 10, sc.ITEM_ONLY_STAT: 11317,
                      sc.SHARED_TREE_ITEM: 1318, sc.TREE_ONLY: 761, sc.UNUSED: 9938}, counts
    print('ok: global partition 10 / 11317 / 1318 / 761 / 9938 over all 23344 stats')


def test_no_hardcoded_ids_in_classifier():
    src = (Path(__file__).resolve().parents[1] / 'phase7_stat_classification.py').read_text()
    for sid in ITEM_ONLY_TEN:
        assert sid not in src, f'classifier must not hardcode {sid}'
    assert '11317' not in src and '1318' not in src and '9938' not in src, \
        'classifier must not hardcode class counts'
    print('ok: classifier contains no hardcoded keystone IDs or counts')


def test_edges_unchanged():
    ncon = sqlite3.connect(f"file:{SANTA / 'cache' / 'edges.db'}?mode=ro", uri=True)
    nid = 'stat:keystone_quiet_might'
    ins = {(s, t, rt) for s, t, rt in ncon.execute(
        "SELECT source_node_id, target_node_id, relationship_type FROM edges "
        "WHERE target_node_id=?", (nid,))}
    outs = {(s, t, rt) for s, t, rt in ncon.execute(
        "SELECT source_node_id, target_node_id, relationship_type FROM edges "
        "WHERE source_node_id=?", (nid,))}
    assert ins == {('mod:KeystoneInnerConvictionUnique__1', nid, 'modifier_grants_stat'),
                   ('mod:DivergentKeystoneInnerConvictionUnique__1', nid,
                    'modifier_grants_stat')}, ins
    assert outs == {(nid, 'tag:frenzy_charge', 'sem_relation_binds'),
                    (nid, 'tag:power_charge', 'sem_relation_binds')}, outs
    print('ok: keystone_quiet_might edges unchanged (2 mod grants in, 2 sem binds out)')


def test_traversal_unchanged():
    g = api.GraphDB()
    r = g.get_neighbour(2, {'start': 'stat:keystone_quiet_might',
                            'max_nodes_per_level': 200})
    reached = {e['to'] for lv in r['levels'] for e in lv['edges']}
    assert 'tag:frenzy_charge' in reached and 'tag:power_charge' in reached, reached
    lvl1 = list(r['levels'][0]['edges'])
    assert sum(1 for e in lvl1 if e['type'] == 'modifier_grants_stat'
               and e['direction'] == 'in') == 2
    assert sum(1 for e in lvl1 if e['type'] == 'sem_relation_binds') == 2
    print('ok: BFS from keystone_quiet_might traverses normally, semantic edges intact')


def test_carrier_grouping_unchanged():
    g = api.GraphDB()
    r = g.get_neighbour(1, {'start': 'stat:keystone_quiet_might',
                            'carrier_grouping': True})
    mods = [grp for grp in r['levels'][0]['carrier_groups']
            if grp['carrier_type'] == 'Modifier']
    assert len(mods) == 1 and mods[0]['count'] == 2, mods
    sem = [e for e in r['levels'][0]['edges'] if e['type'] == 'sem_relation_binds']
    assert len(sem) == 2, sem
    print('ok: carrier grouping behavior unchanged (Modifier group of 2 + 2 sem edges)')


def test_deterministic():
    a = sc.classify_all_keystones(api.GraphDB())
    b = sc.classify_all_keystones(api.GraphDB())
    assert a == b, 'classification must be deterministic'
    print('ok: deterministic across independent graph instances')


if __name__ == '__main__':
    test_quiet_might()
    test_all_ten_item_only_internal_keystones()
    test_shared_tree_item_keystones()
    test_tree_only_keystones()
    test_unused_keystones()
    test_generic_item_only_stat()
    test_generic_shared_stat()
    test_keystone_partition()
    test_global_partition()
    test_no_hardcoded_ids_in_classifier()
    test_edges_unchanged()
    test_traversal_unchanged()
    test_carrier_grouping_unchanged()
    test_deterministic()
    print('ALL TESTS PASSED')
