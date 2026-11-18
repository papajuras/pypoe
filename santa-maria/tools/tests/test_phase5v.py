#!/usr/bin/env python3
"""Phase 5V golden tests: semantic candidate validation.

Run: python3 tools/tests/test_phase5v.py
Assert-based; read-only against the real cache/ artifacts. Contract 5V.1.
Three-tier result model; V2 vocabulary audited+frozen; SUPPRESS V1-only.
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import phase5v_validate as v5

SANTA = Path(__file__).resolve().parents[2]

cand = v5.load_candidates()
payloads = v5.load_payloads()
grant_map = v5.load_grant_map()
uma_map = v5.load_uma_map()
artifact = v5.validate(cand, payloads, grant_map, uma_map)
results = artifact['results']
meta = artifact['meta']


def find(sid, idx, op, node):
    return next((r for r in results
                 if (r['sid'], r['relation_index'], r['operator'],
                     r['candidate_node_id']) == (sid, idx, op, node)), None)


def test_three_tier_model():
    assert set(meta['by_operator_rule']) and all(
        r['result'] in ('validated', 'validated_family') for r in results)
    assert v5.RESULT_CONTRADICTED not in {r['result'] for r in results}, \
        'contradicted reserved, never emitted'
    assert meta['candidates_validated'] == sum(
        1 for r in results if r['result'] == 'validated')
    print(f"ok: tiers — validated={meta['candidates_validated']} "
          f"family={meta['candidates_validated_family']} "
          f"insufficient(summarized)={meta['insufficient_evidence_total']}")


def test_v1_direct_evidence():
    # real gold: this mod grants the marker stat of its own relation
    r = find('curse_skills_cost_life_instead_of_mana', 0, 'SUBSTITUTE',
             'mod:CurseSkillsCostAndReserveLifeUnique__1')
    assert r and r['result'] == 'validated' and r['rule_id'] == 'V1', r
    assert r['evidence_stat_ids'] == ['stat:curse_skills_cost_life_instead_of_mana']
    assert r['status_cap'] is None
    print('ok: V1 direct grant evidence (curse-cost-life mod validated)')


def test_v2_substitute_direction_gate():
    # family: regenerate_energy_shield_instead_of_life validates for to=ES,from=life
    es = [r for r in results if r['rule_id'] == 'V2-SUBSTITUTE'
          and any('regenerate_energy_shield_instead_of_life' in s
                  for s in r['evidence_stat_ids'])]
    assert es, 'expected ES-instead-of-life family validations'
    # direction gate: mana...instead_of...life sid must NOT validate any
    # to=life/from=mana relation (life appears AFTER the indicator)
    wrong = [r for r in results if r['rule_id'] == 'V2-SUBSTITUTE'
             and any('mana_instead_of_life' in s for s in r['evidence_stat_ids'])]
    assert not wrong, f'direction gate failed: {wrong[:2]}'
    print(f'ok: V2-SUBSTITUTE direction gate ({len(es)} ES-family hits; '
          f'reversed sids rejected)')


def test_v2_convert_pool_exact():
    conv = [r for r in results if r['rule_id'] == 'V2-CONVERT']
    assert conv, 'expected pool-exact convert validations'
    for r in conv:
        pools = [a['node_id'].split(':', 1)[1].replace('_damage', '')
                 for a in r['anchors'] if a['field'].startswith('pool')]
        for s in r['evidence_stat_ids']:
            assert all(p in s for p in pools), (r['sid'], s, pools)
            assert 'to_convert_to' in s or 'added_as' in s, s
    # the measured FP: convert-to-cold evidence must not validate the chaos relation
    chaos = [r for r in conv if r['sid'] == 'base_physical_damage_%_to_convert_to_chaos_per_level']
    assert chaos and not any('cold' in s for r in chaos for s in r['evidence_stat_ids'])
    print(f'ok: V2-CONVERT pool-exact ({len(conv)}; cross-pool FPs rejected)')


def test_suppress_v1_only():
    assert not any(r['operator'] == 'SUPPRESS' and r['rule_id'] != 'V1'
                   for r in results), 'SUPPRESS must be V1-only'
    # measured subject-mismatch FPs stay insufficient
    for mod in ('mod:FlaskStunImmunityUnique__1',
                'mod:JunMaster2LocalFlaskReducedReflectDuringEffect'):
        r = [x for x in results if x['candidate_node_id'] == mod
             and x['operator'] == 'SUPPRESS']
        assert not r, f'{mod} must not be validated (subject mismatch)'
    sup = [r for r in results if r['operator'] == 'SUPPRESS']
    assert all(r['result'] == 'validated' for r in sup)
    print(f'ok: SUPPRESS V1-only ({len(sup)} validated; no morphology rule)')


def test_silent_operators_zero():
    # Round B: REDIRECT/DERIVE/COUNT_AS activated via M2b; EQUAL stays silent
    assert not any(r['operator'] == 'EQUAL' for r in results)
    for op in ('REDIRECT', 'DERIVE', 'COUNT_AS'):
        assert any(r['operator'] == op for r in results), op
    print('ok: EQUAL zero results; REDIRECT/DERIVE/COUNT_AS activated via V1')


def test_unique_composition_cap():
    un = [r for r in results if r['candidate_type'] == 'UniqueItem']
    for r in un:
        assert r['status_cap'] == 'resolved_not_validated', r
        assert 'unique_modifier_association' in r['evidence_source'], r
    # no evidence ever cites a tag/membership edge
    for r in results:
        assert r['evidence_stat_ids'], 'every result must cite granted stat ids'
        assert all(s.startswith('stat:') for s in r['evidence_stat_ids'])
    print(f'ok: unique composition ({len(un)}) capped resolved_not_validated; '
          f'evidence always stat-grants')


def test_uncertainty_carried():
    # Round B semantics: an uncertain-operator relation (e.g. redirect-vs-substitute)
    # may be validated ONLY via V1 direct carrier evidence — the carrier fact is
    # certain even when the operator label is not. Uncertainty is copied verbatim.
    unc_sids = {r['sid'] for r in v5.load_candidates()['candidates']
                if r.get('classification_uncertainty')}
    assert 'bleeding_damage_on_self_converted_to_chaos' in unc_sids
    for r in results:
        if r['sid'] in unc_sids:
            assert r['rule_id'] == 'V1' and r['result'] == 'validated', r
            assert r['classification_uncertainty'], 'uncertainty must be carried verbatim'
    n = sum(1 for r in results if r['sid'] in unc_sids)
    # the bleeding relation (SUBSTITUTE uncertainty) has no carrier-candidates: no results
    assert not any(r['sid'] == 'bleeding_damage_on_self_converted_to_chaos' for r in results)
    print(f'ok: uncertain relations validate only via V1 ({n} direct-evidence results; '
          f'uncertainty verbatim; no family claims)')


def test_determinism():
    with tempfile.TemporaryDirectory() as td:
        a1 = v5.validate(cand, payloads, grant_map, uma_map)
        p1 = Path(td) / 'v1.json'
        v5.write_artifact(a1, p1)
        a2 = v5.validate(cand, payloads, grant_map, uma_map)
        p2 = Path(td) / 'v2.json'
        v5.write_artifact(a2, p2)
        assert p1.read_bytes() == p2.read_bytes()
        assert a1['meta']['sha256'] == a2['meta']['sha256']
    print(f"ok: determinism — identical sha256 {a1['meta']['sha256'][:16]}…")


def test_traceback():
    # result -> 5D path -> 5S sem edge -> 4M relation fields (verbatim)
    d5 = json.loads((SANTA / 'cache' / 'sem_candidates.json').read_text())
    d5_ids = {(r['sid'], r['relation_index'], r['operator'], r['candidate_node_id']): r
              for r in d5['candidates']}
    mk = {m['sid']: m for m in json.loads(
        (SANTA / 'cache' / 'semantic_markers.json').read_text())['markers']}
    import sqlite3
    con = sqlite3.connect(f"file:{SANTA / 'cache' / 'edges.db'}?mode=ro", uri=True)
    sem_triples = {(s, t) for s, t in con.execute(
        "SELECT source_node_id, target_node_id FROM edges "
        "WHERE relationship_type='sem_relation_binds'")}
    grant_tails = {(b, a) for a, b in con.execute(
        "SELECT source_node_id, target_node_id FROM edges "
        "WHERE relationship_type IN ('modifier_grants_stat','passive_grants_stat','gem_grants_stat')")}
    con.close()
    import random
    for r in random.Random(0).sample(results, min(25, len(results))):
        src5d = d5_ids[(r['sid'], r['relation_index'], r['operator'],
                        r['candidate_node_id'])]
        assert r['paths'] == src5d['paths'], '5D path must be copied verbatim'
        assert r['relation_fields'] == mk[r['sid']]['relations'][r['relation_index']]['fields']
        for p in r['paths']:
            if len(p) == 1:  # P1b: marker-stat discovery, validated via grant tail
                assert (p[0]['to'], p[0]['from']) in grant_tails, p
            else:
                assert (p[0]['from'], p[0]['to']) in sem_triples, p
    print('ok: traceability candidate→path→sem bind/marker→4M fields (25 sampled)')


if __name__ == '__main__':
    print(f"meta: {json.dumps(meta)[:260]}")
    test_three_tier_model()
    test_v1_direct_evidence()
    test_v2_substitute_direction_gate()
    test_v2_convert_pool_exact()
    test_suppress_v1_only()
    test_unique_composition_cap()
    test_silent_operators_zero()
    test_uncertainty_carried()
    test_determinism()
    test_traceback()
    print('ALL PASS')