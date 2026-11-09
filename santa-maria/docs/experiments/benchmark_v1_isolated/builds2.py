#!/usr/bin/env python3
"""Stage D loose ends — final bounded probes."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe  # noqa: E402


def b09():
    s = 9
    probe.carriers(s, 'stat:damage_vs_shocked_enemies_+%')
    probe.carriers(s, 'stat:critical_strike_chance_+%_vs_shocked_enemies')


def b67():
    s = 67
    probe.carriers(s, 'stat:cold_damage_+%_per_25_intelligence')
    probe.carriers(s, 'stat:area_damage_+%_per_12_strength')


def b43():
    s = 43
    rows = probe.carriers(s, 'stat:attacks_impale_on_hit_%_chance', show=0)
    uniqs = [r['carrier'] for r in rows
             if r['edge_type'] == 'modifier_grants_stat' and 'Unique' in r['carrier']]
    print(f'    unique-named impale mods: {len(uniqs)}: {uniqs[:8]}')
    for m in uniqs[:4]:
        probe.carriers(s, m, edge_types=['unique_modifier_association'], show=3)


def b66():
    s = 66
    probe.validate(s, {'passives': ['passive:AscendancyRaider5'],
                       'gem_groups': [{'skill': 'gem:DefianceBanner'}]})


if __name__ == '__main__':
    before = probe.A.n
    for fn in (b09, b67, b43, b66):
        fn()
    print(f'[total calls: {probe.A.n - before}]')
