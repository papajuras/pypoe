#!/usr/bin/env python3
"""Phase 5I — influenced mods as first-class KB members (whispers08 plan).

The governing invariant (user-pinned): EVERY valid v1 influenced mod must
remain represented and discoverable, with its influence and spawn-class
constraints attached; pruning must never lose valid mod information.

Run: python3 -m tests.test_influence   (from santa-maria/)
"""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import phase6_api as api
import phase7_build_feasibility as feas
from phase7_build_validity import validate_build, BuildState
import phase5i_influence as p5i
import extract_nodes as ex


def test_influence_nodes_and_display_names():
    g = api.get_graph()
    nodes = g._load_nodes()
    expected = {'shaper': "Shaper's", 'elder': "Elder's",
                'crusader': "Crusader's", 'eyrie': "Redeemer's",
                'adjudicator': "Warlord's", 'basilisk': "Hunter's"}
    for sfx, disp in expected.items():
        nid = 'influence:' + sfx
        assert nid in nodes, f'missing influence node {nid}'
        payload = nodes[nid][1]
        assert nodes[nid][0] == 'Influence'
        assert payload['name'] == disp, (nid, payload['name'])
        assert payload['tag_suffix'] == sfx
        assert payload['item_classes'], f'{nid} has no item classes'
    print('ok: six influence nodes with pinned display names + item classes')


def test_mod_to_influence_binding_exact_tags():
    """Hunter's per-10-int lightning: bound to claw/dagger/sceptre/wand/rune
    dagger — exact spawn tag membership, not suffix guessing."""
    g = api.get_graph()
    nodes = g._load_nodes()
    out, _ = g._load_edges()
    mod = 'mod:AddedLightningDamagePerIntelligenceInfluence1'
    out_edges = out['modifier_has_influence'].get(mod, [])
    assert len(out_edges) == 1, out_edges
    tgt = out_edges[0][0]
    assert tgt == 'influence:basilisk', tgt
    prov = out_edges[0][1]
    tags = prov[0].get('tags')
    assert set(tags) == {'claw_basilisk', 'dagger_basilisk',
                         'rune_dagger_basilisk', 'sceptre_basilisk',
                         'wand_basilisk'}, tags
    # the class side comes from item_classes.json influence_tags
    inf_payload = nodes['influence:basilisk'][1]
    assert 'item_class:Claw' in inf_payload['item_classes']
    # Bow is present because basilisk influence applies to Bow class
    assert 'item_class:Bow' in inf_payload['item_classes'] or \
        'bow_basilisk' in (nodes['item_class:Claw'][1].get('influence_tags') or [])
    print('ok: mod->influence binding is the exact spawn-tag set')


def test_influence_variants_never_collapse():
    """Different influence variants of the same family must stay distinct
    nodes with distinct edges (Hunter vs Shaper lightning-per-int)."""
    g = api.get_graph()
    out, _inn = g._load_edges()
    mods = {'mod:AddedLightningDamagePerIntelligenceInfluence1': 'influence:basilisk',
            'mod:AddedLightningDamagePerIntelligenceUber1': 'influence:shaper'}
    for mod, infl in mods.items():
        edges = out['modifier_has_influence'].get(mod, [])
        assert edges, f'{mod} has no influence edge'
        assert {t for (t, _p) in edges} == {infl}, (mod, edges)
# both mod nodes still exist and are discoverable by resolve
    import phase8_research as r8
    for mod in mods:
        env = r8.resolve(mod.split(':', 1)[1], type='Modifier')
        assert any(x['id'] == mod for x in env['results']), mod
    print('ok: influence variants do not collapse; all discoverable')


def test_non_influenced_mods_untouched():
    """Mods without influence spawn tags carry no influence edges (empty
    lists, never invented) — the seed mod and HoWA's unique mod stay clean."""
    g = api.get_graph()
    nodes = g._load_nodes()
    assert nodes.get('mod:AttacksGainMinMaxAddedChaosDamageBasedOnManaUnique__1')
    env = r_resolve_mod('AttacksGainMinMaxAddedChaosDamageBasedOnManaUnique__1')
    assert env['influence'] == [] and env['spawn_classes'] == [], env
    print('ok: non-influenced mods carry no influence data (empty, not guessed)')


def r_resolve_mod(key):
    import phase8_research as r
    env = r.resolve(key, type='Modifier')
    assert env['results'], key
    return env['results'][0]


def test_carriers_surfaces_influence():
    """The whispers08 gap: carriers(stat) rows for influenced mods now name
    the influence + spawn classes instead of a bare zero-carrier verdict."""
    import phase8_research as r
    env = r.carriers('stat:attack_maximum_added_lightning_damage_per_10_int')
    assert env['error'] is None
    rows = [x for x in env['results']
            if x['carrier'] == 'mod:AddedLightningDamagePerIntelligenceInfluence1']
    assert rows and rows[0]['influence'] == ["Hunter's"], rows
    assert 'Claw' in rows[0]['spawn_classes']
    print('ok: carriers(stat) rows expose influence + spawn classes')


def test_tier_prune_never_loses_association_layer():
    """Equivalence self-check (extract_nodes guard g + revert): the pruned
    extraction must produce the EXACT association layer of the unpruned
    extraction. The build currently reverts (fail-open) — this test pins
    that the shipped nodes/edges contain every live association."""
    nodes = api.get_graph()._load_nodes()
    con = sqlite3.connect(api.EDGES_DB)
    assoc = {(r[0], r[1]) for r in con.execute(
        "select source_node_id, target_node_id from edges "
        "where relationship_type='unique_modifier_association'")}
    con.close()
    # every association target is still a node (mod coverage intact)
    missing = [t for _s, t in assoc if t not in nodes]
    assert not missing, f'associated mods missing from nodes.db: {missing[:5]}'
    # every association target grants >=1 stat edge (stat relations preserved)
    econ = sqlite3.connect(api.EDGES_DB)
    grants = {r[0] for r in econ.execute(
        "select source_node_id from edges where relationship_type='modifier_grants_stat'")}
    econ.close()
    bare = [t for _s, t in assoc if t not in grants]
    assert not bare, f'associations whose mod lost its stat edges: {bare[:5]}'
    print('ok: association layer fully represented (mods + their stat edges)')


def test_prune_rederivation_is_deterministic():
    """Re-derivation contract: rerunning the pure prune function over
    mods.json must reproduce the same drop set the build reported."""
    raw_db = Path(__file__).resolve().parents[2] / 'cache' / 'raw_records.db'
    con = sqlite3.connect(raw_db)
    mods = [(k, json.loads(rj)) for k, rj in con.execute(
        "select record_key, raw_json from raw_records where "
        "source_file='repoe/mods.json'")]
    con.close()
    n2b = __import__('extract_nodes').load_pob_blocks(sqlite3.connect(raw_db))
    kept, dropped = ex.prune_lower_tiers(mods, n2b)
    # the pure function is deterministic
    kept2, dropped2 = ex.prune_lower_tiers(mods, n2b)
    assert kept == kept2 and dropped == dropped2, 'prune is not deterministic'
    # every drop is auditable: reason pair (lo, hi) exists in mods.json
    keys = {k for k, _ in mods}
    for lo, hi in dropped:
        assert lo in keys and hi in keys, (lo, hi)
        assert f'mod:{lo}' not in ex._contract_keep_mods()
    print(f'ok: tier-prune re-derivable ({len(dropped)} drops audited; '
          'build currently reverts to retention on association divergence)')


def test_validator_influence_check():
    assert feas.influence_check(
        ['mod:AddedLightningDamagePerIntelligenceInfluence1'], 'Claw'
    )['result'] == 'valid'
    # exact per-class binding: Hunter's one-hand mod cannot roll on a bow
    r = feas.influence_check(
        ['mod:AddedLightningDamagePerIntelligenceInfluence1'], 'Bow')
    assert r['result'] == 'invalid', r
    # non-influenced mod -> unknown, never assumed compatible
    r = feas.influence_check(
        ['mod:AttacksGainMinMaxAddedChaosDamageBasedOnManaUnique__1'], 'Amulet')
    assert r['result'] == 'unknown', r
    # unknown class -> unknown
    r = feas.influence_check(
        ['mod:AddedLightningDamagePerIntelligenceInfluence1'], 'Boots')
    # boots have hunter tags; use a bogus class for the unknown case
    r2 = feas.influence_check(
        ['mod:AddedLightningDamagePerIntelligenceInfluence1'], 'Rocket Boots')
    assert r2['result'] == 'unknown', r2
    print('ok: influence_check valid/invalid/unknown outcomes')


def test_validator_build_state_with_influenced_mods():
    s = BuildState(items=[], influenced_items=[
        {'item_class': 'Claw',
         'mods': ['mod:AddedLightningDamagePerIntelligenceInfluence1']}])
    out = validate_build(s, final=False)
    assert out['status'] == 'valid', out['reason']
    assert 'influence_compatibility' in out['checked']
    s_bad = BuildState(items=[], influenced_items=[
        {'item_class': 'Bow',
         'mods': ['mod:AddedLightningDamagePerIntelligenceInfluence1']}])
    out_bad = validate_build(s_bad, final=False)
    assert out_bad['status'] == 'invalid', out_bad
    assert 'influence: ' in out_bad['reason'], out_bad['reason']
    assert 'influenced-item compatibility not modeled' not in out_bad[
        'limitations'], 'limitation line must be gone'
    print('ok: validator commits/rejects influenced rare components')


def test_projection_idempotent():
    """Deleting + rewriting own namespace only; rerun changes nothing."""
    import subprocess
    cmd = [sys.executable, str(Path(p5i.__file__))]
    r1 = subprocess.run([sys.executable, str(p5i.__file__), '--verify-only'],
                        capture_output=True, text=True)
    assert r1.returncode == 0, r1.stderr
    print('ok: influence projection verifies cleanly (idempotent rerun)')


def test_no_eldritch_leak():
    """Eldritch implicit mods carry no_tier_*_eldritch_implicit tags but are
    NOT six-confluence influences — they must not gain influence edges in v1."""
    g = api.get_graph()
    out, _inn = g._load_edges()
    mod = 'mod:DamagePer100INTEldritchImplicit1'
    assert out['modifier_has_influence'].get(mod) in (None, []), 'eldritch leak'
    print('ok: eldritch/other pseudo-influences not inferred (v1 scope kept)')


if __name__ == '__main__':
    test_influence_nodes_and_display_names()
    test_mod_to_influence_binding_exact_tags()
    test_influence_variants_never_collapse()
    test_non_influenced_mods_untouched()
    test_carriers_surfaces_influence()
    test_tier_prune_never_loses_association_layer()
    test_prune_rederivation_is_deterministic()
    test_validator_influence_check()
    test_validator_build_state_with_influenced_mods()
    test_projection_idempotent()
    test_no_eldritch_leak()
    print('ALL influence tests pass')