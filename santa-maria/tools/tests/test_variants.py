#!/usr/bin/env python3
"""Phase 6 Graph API — first-class Foulborn/Vestigial variant tests.

Run: python3 tools/tests/test_variants.py
Covers: variant seed discovery, variant->modifier->stat traversal with
membership provenance, ambiguous-name policy (attached to ALL matching
records, never upgraded), source-derived VID matches, mutual exclusivity,
ordinary-Unique regression, and the mixed seed universe.
Reads only cache/nodes.db, cache/edges.db and data/pob/Vestigial.json.
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import phase6_api as api


def _d1(res, etype):
    return [e for e in res['levels'][0]['edges'] if e['type'] == etype]


def test_population_counts():
    g = api.GraphDB()
    v = g._load_variants()
    vs = v['variants']
    types = Counter(x['variant_type'] for x in vs.values())
    assert types == Counter({'Vestigial': 447, 'Foulborn': 252}), types
    mem = Counter(m['membership'] for x in vs.values() for m in x['modifiers'])
    assert mem['confirmed_edge'] == 768, mem            # 329 F + 439 V, exact KB parity
    assert mem['source_derived_vid_match'] == 15, mem   # rule-verbatim fresh VID matches
    assert mem['ambiguous_name_shared_by_2_records'] == 44, mem
    assert mem['ambiguous_name_shared_by_3_records'] == 36, mem
    assert len(v['unresolved']['foulborn_mods']) == 39, len(v['unresolved']['foulborn_mods'])
    assert len(v['unresolved']['vestigial_mods']) == 6, len(v['unresolved']['vestigial_mods'])
    # every KB confirmed (unique, mutated mod) pair must be attached
    import sqlite3
    e = sqlite3.connect(api.EDGES_DB)
    kb = {(r[0], r[1]) for r in e.execute(
        "SELECT source_node_id,target_node_id FROM edges "
        "WHERE relationship_type='unique_modifier_association' "
        "AND target_node_id LIKE 'mod:MutatedUnique%'")}
    api_pairs = {(x['base_unique_id'], m['modifier_id'])
                 for x in vs.values() if x['variant_type'] == 'Foulborn'
                 for m in x['modifiers'] if m['membership'] == 'confirmed_edge'}
    assert api_pairs == kb, 'confirmed Foulborn membership must equal KB edges exactly'
    e.close()
    print('ok: variant population counts (699 variants; provenance classes pinned)')


def test_seed_discovery():
    g = api.GraphDB()
    r = g.get_start_seed({'type': 'Variant', 'count': 20, 'seed': 0})
    assert r['seeds'], 'type=Variant must return seeds'
    assert all(s['type'] == 'Variant' for s in r['seeds'])
    assert all(s['variant_type'] in api.VARIANT_TYPES for s in r['seeds'])
    assert all(s['node_id'].startswith('variant:') for s in r['seeds'])
    # by name, both types
    for prefix, vtype in (('Foulborn ', 'Foulborn'), ('Vestigial ', 'Vestigial')):
        found = 0
        for seed_val in range(6):
            s = g.get_start_seed({'name_contains': prefix, 'count': 20, 'seed': seed_val})
            hits = [x for x in s['seeds']
                    if x['type'] == 'Variant' and x['variant_type'] == vtype]
            assert all(x['name'].startswith(prefix) for x in hits)
            found += len(hits)
        assert found >= 10, f'{vtype}: >=10 discoverable by name, got {found}'
    # variant and base unique co-exist in one name search; not merged
    r = g.get_start_seed({'name_contains': 'Doon Cuebiyari', 'count': 20, 'seed': 0})
    ids = {s['node_id'] for s in r['seeds']}
    assert 'unique:206' in ids and 'variant:foulborn:206' in ids, ids
    r = g.get_start_seed({'type': 'UniqueItem', 'name_contains': 'Doon Cuebiyari',
                          'count': 20, 'seed': 0})
    assert {s['node_id'] for s in r['seeds']} == {'unique:206'}, \
        'UniqueItem filter must NOT return variants'
    print('ok: variant seed discovery (type filter, name search, separation from UniqueItem)')


def test_traversal_and_provenance():
    g = api.GraphDB()
    # Foulborn Doon Cuebiyari: 2 mutated mods -> per-STR stats
    nb = g.get_neighbour(2, {'start': 'variant:foulborn:206', 'include_provenance': True})
    d1 = _d1(nb, api.VARIANT_EDGE)
    mods = {e['to']: e['provenance'] for e in d1}
    assert mods, 'variant must expose its modifiers at depth 1'
    assert 'mod:MutatedUniqueSceptre6EnergyShieldPerStrengthIfInOffHand' in mods
    # variant payload exposes source-backed modifier text
    v = g._load_variants()['variants']['variant:foulborn:206']
    mtexts = {m['modifier_id']: m['text'] for m in v['modifiers']}
    assert all(mtexts.values()), mtexts
    assert 'per 25 Strength' in mtexts['mod:MutatedUniqueSceptre6EnergyShieldPerStrengthIfInOffHand']
    for mprov in mods.values():
        assert mprov['membership'] in ('confirmed_edge', 'source_derived_vid_match'), mprov
        assert mprov['source_file'] == 'pob/ModFoulborn.json'
    d2 = {e['to'] for e in nb['levels'][1]['edges'] if e['type'] == 'modifier_grants_stat'}
    assert 'stat:energy_shield_+1%_per_X_strength_when_in_off_hand_from_foulborn_doon_cuebiyari' in d2
    # ambiguous Vestigial case: Bubonic Trail name -> 2 records, both variants
    # expose the same modifier with ambiguity preserved (never confirmed)
    for rk in ('723', '724'):
        nb = g.get_neighbour(2, {'start': f'variant:vestigial:{rk}',
                                 'include_provenance': True})
        d1 = _d1(nb, api.VARIANT_EDGE)
        targets = {e['to']: e['provenance'].get('membership') for e in d1}
        assert 'mod:DivergentAbyssJewelSocketUnique__12' in targets, (rk, targets)
        m = targets['mod:DivergentAbyssJewelSocketUnique__12']
        assert m == 'ambiguous_name_shared_by_2_records', (rk, m)
    # stat continuation from an ambiguous modifier works identically
    nb = g.get_neighbour(2, {'start': 'variant:vestigial:723'})
    d2 = {e['to'] for e in nb['levels'][1]['edges'] if e['type'] == 'modifier_grants_stat'}
    assert 'stat:local_has_X_abyss_sockets' in d2, d2
    print('ok: variant->modifier->stat traversal; ambiguity preserved as '
          'ambiguous_name_shared_by_2_records on both Bubonic Trail records')


def test_no_membership_upgrades_and_mutual_exclusivity():
    g = api.GraphDB()
    v = g._load_variants()
    vs = v['variants']
    legal = set(api.VARIANT_MEMBERSHIP_CLASSES)
    for x in vs.values():
        assert x['variant_type'] in api.VARIANT_TYPES
        for m in x['modifiers']:
            assert api._membership_class(m['membership']) in legal, m
            # no weaker class may masquerade as confirmed_edge: confirmed only
            # when the API found a real KB edge for that exact (base, mod) pair
    # per (variant, modifier) membership must be identical to index truth
    for vid, x in vs.items():
        for m in x['modifiers']:
            rev = v['reverse'][m['modifier_id']]
            entry = [r for r in rev if r[0] == vid]
            assert entry and entry[0][1] == m['membership'], (vid, m)
    # same base, both types -> two distinct variants, disjoint modifier sets
    fmods = {m['modifier_id'] for m in vs['variant:foulborn:136']['modifiers']}
    vmods = {m['modifier_id'] for m in vs['variant:vestigial:136']['modifiers']}
    assert fmods and vmods and not (fmods & vmods), 'variant modifier sets must be disjoint'
    assert vs['variant:foulborn:136']['variant_type'] == 'Foulborn'
    assert vs['variant:vestigial:136']['variant_type'] == 'Vestigial'
    print('ok: no provenance upgrades; mutual exclusivity (Foulborn/Vestigial '
          'of unique:136 are distinct with disjoint modifiers)')


def test_ordinary_unique_regression():
    g = api.GraphDB()
    # seed results unchanged for ordinary uniques
    for name, expected in (("Oro's Sacrifice", 'unique:185'),
                           ('Grand Spectrum', 'unique:1358'),
                           ('Melding of the Flesh', 'unique:1325'),
                           ('Headhunter', 'unique:986'),
                           ('Terminus Est', 'unique:65')):
        r = g.get_start_seed({'name_contains': name, 'count': 20, 'seed': 0})
        assert expected in {s['node_id'] for s in r['seeds']}, name
        assert all(s['type'] != 'Variant' or s['node_id'].startswith('variant:')
                   for s in r['seeds'])
    # ordinary traversal: no virtual edges leak into non-variant starts
    for start in ('unique:206', 'mod:MutatedUniqueSceptre6EnergyShieldPerStrengthIfInOffHand',
                  'stat:strength', 'mod:LocalIncreasedPhysicalDamagePercentUnique__54'):
        nb = g.get_neighbour(1, {'start': start})
        assert not _d1(nb, api.VARIANT_EDGE), start
    # mod -> stat edges intact for an ordinary unique mod
    nb = g.get_neighbour(1, {'start': 'unique:185',
                             'edge_types': ['unique_modifier_association']})
    assert any(e['to'] == 'mod:FrenzyChargeOnIgniteUniqueTwoHandSword6'
               for e in nb['levels'][0]['edges'])
    print('ok: ordinary Unique search/traversal regression (5 controls, no '
          'virtual-edge leakage)')


def test_filter_validation_unchanged():
    g = api.GraphDB()
    for bad in ({'type': 'Nonsense'}, {'type': ''},
                {'type': 'Stat', 'count': 0}, {'type': 'Stat', 'count': 21},
                {'type': 'Stat', 'seed': 'x'}, {'bogus': 1},
                {'type': 'Stat', 'id_contains': 5}):
        try:
            g.get_start_seed(bad)
            raise AssertionError(f'expected rejection: {bad}')
        except ValueError:
            pass
    for bad in ({'start': 'variant:does-not-exist'}, {'start': 'variant:foulborn:999999'},
                {'start': 'unique:206', 'edge_types': ['not_a_type']}):
        try:
            g.get_neighbour(1, bad)
            raise AssertionError(f'expected rejection: {bad}')
        except ValueError:
            pass
    print('ok: closed filter schema still rejects invalid input (incl. unknown variants)')


if __name__ == '__main__':
    test_population_counts()
    test_seed_discovery()
    test_traversal_and_provenance()
    test_no_membership_upgrades_and_mutual_exclusivity()
    test_ordinary_unique_regression()
    test_filter_validation_unchanged()
    print('ALL VARIANT TESTS PASSED')
