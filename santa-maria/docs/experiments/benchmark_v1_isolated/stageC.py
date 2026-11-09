#!/usr/bin/env python3
"""Stage C — bounded deep probes on promoted seeds. See probe.py for ops.

Promoted (full, <=12 calls): 09 12 14 16 21 32 33 35 43 47 66 67
Checked (lite, <=5 calls): 01 19 25 29 30 64
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe  # noqa: E402

MECH = ('stat_mechanic_relation', 'stat_mechanic_operand',
        'stat_mechanic_variant')


def p09():
    s = 9
    probe.carriers(s, 'stat:always_shock')
    probe.carriers(s, 'stat:all_damage_can_shock')
    rows = probe.resolve(s, 'shock', type='Mechanic')
    mech = next((r['id'] for r in rows if r['id'].startswith('mechanic:')), None)
    if mech:
        probe.neighbour(s, mech, edge_types=list(MECH))
    rows = probe.resolve(s, 'shocked', type='Stat')
    cons = [r['id'] for r in rows if 'shocked' in r['id']]
    for st in cons[:2]:
        probe.carriers(s, st)
    probe.resolve(s, 'Fidelitas', type='Passive')
    probe.validate(s, {'passives': ['Shaper of Storms']})


def p12():
    s = 12
    probe.carriers(s, 'stat:number_of_additional_totems_allowed')
    probe.carriers(s, 'stat:summon_totem_cast_speed_+%')
    rows = probe.resolve(s, 'AdditionalTotemsUnique', type='Modifier')
    for m in rows[:1]:
        probe.carriers(s, m['id'], edge_types=['unique_modifier_association'])
    probe.resolve(s, 'AscendancyHeirophant', type='Passive')
    probe.resolve(s, 'SearingBond', type='Gem')
    probe.validate(s, {'passives': ['Pursuit of Faith'],
                       'gem_groups': [{'skill': 'gem:SearingBond'}]})


def p14():
    s = 14
    rows = probe.resolve(s, 'per_endurance_charge', type='Stat')
    dmg = next((r['id'] for r in rows if 'damage' in r['id']), None)
    if dmg:
        probe.carriers(s, dmg)
    probe.carriers(s, 'stat:max_endurance_charges')
    probe.resolve(s, 'maximum_endurance_charges', type='Passive')
    probe.validate(s, {'passives': ['Unflinching']})


def p16():
    s = 16
    probe.carriers(s, 'stat:number_of_additional_curses_allowed')
    probe.carriers(s, 'stat:ignore_hexproof')
    probe.resolve(s, 'Whispers of Doom', type='Passive')
    probe.validate(s, {'passives': ['Unholy Authority']})


def p21():
    s = 21
    probe.carriers(s, 'stat:max_frenzy_charges')
    probe.resolve(s, 'Frenzy', type='Gem')
    probe.resolve(s, 'FlickerStrike', type='Gem')
    probe.resolve(s, 'BloodRage', type='Gem')
    probe.validate(s, {'passives': ['Swift Killer'],
                       'gem_groups': [{'skill': 'gem:Frenzy'}]})


def p32():
    s = 32
    probe.resolve(s, 'frenzy_charges', type='Passive')
    probe.validate(s, {'items': ['Badge of the Brotherhood']})


def p33():
    s = 33
    probe.resolve(s, 'AncestralWarchief', type='Gem')
    probe.resolve(s, 'Critical Strike Multiplier and Stealth', type='Passive')
    probe.validate(s, {'items': ['Facebreaker'],
                       'gem_groups': [{'skill': 'gem:AncestralWarchief'}]})


def p35():
    s = 35
    probe.carriers(s, 'stat:damage_+%_per_endurance_charge')
    probe.resolve(s, 'Unyielding', type='Passive')
    probe.validate(s, {'passives': ['Disciple of the Unyielding']})


def p43():
    s = 43
    probe.carriers(s, 'stat:attacks_impale_on_hit_%_chance')
    probe.resolve(s, 'Impale Chance', type='Passive')
    probe.validate(s, {'gem_groups': [{'skill': 'gem:SplittingSteel'}],
                       'passives': ['Armour and Evasion, Impale Chance']})


def p47():
    s = 47
    rows = probe.resolve(s, 'MinionDamageAlsoAffectsYou', type='Modifier')
    for m in rows[:2]:
        probe.carriers(s, m['id'], edge_types=['unique_modifier_association'])
    probe.resolve(s, 'player_and_minion_notable2240', type='Passive')
    probe.validate(s, {'gem_groups': [{'skill': 'gem:EnchantmentOfReflectionWhenHit4'}]})


def p66():
    s = 66
    probe.carriers(s, 'stat:base_spell_suppression_chance_%')
    probe.resolve(s, 'suppression', type='Passive')
    probe.validate(s, {'passives': ['Evasion and Suppression']})


def p67():
    s = 67
    probe.resolve(s, 'omniscience', type='UniqueItem')
    probe.carriers(s, 'stat:attack_maximum_added_lightning_damage_per_10_dex')
    probe.resolve(s, 'strength', type='Passive')
    probe.validate(s, {'items': ['Presence of Chayula']})


def p01():
    s = 1
    probe.carriers(s, 'stat:max_attack_added_chaos_damage_per_100_mana')
    probe.carriers(s, 'stat:maximum_mana_+%')


def p19():
    s = 19
    probe.carriers(s, 'stat:global_chance_to_blind_on_hit_%')
    rows = probe.resolve(s, 'blinded', type='Stat')
    for st in [r['id'] for r in rows if 'blinded' in r['id']][:2]:
        probe.carriers(s, st)
    probe.resolve(s, 'SupportBlind', type='Gem')


def p25():
    s = 25
    probe.carriers(s, 'stat:intelligence_+%_per_equipped_unique')
    probe.resolve(s, 'per_equipped_unique', type='Stat')


def p29():
    s = 29
    probe.carriers(s, 'stat:poison_damage_+%_with_over_300_dexterity')
    probe.carriers(s, 'stat:poison_duration_+%_with_over_150_intelligence')
    probe.resolve(s, 'poison', type='Mechanic')
    rows = probe.resolve(s, 'poison', type='Gem')
    print(f'    poison gems: {[r["id"] for r in rows][:10]}')
    probe.validate(s, {'items': ['Dendrobate']})


def p30():
    s = 30
    rows = probe.resolve(s, 'blinded', type='Stat')
    for st in [r['id'] for r in rows if 'blinded' in r['id']][:2]:
        probe.carriers(s, st)


def p64():
    s = 64
    probe.carriers(s, 'stat:keystone_minion_instability')
    probe.resolve(s, 'Absolution', type='Gem')
    probe.validate(s, {'passives': ['Minion Instability'],
                       'gem_groups': [{'skill': 'gem:Absolution'}]})


if __name__ == '__main__':
    plans = {int(k): v for k, v in {
        '09': p09, '12': p12, '14': p14, '16': p16, '21': p21, '32': p32,
        '33': p33, '35': p35, '43': p43, '47': p47, '66': p66, '67': p67,
        '01': p01, '19': p19, '25': p25, '29': p29, '30': p30, '64': p64,
    }.items()}
    only = {int(x) for x in sys.argv[1].split(',')} if len(sys.argv) > 1 else set(plans)
    before = probe.A.n
    for idx in sorted(only):
        print(f'---- seed {idx:02d} ----', flush=True)
        plans[idx]()
        print(f'    [calls this seed: {probe.A.n - before}]', flush=True)
        before = probe.A.n
