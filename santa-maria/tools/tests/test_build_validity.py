#!/usr/bin/env python3
"""Build-validity API — assert-based tests.

Run: python3 tools/tests/test_build_validity.py
Covers: valid configurations; the required HoWA + Jiquani's Potential
regression (individually-valid items, invalid composition); incremental
detection with no state mutation on rejection; valid continuation; final
validate_build (single + multiple conflicts); unknown outcomes (no slot
model, unresolved parent weapon, ambiguous weapon context); the pinned
unique-duplication limitation; gem groups (valid / weapon-restriction
invalid / chain invalid); CLI integration usable by the discovery agent.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import phase6_api as api
import phase7_build_validity as bv

# fixtures verified against the KB (see test_build_feasibility.py)
HOWA = 'unique:597'                              # Hand of Wisdom and Action, Claw (1H)
JIQUANI = 'unique:1486'                          # Jiquani's Potential, Staff (2H)
REDBEAK, ICHIMONJI = 'unique:1', 'unique:321'    # 1H swords
STAFF, SHIELD = 'unique:1026', 'unique:1019'     # The Blood Thorn, Demigod's Beacon
RING_A, RING_B = 'unique:1003', 'unique:1006'    # Demigod's Eye, Doedre's Damning
VOLLS, BRASS = 'unique:8', 'unique:560'          # two body armours
JEWEL, WELLHOOK = 'unique:1054', 'unique:1554'   # no slot model / unresolved parent
HH = 'gem:HolyHammers'                           # Staff/Sceptre/Mace restrictions


def test_valid_configurations():
    g = api.GraphDB()
    r = bv.validate_addition(bv.BuildState([REDBEAK]), SHIELD, g)
    assert r['status'] == bv.VALID and not r['conflicts'], r
    s = bv.BuildState()
    r1 = bv.validate_addition(s, RING_A, g)
    assert r1['status'] == bv.VALID, r1
    r2 = bv.validate_addition(s.add(RING_A), RING_B, g)
    assert r2['status'] == bv.VALID, r2
    full = bv.BuildState([REDBEAK, SHIELD, RING_A, RING_B])
    r = bv.validate_build(full, g)
    assert r['status'] == bv.VALID, r
    assert r['checked'] == ['slot_occupancy', 'weapon_configuration',
                            'item_availability'], r
    print('ok: valid 1H+offhand, two-ring, and single-slot additions')


def test_howa_jiquani_regression():
    g = api.GraphDB()
    # required regression case: each item individually valid, composition invalid
    assert bv.validate_build(bv.BuildState([HOWA]), g)['status'] == bv.VALID
    assert bv.validate_build(bv.BuildState([JIQUANI]), g)['status'] == bv.VALID
    r = bv.validate_addition(bv.BuildState([HOWA]), JIQUANI, g)
    assert r['status'] == bv.INVALID, r
    assert any(c['slot'] == 'weapon' for c in r['conflicts']), r
    assert "Jiquani's Potential" in r['reason'] \
        and 'Hand of Wisdom and Action' in r['reason'], r
    print('ok: HoWA + Jiquani\'s Potential -> INVALID (weapon/offhand conflict)')


def test_incremental_detection_no_mutation():
    g = api.GraphDB()
    s = bv.BuildState([HOWA])
    r = bv.validate_addition(s, JIQUANI, g)
    assert r['status'] == bv.INVALID, r
    assert s.items == [HOWA], 'rejected candidate must not be committed'
    assert r['candidate'] == JIQUANI and r['conflicts'], r
    print('ok: invalid candidate rejected, build state unchanged')


def test_valid_continuation_after_rejection():
    g = api.GraphDB()
    s = bv.BuildState([HOWA])
    assert bv.validate_addition(s, JIQUANI, g)['status'] == bv.INVALID
    r = bv.validate_addition(s, RING_A, g)
    assert r['status'] == bv.VALID, r
    s2 = s.add(RING_A)
    assert bv.validate_addition(s2, RING_B, g)['status'] == bv.VALID
    r = bv.validate_build(s2.add(RING_B), g)
    assert r['status'] == bv.VALID, r
    print('ok: state remains usable after a rejected candidate')


def test_validate_build_multiple_conflicts():
    g = api.GraphDB()
    r = bv.validate_build(bv.BuildState([VOLLS, BRASS, STAFF, SHIELD]), g)
    assert r['status'] == bv.INVALID, r
    assert {c['slot'] for c in r['conflicts']} == {'body', 'offhand'}, r
    assert all(c['items_named'] for c in r['conflicts']), r
    print('ok: validate_build reports all conflicts, not just the first')


def test_unknown_outcomes():
    g = api.GraphDB()
    r = bv.validate_addition(bv.BuildState([REDBEAK]), JEWEL, g)
    assert r['status'] == bv.UNKNOWN and r['unsupported'], r
    assert 'no slot model' in r['reason'], r
    r = bv.validate_addition(bv.BuildState([REDBEAK, SHIELD]), WELLHOOK, g)
    assert r['status'] == bv.UNKNOWN, r
    assert 'parent weapon class' in r['reason'], r
    print('ok: unchecked constraints surface as unknown, never valid')


def test_duplicate_unique_limitation():
    g = api.GraphDB()
    r = bv.validate_addition(bv.BuildState([HOWA]), HOWA, g)
    # documents current behavior — duplication is NOT modeled (limitation)
    assert r['status'] == bv.VALID, r
    assert any('duplication' in lim for lim in r['limitations']), r
    print('ok: unique-duplication limitation pinned and reported')


def test_gem_groups():
    g = api.GraphDB()
    # uniquely determined weapon + allowed restriction + valid chain -> valid
    s = bv.BuildState([STAFF], [{'skill': HH,
                                 'supports': ['gem:SupportMultistrike']}])
    r = bv.validate_build(s, g)
    assert r['status'] == bv.VALID and 'gem_support' in r['checked'], r
    # determined weapon, skill restriction violated -> invalid
    s = bv.BuildState([ICHIMONJI], [{'skill': 'gem:GroundSlam'}])
    r = bv.validate_build(s, g)
    assert r['status'] == bv.INVALID, r
    assert r['gem_checks'][0]['weapon_restriction']['result'] == bv.INVALID, r
    # determined weapon, invalid support chain (weapon-independent) -> invalid
    s = bv.BuildState([ICHIMONJI],
                      [{'skill': HH, 'supports': ['gem:SupportMultistrike',
                                                  'gem:SupportChargedTraps']}])
    r = bv.validate_build(s, g)
    assert r['status'] == bv.INVALID, r
    assert r['gem_checks'][0]['support_chain']['result'] == bv.INVALID, r
    # ambiguous weapon context (two 1H) -> unknown with explicit reason
    s = bv.BuildState([REDBEAK, ICHIMONJI], [{'skill': HH}])
    r = bv.validate_build(s, g)
    assert r['status'] == bv.UNKNOWN, r
    assert 'not uniquely determined' in r['reason'], r
    assert r['gem_checks'][0]['weapon_restriction']['result'] == bv.UNKNOWN, r
    # no weapon at all -> unknown, never guessed
    s = bv.BuildState([], [{'skill': HH}])
    r = bv.validate_build(s, g)
    assert r['status'] == bv.UNKNOWN and '0 weapon-class items' in r['reason'], r
    print('ok: gem groups valid/invalid/unknown; weapon context never guessed')


def test_cli_integration():
    root = Path(__file__).resolve().parents[2]
    cli = root / 'tools' / 'phase7_build_validity.py'

    def run(*args):
        p = subprocess.run([sys.executable, str(cli), *args],
                           capture_output=True, text=True, cwd=root)
        assert p.returncode == 0, p.stderr
        return json.loads(p.stdout)

    r = run('add', "Jiquani's Potential", 'Hand of Wisdom and Action')
    assert r['status'] == 'invalid' and r['conflicts'], r
    r = run('add', "Demigod's Beacon", 'Hand of Wisdom and Action')
    assert r['status'] == 'valid', r
    r = run('build', 'Hand of Wisdom and Action', "Demigod's Eye",
            "Doedre's Damning")
    assert r['status'] == 'valid', r
    r = run('build', 'The Blood Thorn', '--gem', HH, 'gem:SupportMultistrike')
    assert r['status'] == 'valid' and r['gem_checks'], r
    print('ok: CLI add/build round-trips (discovery-agent usable)')


if __name__ == '__main__':
    test_valid_configurations()
    test_howa_jiquani_regression()
    test_incremental_detection_no_mutation()
    test_valid_continuation_after_rejection()
    test_validate_build_multiple_conflicts()
    test_unknown_outcomes()
    test_duplicate_unique_limitation()
    test_gem_groups()
    test_cli_integration()
    print('ALL TESTS PASSED')
