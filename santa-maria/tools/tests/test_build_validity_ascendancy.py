"""Ascendancy composition tests for phase7_build_validity (assert-style).

Run: cd santa-maria && uv run python -m tools.tests.test_build_validity_ascendancy
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import phase7_build_validity as bv

VALID, INVALID, UNKNOWN = bv.VALID, bv.INVALID, bv.UNKNOWN

# real KB nodes (Default tree): Necromancer notables/smalls, Juggernaut notable
NEC_NOTABLES = ['AscendancyNecromancer9', 'AscendancyNecromancer11',
                'AscendancyNecromancer14', 'AscendancyNecromancer16']
NEC_NOTABLE5 = 'AscendancyNecromancer12'          # Commander of Darkness
NEC_SMALLS = ['AscendancyNecromancer1', 'AscendancyNecromancer5']
JUG_NOTABLE = 'AscendancyJuggernaut7'             # Unstoppable
CLASSLESS_KEYSTONE = 'Vaal Pact'                  # regular-tree, ascendancy=None
DATA_GAP_SMALL = 'AlternateAscendancyWardenSmall5'  # Ascendancy* id, class None


def test_valid_single_ascendancy():
    r = bv.validate_build(bv.BuildState(passives=NEC_NOTABLES))
    assert r['status'] == VALID, r
    assert 'ascendancy_composition' in r['checked']
    pc = r['passive_checks']
    assert pc['class_mix']['classes'] == ['Necromancer']
    assert pc['notable_cap']['count'] == 4


def test_no_ascendancy_at_final():
    # classless keystone only -> final build lacks an Ascendancy
    r = bv.validate_build(bv.BuildState(passives=[CLASSLESS_KEYSTONE]))
    assert r['status'] == INVALID, r
    assert 'no Ascendancy' in r['reason']
    # incremental (final=False) does not penalize the missing ascendancy yet
    r2 = bv.validate_addition(bv.BuildState(), CLASSLESS_KEYSTONE)
    assert r2['status'] == VALID, r2


def test_two_ascendancies_invalid():
    r = bv.validate_build(bv.BuildState(passives=NEC_NOTABLES + [JUG_NOTABLE]))
    assert r['status'] == INVALID, r
    assert 'mixed Ascendancies' in r['reason']
    assert 'Juggernaut' in r['reason'] and 'Necromancer' in r['reason']


def test_notable_cap_4():
    r = bv.validate_build(bv.BuildState(passives=NEC_NOTABLES))
    assert r['status'] == VALID, r
    r = bv.validate_build(bv.BuildState(passives=NEC_NOTABLES + [NEC_NOTABLE5]))
    assert r['status'] == INVALID, r
    assert 'cap of 4' in r['reason']
    # smalls do not count toward the cap
    r = bv.validate_build(bv.BuildState(passives=NEC_NOTABLES + NEC_SMALLS))
    assert r['status'] == VALID, r
    assert r['passive_checks']['notable_cap']['count'] == 4


def test_addition_second_ascendancy_rejected():
    state = bv.BuildState(passives=NEC_NOTABLES)
    r = bv.validate_addition(state, JUG_NOTABLE)
    assert r['status'] == INVALID, r
    assert 'second Ascendancy' in r['reason']
    assert 'Juggernaut' in r['reason']
    # state not mutated (check-then-commit)
    assert state.passives == NEC_NOTABLES


def test_unclassifiable_is_unknown_never_guessed():
    r = bv.validate_build(bv.BuildState(passives=[DATA_GAP_SMALL]),
                          final=False)      # skip the final-only class check
    assert r['status'] == UNKNOWN, r
    assert 'unclassifiable' in r['reason']
    # classless regular-tree keystone is legal (consistent ascendancy=None)
    r2 = bv.validate_addition(bv.BuildState(passives=NEC_NOTABLES),
                              CLASSLESS_KEYSTONE)
    assert r2['status'] == VALID, r2


def test_passive_resolution_errors():
    for bad in ('Not A Passive Node', 'Minion Damage and Life'):
        # unknown name / ambiguous name (several Necromancer smalls share it)
        try:
            bv.validate_build(bv.BuildState(passives=[bad]))
            raise AssertionError(f'{bad!r} should not resolve')
        except ValueError as e:
            assert 'passive node not found' in str(e) or \
                'ambiguous' in str(e), e


def test_add_passive_immutability():
    s = bv.BuildState(passives=['AscendancyNecromancer1'])
    s2 = s.add_passive('AscendancyNecromancer9')
    assert s.passives == ['AscendancyNecromancer1']
    assert s2.passives == ['AscendancyNecromancer1', 'AscendancyNecromancer9']
    assert s2.items == []


if __name__ == '__main__':
    fns = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for fn in fns:
        fn()
        print(f'{fn.__name__}: OK')
    print(f'{len(fns)} tests passed')
