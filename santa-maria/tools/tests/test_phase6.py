#!/usr/bin/env python3
"""Phase 6 Graph API — assert-based tests.

Run: python3 tools/tests/test_phase6.py
Covers: get_start_seed sampling + determinism, get_neighbour traversal, the four
design discovery examples, validation/rejection of the closed filter schema,
and determinism. Reads only cache/nodes.db and cache/edges.db.
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import phase6_api as api


def _pairs(res):
    return {(e['from'], e['to'], e['type']) for lv in res['levels'] for e in lv['edges']}


def _reachable(res, nid):
    return any(e['to'] == nid for lv in res['levels'] for e in lv['edges'])


def test_start_seed_filter_and_determinism():
    g = api.GraphDB()
    s1 = g.get_start_seed({'type': 'Stat', 'id_contains': 'strength', 'count': 5, 'seed': 0})
    s2 = g.get_start_seed({'type': 'Stat', 'id_contains': 'strength', 'count': 5, 'seed': 0})
    s3 = g.get_start_seed({'type': 'Stat', 'id_contains': 'strength', 'count': 5, 'seed': 1})
    assert s1 == s2, 'same seed must be reproducible'
    assert s1 != s3, 'different seed should vary the sample'
    assert len(s1['seeds']) == 5, 'count respected'
    assert all(s['type'] == 'Stat' for s in s1['seeds']), 'type filter enforced'
    assert all('strength' in s['node_id'] for s in s1['seeds']), 'id_contains enforced'
    # name filter
    n = g.get_start_seed({'name_contains': 'Whispers', 'count': 10, 'seed': 0})
    names = {s['name'] for s in n['seeds']}
    assert names, 'name_contains must find at least one node'
    assert all(name and 'whispers' in name.lower() for name in names), 'name_contains enforced'
    print('ok: start_seed sampling, filters, seed determinism')


def test_start_seed_rejection():
    g = api.GraphDB()
    for bad in [
        {'bogus': 1, 'type': 'Stat'},              # unknown filter
        {'type': 'BaseItem'},                      # invalid enum (not a node type)
        {'type': 'Stat', 'count': 99},             # count out of range
        {'type': 'Stat', 'count': 0},
        {'type': 'Stat', 'count': 1.5},
        {},                                        # empty filter set
        {'type': 'Stat', 'seed': 0.5},
    ]:
        try:
            g.get_start_seed(bad)
            raise AssertionError(f'should have rejected: {bad}')
        except ValueError:
            pass
    print('ok: start_seed closed-schema rejection')


def test_discovery_example_1_strength():
    g = api.GraphDB()
    r = g.get_neighbour(2, {'start': 'stat:strength',
                            'edge_types': ['stat_scales_with', 'modifier_grants_stat'],
                            'max_nodes_per_level': 200})
    p = _pairs(r)
    assert ('stat:strength', 'stat:attack_minimum_added_fire_damage_per_10_strength',
            'stat_scales_with') in p, 'Strength -> FireMin scaling hop'
    assert ('stat:strength', 'stat:attack_maximum_added_fire_damage_per_10_strength',
            'stat_scales_with') in p, 'Strength -> FireMax scaling hop'
    assert _reachable(r, 'mod:AddedFireDamagePerStrengthInfluence1'), \
        'per-10-strength fire mod reachable at depth 2'
    # single-hop confirmation of the modifier hop
    r1 = g.get_neighbour(1, {'start': 'stat:attack_minimum_added_fire_damage_per_10_strength',
                             'edge_types': ['modifier_grants_stat']})
    assert _reachable(r1, 'mod:AddedFireDamagePerStrengthInfluence1')
    print('ok: example 1 Strength -> Fire scaling -> modifiers')


def test_discovery_example_2_unique_rare():
    g = api.GraphDB()
    r = g.get_neighbour(2, {'start': 'unique:183', 'max_nodes_per_level': 200})
    p = _pairs(r)
    assert ('unique:183', 'mod:IncreasedAccuracyUniqueAmulet17_',
            'unique_modifier_association') in p, 'Unique -> associated Modifier'
    assert ('mod:IncreasedAccuracyUniqueAmulet17_', 'stat:accuracy_rating',
            'modifier_grants_stat') in p, 'Modifier -> shared Stat'
    # shared Stat -> rare Modifier (reverse hop)
    r1 = g.get_neighbour(1, {'start': 'stat:accuracy_rating',
                             'edge_types': ['modifier_grants_stat']})
    assert _reachable(r1, 'mod:AbyssAccuracyRatingJewel1'), 'Stat -> rare Modifier hop'
    # no direct Unique -> rare shortcut edge
    assert not any(e['type'] == 'unique_modifier_association'
                   and e['to'].startswith('mod:') and 'Abyss' in e['to']
                   for lv in r['levels'] for e in lv['edges'])
    print('ok: example 2 Unique -> Modifier -> shared Stat -> rare Modifier')


def test_discovery_example_3_whispers():
    g = api.GraphDB()
    r = g.get_neighbour(2, {'start': 'unique:1461', 'max_nodes_per_level': 200})
    p = _pairs(r)
    assert ('unique:1461', 'mod:AttacksGainMinMaxAddedChaosDamageBasedOnManaUnique__1',
            'unique_modifier_association') in p, 'Whispers chaos-per-mana mod'
    assert ('unique:1461', 'mod:PercentReducedMaximumManaUnique_1',
            'unique_modifier_association') in p, 'Whispers reduced-mana mod'
    assert ('unique:1461', 'mod:SkillsCostEnergyShieldInsteadOfManaLifeUnique__1',
            'unique_modifier_association') in p, 'Whispers skills-cost-ES mod'
    # confirmed gap: no hop to intelligence from Whispers
    assert not any(e['to'] == 'stat:intelligence' or e['from'] == 'stat:intelligence'
                   for lv in r['levels'] for e in lv['edges']), \
        'no intelligence hop from Whispers (confirmed gap must be exposed, not invented)'
    # intelligence -> lightning-per-int scaling
    r2 = g.get_neighbour(1, {'start': 'stat:intelligence',
                             'edge_types': ['stat_scales_with']})
    assert _reachable(r2, 'stat:minimum_added_lightning_damage_to_attacks_per_10_intelligence')
    print('ok: example 3 Whispers confirmed mods + intelligence gap exposed')


def test_discovery_example_4_unholy_trinity():
    g = api.GraphDB()
    r = g.get_neighbour(1, {'start': 'gem:SupportUnholyTrinity',
                            'edge_types': ['gem_has_tag']})
    to = {e['to'] for lv in r['levels'] for e in lv['edges']}
    assert {'tag:lightning', 'tag:physical', 'tag:chaos'} <= to, 'UT reaches Lightning/Physical/Chaos'
    print('ok: example 4 Unholy Trinity -> Lightning / Physical / Chaos')


def test_neighbour_filters_direction_and_rejection():
    g = api.GraphDB()
    # direction out vs in
    out = g.get_neighbour(1, {'start': 'stat:strength', 'edge_types': ['stat_scales_with'],
                              'direction': 'out'})
    inn = g.get_neighbour(1, {'start': 'stat:attack_minimum_added_fire_damage_per_10_strength',
                              'edge_types': ['stat_scales_with'], 'direction': 'in'})
    assert _reachable(out, 'stat:attack_minimum_added_fire_damage_per_10_strength')
    assert _reachable(inn, 'stat:strength')
    # edge_types restrict
    r = g.get_neighbour(1, {'start': 'gem:SupportUnholyTrinity', 'edge_types': ['gem_has_tag']})
    assert all(e['type'] == 'gem_has_tag' for lv in r['levels'] for e in lv['edges'])
    # provenance flag
    p = g.get_neighbour(1, {'start': 'stat:strength', 'edge_types': ['stat_scales_with'],
                            'include_provenance': True})
    assert any('provenance' in e for lv in p['levels'] for e in lv['edges'])
    # closed-schema rejection
    for bad in [
        {'start': 'stat:strength', 'bogus': 1},
        {'start': 'stat:strength', 'direction': 'sideways'},
        {'start': 'stat:strength', 'edge_types': ['conversion_relationship']},
        {'start': 'stat:strength', 'edge_types': []},
        {'start': 'stat:strength', 'max_nodes_per_level': 999},
        {'start': 'missing_node'},
        {'direction': 'both'},
    ]:
        try:
            g.get_neighbour(1, bad)
            raise AssertionError(f'should have rejected: {bad}')
        except ValueError:
            pass
    try:
        g.get_neighbour(0, {'start': 'stat:strength'})
        raise AssertionError('depth 0 should be rejected')
    except ValueError:
        pass
    print('ok: neighbour direction/edge_types/provenance + closed-schema rejection')


def test_neighbour_determinism():
    g = api.GraphDB()
    a = json.dumps(g.get_neighbour(2, {'start': 'stat:strength', 'max_nodes_per_level': 200}))
    b = json.dumps(g.get_neighbour(2, {'start': 'stat:strength', 'max_nodes_per_level': 200}))
    assert a == b, 'get_neighbour must be deterministic'
    print('ok: neighbour determinism')


def test_gem_static_stats_reachability():
    g = api.GraphDB()
    r = g.get_neighbour(1, {'start': 'gem:HeavyStrikeAltY',
                            'edge_types': ['gem_grants_stat']})
    assert _reachable(r, 'stat:active_skill_additive_spell_damage_modifiers_apply_to_attack_damage_at_%_value'), \
        'Heavy Strike of Trarthus must expose its 150% Arcane Might static stat'
    assert _reachable(r, 'stat:chance_to_deal_double_damage_%_per_10_intelligence'), \
        'Heavy Strike of Trarthus must expose its per-10-Intelligence double damage static stat'
    print('ok: gem static.stats reachable via gem_grants_stat')


if __name__ == '__main__':
    test_start_seed_filter_and_determinism()
    test_start_seed_rejection()
    test_discovery_example_1_strength()
    test_discovery_example_2_unique_rare()
    test_discovery_example_3_whispers()
    test_discovery_example_4_unholy_trinity()
    test_neighbour_filters_direction_and_rejection()
    test_neighbour_determinism()
    test_gem_static_stats_reachability()
    print('ALL TESTS PASSED')
