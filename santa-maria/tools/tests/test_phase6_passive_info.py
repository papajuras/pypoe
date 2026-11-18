"""passive_info exposure tests (get_start_seed + get_neighbour).

Run: cd santa-maria && uv run python -m tools.tests.test_phase6_passive_info
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.phase6_api import get_start_seed, get_neighbour


def test_seed_entry_carries_passive_info():
    r = get_start_seed({'id_contains': 'AscendancyNecromancer9', 'count': 1})
    e = r['seeds'][0]
    assert e['name'] == 'Bone Barrier'
    pi = e['passive_info']
    assert pi['ascendancy'] == 'Necromancer'
    assert pi['kind_flags']['is_notable'] is True
    assert pi['kind_flags']['is_keystone'] is False


def test_seed_classless_keystone():
    r = get_start_seed({'type': 'Passive', 'id_contains': 'vaal_pact',
                        'count': 1})
    pi = r['seeds'][0]['passive_info']
    assert pi['ascendancy'] is None            # legal classless, not guessed
    assert pi['kind_flags']['is_keystone'] is True


def test_neighbour_levels_carry_passive_nodes():
    n = get_neighbour(1, {'start': 'stat:minion_maximum_life_%_to_add_as_'
                                   'maximum_energy_shield',
                          'edge_types': ['passive_grants_stat'],
                          'max_nodes_per_level': 20})
    pn = n['levels'][0]['passive_nodes']
    by_id = {p['id']: p for p in pn}
    assert by_id['passive:AscendancyNecromancer9']['passive_info'][
        'ascendancy'] == 'Necromancer'
    # alternate (Phrecia) ascendancy passives are excluded by default
    assert not any(p['id'].startswith(('passive:AscendancyCustom',
                                       'passive:AlternateAscendancy'))
                   for p in pn)
    # non-Passive endpoints never appear in the block
    assert not any(not p['id'].startswith('passive:') for p in pn)


def test_neighbour_alternate_ascendancy_opt_in():
    n = get_neighbour(1, {'start': 'stat:minion_maximum_life_%_to_add_as_'
                                   'maximum_energy_shield',
                          'edge_types': ['passive_grants_stat'],
                          'max_nodes_per_level': 20,
                          'include_alternate_ascendancies': True})
    pn = n['levels'][0]['passive_nodes']
    by_id = {p['id']: p for p in pn}
    assert by_id['passive:AscendancyCustomHeirophant18']['name'] == 'Marination'


def test_seed_excludes_alternate_ascendancies_by_default():
    r = get_start_seed({'type': 'Passive', 'id_contains': 'AlternateAscendancy',
                        'count': 10, 'seed': 1})
    assert r['seeds'] == []
    r = get_start_seed({'type': 'Passive', 'id_contains': 'AlternateAscendancy',
                        'count': 10, 'seed': 1,
                        'include_alternate_ascendancies': True})
    assert len(r['seeds']) == 10
    assert all(s['node_id'].startswith('passive:AlternateAscendancy')
               for s in r['seeds'])


def test_no_passives_no_block():
    n = get_neighbour(1, {'start': 'stat:strength',
                          'edge_types': ['stat_scales_with'],
                          'max_nodes_per_level': 10})
    assert 'passive_nodes' not in n['levels'][0]


def test_deterministic():
    f = {'start': 'stat:minion_maximum_life_%_to_add_as_maximum_energy_shield',
         'edge_types': ['passive_grants_stat'], 'max_nodes_per_level': 20}
    a = get_neighbour(1, f)
    b = get_neighbour(1, f)
    assert a['levels'][0]['passive_nodes'] == b['levels'][0]['passive_nodes']


if __name__ == '__main__':
    fns = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for fn in fns:
        fn()
        print(f'{fn.__name__}: OK')
    print(f'{len(fns)} tests passed')
