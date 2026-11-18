#!/usr/bin/env python3
"""m5 disambiguation: deterministic fail-closed unique->modifier resolution.

Run: cd santa-maria && uv run python -m tools.tests.test_m5_disambiguation

Unit tests run resolve_unique_all on synthetic fixtures (no KB needed).
Live gates read cache/nodes.db (+ cache/edges.db) and pin the REBUILT KB:
on the pre-fix build they fail by design (Shaper's Touch 3/6, Crown 2/5).

Fix contract (whispers04):
  1. exact singleton -> resolved;
  2. alt-quality twins (Divergent*/Anomalous*/Phantasmal*) demoted when a
     non-alt candidate remains for the same line;
  3. multi-line mods keep a claiming line only with cross-line ownership
     evidence (another of their text lines matching a block line that still
     lists them); 'non-first line' alone is never a rejection reason;
  4. anything still multi-candidate stays ambiguous — no edge, never guess.
"""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import extract_nodes as en

ROOT = Path(__file__).resolve().parents[2]

SHAPERS = 'unique:573'
CROWN = 'unique:1083'
WHISPERS = 'unique:1461'
ALT = ('Divergent', 'Anomalous', 'Phantasmal')


# ---------------------------------------------------------------- fixtures

def _resolve_world(mods, blocks, exact, base2class):
    """Call resolve_unique_all on a synthetic universe (m1/m2/m4 disabled)."""
    mods_by_key = {}
    for k, text in mods.items():
        mods_by_key[k] = {'id': k, 'text': text, 'generation_type': 'unique',
                          'stats': []}
    pob = {'exact': {ln: set(ks) for ln, ks in exact.items()},
           'skel': {}, 'base2class': dict(base2class)}
    uniques = [(u, {'id': u, 'visual_identity': None}) for u in blocks]
    res = en.resolve_unique_all(uniques, mods_by_key, None, {}, [], [],
                                dict(blocks), set(), pob=pob)
    return res


def _m5(res, ukey):
    tg = res[ukey]['resolved_targets']
    return {t['target_key']: t for t in tg if t['method'] == 5}


def _m5_resolved(res, ukey):
    return {k for k, t in _m5(res, ukey).items() if t['status'] == 'resolved'}


# ------------------------------------------------------------ unit tests

def test_alt_twin_demoted_base_resolves():
    """Crown shape: alt twin + multi-line collider demoted, base resolves."""
    en.M5_DIAG.clear()
    tom, div, maven = ('TransfigurationOfMindUnique__1',
                       'DivergentTransfigurationOfMindUnique__1',
                       'MaximumManaUberMaven')
    res = _resolve_world(
        mods={tom: 'Transfiguration of Mind',
              div: 'Transfiguration of Mind',
              maven: '(12-15)% increased maximum Mana\nTransfiguration of Mind'},
        blocks={'Test Crown':
                'Test Crown\nProphet Crown\nTransfiguration of Mind\n'},
        exact={'Transfiguration of Mind': {tom, div, maven}},
        base2class={'Prophet Crown': 'Helmet'})
    assert _m5_resolved(res, 'Test Crown') == {tom}, _m5(res, 'Test Crown')
    assert en.M5_DIAG.get('m5_demoted_alt_twin', 0) >= 1
    assert en.M5_DIAG.get('m5_demoted_multiline', 0) >= 1
    assert en.M5_DIAG.get('m5_resolved_disambiguated', 0) >= 1
    print('ok: alt twin + multiline collider demoted, base mod resolved')


def test_alt_twin_demoted_base_resolves_shapers_shape():
    """Shaper's Touch shape: identical-text twin loses to the base mod."""
    en.M5_DIAG.clear()
    base, alt = 'EnergyShieldPerStrengthUnique__1', 'DivergentEnergyShieldPerStrengthUnique__1'
    line = '1% increased Energy Shield per 10 Strength'
    res = _resolve_world(
        mods={base: line, alt: line},
        blocks={"Shaper's Touch":
                "Shaper's Touch\nCrusader Gloves\n" + line + '\n'},
        exact={line: {base, alt}},
        base2class={'Crusader Gloves': 'Gloves'})
    assert _m5_resolved(res, "Shaper's Touch") == {base}
    assert en.M5_DIAG.get('m5_demoted_alt_twin', 0) == 1
    print('ok: alt-quality twin demoted, base mod resolved (Shaper\'s shape)')


def test_multiline_ownership_confirms_and_foreign_claim_demoted():
    """A mod whose OTHER text line also matches the block keeps the line;
    a foreign mod sharing only that line is demoted (no non-first rejection)."""
    en.M5_DIAG.clear()
    own, foreign = 'OwnUnique1', 'ForeignUnique1'
    l1, l2 = 'Line One X', 'Line Two Y'
    res = _resolve_world(
        mods={own: l1 + '\n' + l2, foreign: 'Nothing Here\n' + l2},
        blocks={'Test Ring': 'Test Ring\nRing Base\n' + l1 + '\n' + l2 + '\n'},
        exact={l1: {own}, l2: {own, foreign}},
        base2class={'Ring Base': 'Ring'})
    m5 = _m5(res, 'Test Ring')
    assert m5[own]['status'] == 'resolved'
    assert m5.get(foreign, {}).get('status') != 'resolved'
    assert en.M5_DIAG.get('m5_demoted_multiline', 0) >= 1
    print('ok: cross-line ownership evidence confirms owner, demotes foreign')


def test_genuinely_ambiguous_stays_closed():
    """Same-text family with no demotion signal -> no association, ever."""
    en.M5_DIAG.clear()
    a, b = 'IncreasedCastSpeedUnique__8', 'IncreasedCastSpeedUnique__14'
    line = '(9-15)% increased Cast Speed'
    res = _resolve_world(
        mods={a: line, b: line},
        blocks={'Test Amulet': 'Test Amulet\nAmulet Base\n' + line + '\n'},
        exact={line: {a, b}},
        base2class={'Amulet Base': 'Amulet'})
    assert _m5_resolved(res, 'Test Amulet') == set()
    assert set(_m5(res, 'Test Amulet')) == {a, b}      # candidates stay visible
    assert en.M5_DIAG.get('m5_ambiguous_lines', 0) >= 1
    assert en.M5_DIAG.get('m5_unresolved_candidates', 0) >= 2
    print('ok: genuinely ambiguous line stays fail-closed (counted, no edge)')


def test_alt_only_candidate_resolves_no_overdemotion():
    """No base candidate remains -> the alt candidate is NOT demoted."""
    en.M5_DIAG.clear()
    div = 'DivergentOnlyModUnique__1'
    line = 'Some Rare Line 7'
    res = _resolve_world(
        mods={div: line},
        blocks={'Test Glove': 'Test Glove\nGlove Base\n' + line + '\n'},
        exact={line: {div}},
        base2class={'Glove Base': 'Gloves'})
    assert _m5_resolved(res, 'Test Glove') == {div}
    assert en.M5_DIAG.get('m5_demoted_alt_twin', 0) == 0
    print('ok: alt-only candidate resolves (demotion requires a base candidate)')


def test_exact_singletons_unchanged_and_counters():
    """Rule 1 regression: plain singletons resolve as before, counted exact."""
    en.M5_DIAG.clear()
    solo, other = 'SoloModUnique1', 'DivergentOtherThingUnique__1'
    res = _resolve_world(
        mods={solo: 'Solo Line 10', other: 'Other Thing 5'},
        blocks={'Test Glove':
                'Test Glove\nGlove Base\nSolo Line 10\nOther Thing 5\n'},
        exact={'Solo Line 10': {solo}, 'Other Thing 5': {other}},
        base2class={'Glove Base': 'Gloves'})
    assert _m5_resolved(res, 'Test Glove') == {solo, other}
    assert en.M5_DIAG.get('m5_resolved_exact', 0) == 2
    assert en.M5_DIAG.get('m5_resolved_disambiguated', 0) == 0
    assert en.M5_DIAG.get('m5_demoted_alt_twin', 0) == 0
    assert en.M5_DIAG.get('m5_demoted_multiline', 0) == 0
    print('ok: exact singletons unchanged (m5_resolved_exact counted)')


def test_multiline_singleton_exempt_from_ownership():
    """Eye-of-Malice shape: a SOLE candidate is never ownership-demoted, even
    when its other text lines are helper lines absent from the block."""
    en.M5_DIAG.clear()
    mod = 'NearbyEnemiesIncreasedFireColdResistUnique__1_'
    line = 'Nearby Enemies have 50% increased Fire and Cold Resistances'
    res = _resolve_world(
        mods={mod: '50% increased Fire Resistance\n'
                   '50% increased Cold Resistance\n' + line},
        blocks={'Eye Test': 'Eye Test\nCallous Mask\n' + line + '\n'},
        exact={line: {mod}},
        base2class={'Callous Mask': 'Helmet'})
    assert _m5_resolved(res, 'Eye Test') == {mod}
    assert en.M5_DIAG.get('m5_demoted_multiline', 0) == 0
    print('ok: sole multi-line candidate resolves (ownership only disambiguates)')


def test_multiline_ownership_bracket_tolerant():
    """RePoE [id|display] markers in mod text lines must not break ownership."""
    en.M5_DIAG.clear()
    own, foreign = 'OwnUnique1', 'ForeignUnique1'
    l1, l2 = 'Line One X', 'Helper X'
    res = _resolve_world(
        mods={own: l1 + '\n[Helper|' + l2 + ']',
              foreign: 'Nothing Here\n[Helper|' + l2 + ']'},
        blocks={'Test Ring': 'Test Ring\nRing Base\n' + l1 + '\n' + l2 + '\n'},
        exact={l1: {own}, l2: {own, foreign}},
        base2class={'Ring Base': 'Ring'})
    m5 = _m5(res, 'Test Ring')
    assert m5[own]['status'] == 'resolved'
    assert m5.get(foreign, {}).get('status') != 'resolved'
    print('ok: ownership matching survives [id|display] markers in mod text')


# ------------------------------------------------- live gates (rebuilt KB)

def _payload(uid):
    con = sqlite3.connect(f'file:{ROOT / "cache" / "nodes.db"}?mode=ro', uri=True)
    row = con.execute("SELECT payload FROM nodes WHERE node_id=?", (uid,)).fetchone()
    con.close()
    assert row, uid
    return json.loads(row[0])


def _live_m5_resolved(uid):
    p = _payload(uid)
    return {t['target_key'] for t in p['resolved_targets']
            if t['method'] == 5 and t['status'] == 'resolved'}


def test_live_shapers_touch_six_mods_recovered():
    got = _live_m5_resolved(SHAPERS)
    want = {'AccuracyPerIntelligenceUnique__1', 'LifePerDexterityUnique__1',
            'ManaPerStrengthUnique__1__', 'EnergyShieldPerStrengthUnique__1',
            'EvasionRatingPerIntelligenceUnique__1',
            'MeleePhysicalDamagePerDexterityUnique__1_'}
    assert want <= got, ('missing', want - got)
    assert not any(k.startswith(ALT) for k in got), got
    # the armour line is a genuine same-text family -> must stay closed
    for k in ('LocalIncreasedArmourAndEnergyShieldUnique__16',
              'LocalIncreasedArmourAndEnergyShieldUnique__27',
              'LocalIncreasedArmourAndEnergyShieldUnique__5'):
        assert k not in got, k
    print(f'ok: Shaper\'s Touch {len(got)} m5-resolved (6 mods recovered, '
          'armour line still fail-closed)')


def test_live_crown_all_five_mods_recovered():
    got = _live_m5_resolved(CROWN)
    want = {'LocalIncreasedArmourAndEnergyShieldUnique__19',
            'MaximumLifeManaEnergyShieldUnique__1',
            'TransfigurationOfMindUnique__1',
            'TransfigurationOfBodyUnique__1',
            'TransfigurationOfSoulUnique__1_'}
    assert got == want, got
    assert 'MaximumManaUberMaven' not in got
    assert not any(k.startswith(ALT) for k in got)
    print('ok: Crown of the Inward Eye 5/5 m5-resolved incl. all 3 '
          'Transfigurations; MaximumManaUberMaven excluded')


def test_live_generic_collision_still_absent():
    con = sqlite3.connect(f'file:{ROOT / "cache" / "nodes.db"}?mode=ro', uri=True)
    uid = con.execute(
        "SELECT node_id FROM nodes WHERE type='UniqueItem' AND "
        "json_extract(payload,'$.id')='Stone of Lazhwar'").fetchone()[0]
    con.close()
    got = _live_m5_resolved(uid)
    for k in ('IncreasedCastSpeedUniqueAmulet1', 'IncreasedCastSpeedUnique__11__',
              'IncreasedCastSpeedUnique__14', 'BlockAppliesToSpellsShieldUber2_'):
        assert k not in got, k
    print('ok: Stone of Lazhwar cast-speed family still ambiguous (fail-closed)')


def test_live_whispers_unregressed():
    got = {t['target_key'] for t in _payload(WHISPERS)['resolved_targets']
           if t['method'] in (1, 4, 5) and t['status'] == 'resolved'}
    want = {'AttacksGainMinMaxAddedChaosDamageBasedOnManaUnique__1',
            'PercentReducedMaximumManaUnique_1',
            'ReducedEnergyShieldDelayImplicit1_',
            'SkillsCostEnergyShieldInsteadOfManaLifeUnique__1'}
    assert want <= got, want - got
    print('ok: Whispers of Infinity associations unregressed (4/4)')


def test_live_association_count_no_shrink():
    con = sqlite3.connect(f'file:{ROOT / "cache" / "edges.db"}?mode=ro', uri=True)
    n = con.execute("SELECT COUNT(*) FROM edges WHERE "
                    "relationship_type='unique_modifier_association'").fetchone()[0]
    con.close()
    assert n >= 5004, n          # pre-fix baseline; the fix only adds
    print(f'ok: association edge count {n} >= 5004 baseline')


if __name__ == '__main__':
    fns = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for fn in fns:
        fn()
    print(f'{len(fns)} tests passed')
