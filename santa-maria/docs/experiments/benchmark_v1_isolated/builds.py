#!/usr/bin/env python3
"""Stage D — build assembly + validation on promoted seeds (public API only,
audited). Validates concrete build states; records VALID/INVALID/UNKNOWN."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe  # noqa: E402

MECH = ('stat_mechanic_relation', 'stat_mechanic_operand',
        'stat_mechanic_variant')


def unique_carriers_of_stat(seed, stat, rows=None, maxprobe=3):
    """From carriers(stat) rows, probe UMA for unique-named mods (bounded)."""
    if rows is None:
        rows = probe.carriers(seed, stat, show=0)
    mods = [r['carrier'] for r in rows
            if r['edge_type'] == 'modifier_grants_stat' and 'Unique' in r['carrier']]
    for m in mods[:maxprobe]:
        probe.carriers(seed, m, edge_types=['unique_modifier_association'], show=4)


def b09():
    s = 9
    rows = probe.resolve(s, 'vs_shocked', type='Stat')
    cons = [r['id'] for r in rows if r['id'].startswith('stat:damage_+%_vs_shocked')]
    for st in cons[:1]:
        probe.carriers(s, st)
    probe.carriers(s, 'mod:AlwaysCritShockedEnemiesUnique__1',
                   edge_types=['unique_modifier_association'], show=4)
    st = probe.validate(s, {'passives': ['Shaper of Storms']})


def b12():
    s = 12
    st = probe.validate(s, {'passives': ['Pursuit of Faith',
                                         'passive:AscendancyHeirophant2'],
                            'gem_groups': [{'skill': 'gem:SearingBond'}]})


def b14():
    s = 14
    unique_carriers_of_stat(s, 'stat:max_endurance_charges')
    st = probe.validate(s, {'passives': ['Unflinching',
                                         'passive:maximum_endurance_charges132']})
    st = probe.validate(s, {'items': ["Kaom's Sign", "Daresso's Defiance"],
                            'passives': ['Unflinching',
                                         'passive:maximum_endurance_charges132']})


def b16():
    s = 16
    st = probe.validate(s, {'passives': ['Unholy Authority', 'Whispers of Doom']})


def b21():
    s = 21
    st = probe.validate(s, {'passives': ['Swift Killer'],
                            'gem_groups': [{'skill': 'gem:Frenzy'},
                                           {'skill': 'gem:BloodRage'}]})


def b32():
    s = 32
    rows = probe.resolve(s, 'frenzy_charges', type='Passive')
    pid = next((r['id'] for r in rows if r['id'].startswith('passive:frenzy_charges')), None)
    rows = probe.resolve(s, 'Avidity', type='Passive')
    avidity = next((r['id'] for r in rows if r['id'] == 'passive:AscendancyDeadeye10'), None)
    st = probe.validate(s, {'items': ['Badge of the Brotherhood'],
                            'passives': [p for p in (pid, avidity) if p]})


def b33():
    s = 33
    rows = probe.resolve(s, 'Critical Strike Chance and Multiplier', type='Passive')
    base = [r for r in rows if 'Custom' not in r['id']]
    st = probe.validate(s, {'items': ['Facebreaker'],
                            'gem_groups': [{'skill': 'gem:AncestralWarchief'}],
                            'passives': ['passive:AscendancyAssassin5']})


def b35():
    s = 35
    rows = probe.carriers(s, 'stat:damage_+%_per_endurance_charge', show=0)
    unique_carriers_of_stat(s, 'stat:damage_+%_per_endurance_charge', rows)
    st = probe.validate(s, {'passives': ['Disciple of the Unyielding',
                                         'Unyielding']})


def b43():
    s = 43
    rows = probe.carriers(s, 'stat:attacks_impale_on_hit_%_chance', show=0)
    unique_carriers_of_stat(s, 'stat:attacks_impale_on_hit_%_chance', rows)
    st = probe.validate(s, {'gem_groups': [{'skill': 'gem:SplittingSteel'}],
                            'passives': ['Armour and Evasion, Impale Chance']})


def b47():
    s = 47
    probe.carriers(s, 'stat:additive_minion_damage_modifiers_apply_to_you_at_%_value')
    probe.carriers(s, 'stat:minion_damage_increases_and_reductions_also_affects_you')
    probe.validate(s, {'gem_groups': [{'skill': 'gem:EnchantmentOfReflectionWhenHit4'}],
                       'passives': ['Spiritual Aid', 'Commander of Darkness']})


def b64():
    s = 64
    st = probe.validate(s, {'passives': ['Minion Instability', 'Commander of Darkness']})
    st = probe.validate(s, {'passives': ['Minion Instability', 'Commander of Darkness'],
                            'gem_groups': [{'skill': 'gem:Absolution'}]})


def b66():
    s = 66
    rows = probe.carriers(s, 'stat:base_spell_suppression_chance_%', show=0)
    unique_carriers_of_stat(s, 'stat:base_spell_suppression_chance_%', rows)
    st = probe.validate(s, {'passives': ['passive:AscendancyRaider5']})


def b67():
    s = 67
    probe.resolve(s, 'omniscience', type='UniqueItem')
    probe.carriers(s, 'stat:attack_maximum_added_lightning_damage_per_10_dex')
    probe.validate(s, {'items': ['Crystallised Omniscience']})


def b19():
    s = 19
    probe.carriers(s, 'stat:damage_+%_vs_blinded_enemies')
    probe.can_support(s, 'gem:SupportBlind', 'gem:VaalBladeFlurry')
    probe.validate(s, {'passives': ['Born in the Shadows'],
                       'gem_groups': [{'skill': 'gem:VaalBladeFlurry',
                                       'supports': ['gem:SupportBlind']}]})


def b25():
    s = 25
    probe.carriers(s, 'stat:damage_+%_final_per_equipped_unique')
    probe.carriers(s, 'stat:minion_damage_+%_final_per_equipped_unique')
    probe.validate(s, {'items': ['Perandus Signet']})


def b29():
    s = 29
    probe.validate(s, {'items': ['Dendrobate'],
                       'gem_groups': [{'skill': 'gem:PoisonousConcoction'}]})


if __name__ == '__main__':
    plans = {int(k): v for k, v in {
        '09': b09, '12': b12, '14': b14, '16': b16, '21': b21, '32': b32,
        '33': b33, '35': b35, '43': b43, '47': b47, '64': b64, '66': b66, '67': b67,
        '19': b19, '25': b25, '29': b29,
    }.items()}
    only = {int(x) for x in sys.argv[1].split(',')} if len(sys.argv) > 1 else set(plans)
    before = probe.A.n
    for idx in sorted(only):
        print(f'---- build seed {idx:02d} ----', flush=True)
        plans[idx]()
        print(f'    [calls this build: {probe.A.n - before}]', flush=True)
        before = probe.A.n
