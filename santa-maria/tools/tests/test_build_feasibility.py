#!/usr/bin/env python3
"""Build feasibility layer — assert-based tests.

Run: python3 tools/tests/test_build_feasibility.py
Covers: slot conflicts/capacities/off-hand rules/unsupported classes; the five
researched supportability cases; unknown outcomes for missing data; conservative
exclusion-expression handling; ordered support chains with added_types mutation;
weapon restrictions. Expectations are derived from actual payloads wherever
possible; only the research-verified IDs are pinned as fixtures.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import phase6_api as api
import phase7_build_feasibility as bf

# fixtures verified during the feasibility research
VOLLS, BRASS = 'unique:8', 'unique:560'          # Body Armour pair
RING_A, RING_B = 'unique:1003', 'unique:1006'    # Demigod's Eye, Doedre's Damning
DAGGER, STAFF = 'unique:1012', 'unique:1026'     # Bino's Kitchen Knife, The Blood Thorn
BOW, SHIELD = 'unique:10', 'unique:1019'         # Silverbranch, Demigod's Beacon
QUIVER, JEWEL = 'unique:1036', 'unique:1054'     # Asphyxia's Wrath, Glorious Vanity
WELLHOOK = 'unique:1554'                         # Mace parent, no PoB block -> unknown
ICHIMONJI, REDBEAK = 'unique:321', 'unique:1'    # parent 'Sword', both 1H
QDECRE, KAOM = 'unique:107', 'unique:0'          # Queen's Decree 2H sword, Kaom's Primacy 2H axe
CHOBER = 'unique:120'                            # Chober Chaber, parent 'Mace' -> 2H
HH = 'gem:HolyHammers'


def test_slot_conflicts_and_capacities():
    g = api.GraphDB()
    r = bf.slot_check([VOLLS, BRASS], g)
    assert not r['valid'] and r['conflicts'] == [
        {'slot': 'body', 'items': sorted([VOLLS, BRASS]),
         'reason': 'capacity 1 exceeded (2 slot units)'}], r
    assert bf.slot_check([RING_A, RING_B], g)['valid'], 'two rings must be valid'
    assert bf.slot_check([DAGGER, SHIELD], g)['valid'], '1H + shield must be valid'
    r = bf.slot_check([STAFF, SHIELD], g)
    assert not r['valid'] and any('two-handed melee' in c['reason']
                                  for c in r['conflicts']), r
    r = bf.slot_check([BOW, SHIELD], g)
    assert not r['valid'] and any('one-handed main' in c['reason']
                                  for c in r['conflicts']), r
    r = bf.slot_check([BOW, QUIVER], g)
    assert r['valid'], f'bow + quiver must be valid: {r}'
    r = bf.slot_check([QUIVER], g)
    assert not r['valid'] and any('quiver requires a bow' in c['reason']
                                  for c in r['conflicts']), r
    r = bf.slot_check([STAFF, BOW], g)
    assert not r['valid'] and any(c['slot'] == 'weapon' for c in r['conflicts']), r
    print('ok: slot conflicts, capacities and off-hand rules')


def test_slot_unsupported_explicit():
    g = api.GraphDB()
    r = bf.slot_check([JEWEL], g)
    assert r['valid'] and not r['conflicts'], r
    assert r['undetermined'] and r['unsupported'][0]['item_class'] == 'Jewel', r
    r = bf.slot_check([WELLHOOK], g)
    assert r['undetermined'] and r['valid'], r
    assert r['unsupported'][0]['item_class'] == 'Mace', r
    assert 'parent weapon class' in r['unsupported'][0]['reason'], r
    print('ok: unsupported/unresolved classes reported explicitly, never assumed')


def test_weapon_parent_resolution():
    g = api.GraphDB()
    cases = [(ICHIMONJI, 'One Hand Sword', '1H'), (REDBEAK, 'One Hand Sword', '1H'),
             (QDECRE, 'Two Hand Sword', '2H'), (KAOM, 'Two Hand Axe', '2H'),
             (CHOBER, 'Two Hand Mace', '2H'),
             ('unique:117', 'Sceptre', '1H'),           # Nycta's Lantern
             ('unique:1132', 'One Hand Sword', '1H'),   # The Surging Thoughts
             ('unique:1026', 'Staff', None),            # concrete class: passthrough
             ('unique:10', 'Bow', None)]                # concrete class: passthrough
    for uid, want_cls, want_h in cases:
        r = bf.resolve_weapon_class(uid, g)
        assert r['item_class'] == want_cls, (uid, r)
        if want_h:
            assert r['resolved'] and r['handedness'] == want_h, (uid, r)
        else:
            assert not r['resolved'] and r['reason'] == 'not a parent weapon class', (uid, r)
    print('ok: parent-class weapon resolution (9 cases, deterministic chain)')


def test_resolved_handedness_feasibility():
    g = api.GraphDB()
    # resolved 1H + shield valid
    assert bf.slot_check([REDBEAK, SHIELD], g)['valid'], 'Redbeak (1H) + shield'
    assert bf.slot_check([ICHIMONJI, SHIELD], g)['valid'], 'Ichimonji (1H) + shield'
    # resolved 2H + shield invalid; 2H occupies the off-hand
    r = bf.slot_check([QDECRE, SHIELD], g)
    assert not r['valid'] and any('two-handed melee' in c['reason']
                                  for c in r['conflicts']), r
    r = bf.slot_check([KAOM, QUIVER], g)
    assert not r['valid'] and any('off-hand' in c['reason'] for c in r['conflicts']), r
    # assignment carries the resolved class
    a = bf.slot_check([ICHIMONJI], g)['assignments'][0]
    assert a['resolved_item_class'] == 'One Hand Sword' and a['slots'] == ['weapon'], a
    # weapon axis uses the resolved class
    assert bf.weapon_check('gem:Lacerate', ICHIMONJI, g)['result'] == bf.VALID, \
        'One Hand Sword is a Lacerate weapon'
    assert bf.weapon_check('gem:GroundSlam', ICHIMONJI, g)['result'] == bf.INVALID, \
        'swords are not Ground Slam weapons'
    # unresolved parent class degrades to unknown, never invalid/assumed
    r = bf.weapon_check('gem:Lacerate', WELLHOOK, g)
    assert r['result'] == bf.UNKNOWN and 'unresolved' in r['reason'], r
    print('ok: resolved handedness drives slot/weapon checks; unresolved stays unknown')


def test_resolution_deterministic():
    g = api.GraphDB()
    items = [ICHIMONJI, REDBEAK, QDECRE, CHOBER, WELLHOOK]
    assert bf.slot_check(items, g) == bf.slot_check(items, g)
    assert bf.resolve_weapon_class(ICHIMONJI, g) == bf.resolve_weapon_class(ICHIMONJI, g)
    print('ok: resolution deterministic across repeated calls')


def test_can_support_five_cases():
    g = api.GraphDB()
    cases = [('gem:SupportMultistrike', HH, bf.VALID),
             ('gem:SupportChargedTraps', HH, bf.INVALID),
             ('gem:SupportPointBlank', HH, bf.INVALID),
             ('gem:SupportChargedTraps', 'gem:LightningTrap', bf.VALID),
             ('gem:SupportElementalFocus', HH, bf.VALID)]
    for b, a, want in cases:
        r = bf.can_support(b, a, g)
        assert r['result'] == want, (b, a, r)
    print('ok: all five researched supportability cases')


def test_unknown_outcomes():
    g = api.GraphDB()
    r = bf.can_support('gem:SupportMultistrike', 'gem:AfflictionSplitColdIceSpikes', g)
    assert r['result'] == bf.UNKNOWN and 'no active_skill.types' in r['reason'], r
    r = bf.can_support('gem:DelveModSocketedAttackSpeed', HH, g)
    assert r['result'] == bf.UNKNOWN and 'no support contract data' in r['reason'], r
    assert bf.can_support(HH, HH, g)['result'] == bf.INVALID, 'skill is not a support'
    assert bf.can_support('gem:SupportMultistrike',
                          'gem:SupportMultistrike', g)['result'] == bf.INVALID
    print('ok: missing/incomplete data -> unknown; non-supports -> invalid')


def test_exclusion_expressions():
    g = api.GraphDB()
    # operator tokens (NOT/AND) + intersecting plain token -> ambiguous unknown
    # (SupportArcaneSurge: allowed=[Spell] ok for LightningTrap, but its
    #  NOT/AND-encoded exclusion intersects 'Trapped' -> not confidently evaluable)
    r = bf.can_support('gem:SupportArcaneSurge', 'gem:LightningTrap', g)
    assert r['result'] == bf.UNKNOWN and 'ambiguous' in r['reason'], r
    # operator tokens with allowed-gate miss -> plain invalid (unambiguous allowed)
    assert bf.can_support('gem:SupportMultistrike', 'gem:VaalAbsolution', g)['result'] == bf.INVALID
    # plain exclusion, intersecting -> invalid (derived from actual payload)
    r = bf.can_support('gem:BattlemagesCrySupport', 'gem:LightningTrap', g)
    assert r['result'] == bf.INVALID and 'Trapped' in r['reason'], r
    # plain-only excluded + allowed pass + disjoint -> valid, derived from payloads
    OPS = bf.EXPRESSION_OPS
    nodes = g._load_nodes()
    derived = None
    for nid, (t, p) in sorted(nodes.items()):
        if t != 'Gem' or not p.get('is_support'):
            continue
        sg = p.get('support_gem') or {}
        ex = sg.get('excluded_types') or []
        if not ex or set(ex) & OPS:
            continue
        r = bf.can_support(nid, HH, g)
        if r['result'] == bf.VALID:
            derived = (nid, r)
            break
    assert derived, 'expected at least one plain-exclusion valid case against HH'
    print(f'   derived plain-exclusion valid case: {derived[0]}')
    # plain exclusion, disjoint -> valid (Multistrike -> HH covers this too)
    assert bf.can_support('gem:SupportMultistrike', HH, g)['result'] == bf.VALID
    print('ok: exclusion expressions handled conservatively')


def test_ordered_support_chain():
    g = api.GraphDB()
    r = bf.validate_support_chain(HH, ['gem:GeneralsCrySupport',
                                       'gem:SupportMultistrike'], g)
    assert [s['result'] for s in r['steps']] == [bf.VALID, bf.UNKNOWN], r
    assert 'NonRepeatable' in r['steps'][0]['added_types_applied'], r
    assert 'NonRepeatable' in r['steps'][1]['types_before'], r
    assert r['result'] == bf.UNKNOWN, r
    # standalone Multistrike is valid -> the earlier support changed the outcome
    assert bf.can_support('gem:SupportMultistrike', HH, g)['result'] == bf.VALID
    # reverse order stays valid end-to-end
    r = bf.validate_support_chain(HH, ['gem:SupportMultistrike',
                                       'gem:GeneralsCrySupport'], g)
    assert r['result'] == bf.VALID, r
    # invalid later step with full debug state
    r = bf.validate_support_chain(HH, ['gem:SupportMultistrike',
                                       'gem:SupportChargedTraps'], g)
    assert r['result'] == bf.INVALID and r['steps'][1]['result'] == bf.INVALID, r
    assert r['steps'][1]['types_before'] == r['steps'][0]['types_after'], r
    # unknown preserved end-to-end (skill without types)
    r = bf.validate_support_chain('gem:AfflictionSplitColdIceSpikes',
                                  ['gem:SupportMultistrike'], g)
    assert r['result'] == bf.UNKNOWN and r['steps'][0]['result'] == bf.UNKNOWN, r
    assert r['steps'][0]['types_before'] == [] and r['final_types'] == [], r
    print('ok: ordered chains accumulate added_types; order changes outcomes; unknown preserved')


def test_weapon_restrictions():
    g = api.GraphDB()
    assert bf.weapon_check(HH, 'Sceptre', g)['result'] == bf.VALID
    assert bf.weapon_check(HH, 'Bow', g)['result'] == bf.INVALID
    assert bf.weapon_check(HH, BOW, g)['result'] == bf.INVALID, 'unique resolves to Bow'
    r = bf.weapon_check(HH, None, g)
    assert r['result'] == bf.UNKNOWN, r
    r = bf.weapon_check('gem:LightningTrap', 'Bow', g)
    assert r['result'] == bf.VALID and 'no weapon restrictions' in r['reason'], r
    print('ok: weapon restriction checks; missing restrictions never invalid')


def test_deterministic():
    g = api.GraphDB()
    a = bf.slot_check([VOLLS, BRASS, RING_A, RING_B, DAGGER, SHIELD, JEWEL], g)
    b = bf.slot_check([VOLLS, BRASS, RING_A, RING_B, DAGGER, SHIELD, JEWEL], g)
    assert a == b, 'slot_check must be deterministic'
    c = bf.validate_support_chain(HH, ['gem:GeneralsCrySupport',
                                       'gem:SupportMultistrike'], g)
    d = bf.validate_support_chain(HH, ['gem:GeneralsCrySupport',
                                       'gem:SupportMultistrike'], g)
    assert c == d, 'chain validation must be deterministic'
    print('ok: deterministic')


if __name__ == '__main__':
    test_slot_conflicts_and_capacities()
    test_slot_unsupported_explicit()
    test_weapon_parent_resolution()
    test_resolved_handedness_feasibility()
    test_can_support_five_cases()
    test_unknown_outcomes()
    test_exclusion_expressions()
    test_ordered_support_chain()
    test_weapon_restrictions()
    test_resolution_deterministic()
    test_deterministic()
    print('ALL TESTS PASSED')
