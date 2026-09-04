#!/usr/bin/env python3
"""Phase 5D golden tests: semantic candidate discovery.

Run: python3 tools/tests/test_phase5d.py
Assert-based; uses the real cache/ artifacts read-only (plus temp files for
determinism/truncation). Contract 5D.1. No DBs are modified.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import phase5d_candidates as d5

SANTA = Path(__file__).resolve().parents[2]

markers = d5.load_markers()
sem_edges = d5.load_sem_edges()
rev = d5.load_reverse_maps()
rev_grants = d5.load_reverse_grants()
artifact = d5.finalize(d5.discover(markers, sem_edges, rev, rev_grants))
cands = artifact['candidates']
meta = artifact['meta']
by_op = meta['candidates_by_operator']
ALLOWED_HOPS = {'sem_relation_binds', 'modifier_has_tag', 'gem_has_tag',
                'unique_modifier_association', 'modifier_grants_stat',
                'passive_grants_stat', 'gem_grants_stat'}
GRANT_HOPS = {'modifier_grants_stat', 'passive_grants_stat', 'gem_grants_stat'}


def rec(sid, idx, op, node):
    return next(r for r in cands
                if (r['sid'], r['relation_index'], r['operator'],
                    r['candidate_node_id']) == (sid, idx, op, node))


def test_blood_magic_family():
    # to:life must discover life-tagged mods via tag:life anchor
    bm_to_life = [r for r in cands if r['sid'] == 'keystone_blood_magic'
                  and r['operator'] == 'SUBSTITUTE'
                  and any(a['anchor_role'] == 'replacement_resource'
                          and a['node_id'] == 'tag:life' for a in r['anchors'])]
    assert bm_to_life, 'no replacement_resource (life) candidates for Blood Magic'
    assert all(r['candidate_type'] in ('Modifier', 'UniqueItem') for r in bm_to_life)
    # every record reaches at least one path through tag:life; merged records
    # may ALSO carry other anchors' paths (dedup keeps all valid paths)
    assert all(any(h['to'] == 'tag:life' for h in p)
               for r in bm_to_life for p in [next(p for p in r['paths']
                                                if any(a['node_id'] == 'tag:life'
                                                       and a['anchor_role'] == 'replacement_resource'
                                                       for a in r['anchors']))])
    # from:mana role
    bm_from_mana = [r for r in cands if r['sid'] == 'keystone_blood_magic'
                    and any(a['anchor_role'] == 'displaced_resource'
                            and a['node_id'] == 'tag:mana' for a in r['anchors'])]
    assert bm_from_mana, 'no displaced_resource (mana) candidates for Blood Magic'
    print(f"ok: Blood Magic to:life candidates={len(bm_to_life)}, "
          f"from:mana candidates={len(bm_from_mana)}, roles correct")


def test_path_shape_contract():
    # P2/P2g/P3 (tag anchors): sem hop + structural hop; no grants hops
    # P1a (stat anchors): sem hop + ONE grants hop; P1b: single grants hop
    # carrier-carrier (>=2 grants hops) is forbidden everywhere
    for r in cands:
        for p in r['paths']:
            ghops = [h for h in p if h['edge_type'] in GRANT_HOPS]
            assert len(ghops) <= 1, f'carrier-carrier hop: {p}'
            if ghops:  # P1 path
                assert ghops[0]['to'].startswith('stat:'), p
                assert len(p) in (1, 2), f'P1 depth must be 1-2: {p}'
                if len(p) == 2:
                    assert p[0]['edge_type'] == 'sem_relation_binds', p
                    assert p[1]['to'] == p[0]['to'], 'P1a hop must target the bound anchor stat'
            else:
                assert p[0]['edge_type'] == 'sem_relation_binds', p
                assert p[1]['edge_type'] in ('modifier_has_tag', 'gem_has_tag',
                                             'unique_modifier_association'), p
    assert not any(r['candidate_node_id'].startswith(('stat:',)) for r in cands)
    print('ok: path shape contract (P1 <=1 grants hop; no carrier-carrier; tag paths unchanged)')


def test_iron_will_p1b_p1a():
    sc = [r for r in cands if r['sid'] == 'strong_casting']
    p1b_only = [r for r in sc if len(r['anchors']) == 0]
    # P1a: carriers of the two bound anchor stats (9 melee + 339 spell, 1 shared)
    p1a_nodes = {r['candidate_node_id'] for r in sc
                 if any(a['node_id'].startswith('stat:') for a in r['anchors'])}
    assert len(p1a_nodes) == 348, len(p1a_nodes)
    # P1b: exactly the 10 strong_casting carriers, incl. the keystone passive
    p1b_nodes = {r['candidate_node_id'] for r in sc
                 if any(h['edge_type'] in GRANT_HOPS and h['to'] == 'stat:strong_casting'
                        for r2 in [r] for p in r['paths'] for h in p)}
    assert len(p1b_nodes) == 10, len(p1b_nodes)
    assert 'passive:iron_will_keystone2850' in p1b_nodes
    # every P1b candidate has at least one marker-targeting grants path
    assert all(any(h['edge_type'] in GRANT_HOPS and h['to'] == 'stat:strong_casting'
                   for p in r['paths'] for h in p)
               for r in sc if r['candidate_node_id'] in p1b_nodes)
    # SupportIronWill is reached via P1a (spell_damage anchor) AND P1b (marker carrier):
    # both paths retained on one deduped record
    siw = next(r for r in sc if r['candidate_node_id'] == 'gem:SupportIronWill')
    ptypes = {d5._ptype(p) for p in siw['paths']}
    assert ptypes == {'P1a', 'P1b'}, ptypes
    assert any(p[0]['to'] == 'stat:spell_damage_+%' and p[1]['edge_type'] == 'gem_grants_stat'
               for p in siw['paths']), 'P1a path via spell_damage anchor missing'
    # the other 9 carriers are P1b-only (no stat-anchor path)
    assert all({d5._ptype(p) for p in r['paths']} == {'P1b'}
               for r in p1b_only if r['candidate_node_id'] != 'gem:SupportIronWill')
    print(f'ok: Iron Will — P1a=348, P1b=10 carriers (keystone included); '
          f'SupportIronWill carries P1a+P1b paths; 9 carriers P1b-only')


def test_p1_inactive_for_tag_anchors():
    # tag-anchored relations (e.g. Blood Magic) must have zero P1 paths
    for r in cands:
        if r['sid'] == 'keystone_blood_magic':
            for p in r['paths']:
                assert not (p[0]['edge_type'] == 'sem_relation_binds'
                            and p[0]['to'].startswith('stat:')), p
    print('ok: P1 inactive for tag-anchored relations (carrier exclusion preserved)')


def test_suppress_flask_anchor():
    flask = [r for r in cands if r['sid'] == 'cannot_be_affected_by_flasks']
    assert flask, 'no SUPPRESS flask candidates'
    for r in flask:
        for a in r['anchors']:
            assert a['node_id'] == 'tag:flask', a
            assert a['anchor_role'] == 'suppressed_target', a
    print(f"ok: SUPPRESS flask candidates={len(flask)}, all via tag:flask only")


def test_zero_binding_operators():
    # Round B: REDIRECT/DERIVE/COUNT_AS activated via M2b; EQUAL remains silent
    assert by_op.get('EQUAL', 0) == 0
    assert meta['zero_binding_operators'] == ['EQUAL'], meta['zero_binding_operators']
    for op in ('REDIRECT', 'DERIVE', 'COUNT_AS'):
        assert by_op.get(op, 0) > 0, op
    silent_rows = [r for r in artifact['relation_summary'] if r['operator'] == 'EQUAL']
    assert silent_rows and all(r['candidates'] == 0 for r in silent_rows)
    print(f"ok: EQUAL silent ({len(silent_rows)} instances); "
          f"REDIRECT/DERIVE/COUNT_AS activated ({by_op.get('REDIRECT',0)}/"
          f"{by_op.get('DERIVE',0)}/{by_op.get('COUNT_AS',0)})")


def test_forbidden_traversal_absent():
    for r in cands:
        for p in r['paths']:
            assert len(p) <= 3, f'path too deep: {p}'
            for h in p:
                assert h['edge_type'] in ALLOWED_HOPS, h
            assert 'modifier_in_group' not in {h['edge_type'] for h in p}
            assert 'stat_scales_with' not in {h['edge_type'] for h in p}
    print('ok: no forbidden hops; max depth 3 (P3)')


def test_p3_status_preserved():
    p3 = [r for r in cands if r['candidate_type'] == 'UniqueItem']
    assert p3, 'no P3 unique candidates'
    for r in p3[:200]:
        hop = r['paths'][0][1]
        assert hop['edge_type'] == 'unique_modifier_association'
        assert hop['direction'] == 'reverse'
        assert hop['status'] == 'resolved_not_validated', hop
    print(f"ok: P3 uniques={len(p3)}, unique_modifier_association hop + "
          f"resolved_not_validated status preserved")


def test_dedup_identity():
    ids = [(r['sid'], r['relation_index'], r['operator'], r['candidate_node_id'])
           for r in cands]
    assert len(ids) == len(set(ids)), 'duplicate candidate identities'
    multi = [r for r in cands if len(r['paths']) > 1]
    assert multi, 'expected at least one multi-path merged record'
    for r in multi:
        assert len({d5.js(p) for p in r['paths']}) == len(r['paths'])
        ps = [d5.js(p) for p in r['paths']]
        assert ps == sorted(ps), 'paths must be deterministically sorted'
    # cross-relation duplication is kept: same node under >=2 relations
    per_node = {}
    for r in cands:
        per_node.setdefault(r['candidate_node_id'], set()).add(
            (r['sid'], r['relation_index']))
    dup = {n: rels for n, rels in per_node.items() if len(rels) > 1}
    assert dup, 'expected same node as candidate of multiple relations'
    print(f'ok: identities unique; {len(multi)} multi-path merges; '
          f'{len(dup)} nodes legitimately shared across relations')


def test_determinism(tmp_root=None):
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        a1 = d5.finalize(d5.discover(markers, sem_edges, rev))
        p1 = Path(td) / 'a1.json'
        d5.write_artifact(a1, p1)
        a2 = d5.finalize(d5.discover(markers, sem_edges, rev))
        p2 = Path(td) / 'a2.json'
        d5.write_artifact(a2, p2)
        h1, h2 = p1.read_bytes(), p2.read_bytes()
        assert h1 == h2, 'two runs must be byte-identical'
        assert a1['meta']['sha256'] == a2['meta']['sha256']
    print(f"ok: determinism — identical sha256 {a1['meta']['sha256'][:16]}…")


def test_truncation_explicit():
    # real run: the tag:damage anchor exceeds the cap and is loudly truncated
    real = meta['truncated_anchors']
    assert any(t['anchor'] == 'tag:damage' and t['kept'] == 5000 and t['known_total'] > 5000
               for t in real), real
    a = d5.finalize(d5.discover(markers, sem_edges, rev, rev_grants, cap=5))
    t = a['meta']['truncated_anchors']
    assert t, 'cap=5 must produce explicit truncation records'
    for r in t:
        assert r['kept'] == 5 and r['known_total'] > 5, r
        assert {'sid', 'relation_index', 'operator', 'field', 'anchor',
                'kept', 'known_total'} <= set(r)
    assert a['meta']['candidates_deduped'] < meta['candidates_deduped']
    print(f"ok: truncation explicit under low cap ({len(t)} anchors truncated, "
          f"known_total recorded)")


def test_provenance_traceback():
    # candidate -> path -> sem_relation_binds triple exists in 5S edges
    sem_triples = {(e['src'], e['tgt']) for e in sem_edges}
    import random
    sample = random.Random(0).sample(cands, 25)
    for r in sample:
        for p in r['paths']:
            if len(p) == 1:  # P1b: discovery starts at the marker stat itself
                assert p[0]['edge_type'] in GRANT_HOPS and p[0]['to'] == 'stat:' + r['sid'], p
            else:
                assert (p[0]['from'], p[0]['to']) in sem_triples, p
        assert r['status'] == 'discovered'
        assert r['relation_fields'], 'frozen 4M relation_fields must be verbatim'
    # 4M text trace: relation_fields keys exist in the marker's relation
    mk = {m['sid']: m for m in markers}
    for r in sample[:10]:
        rel = mk[r['sid']]['relations'][r['relation_index']]
        assert rel['fields'] == r['relation_fields']
        if 'classification_uncertainty' in rel:
            assert r['classification_uncertainty'] == rel['classification_uncertainty']
    print('ok: provenance trace candidate→path→sem edge→4M relation intact (25 sampled)')


if __name__ == '__main__':
    print(f"meta: {json.dumps({k: v for k, v in meta.items() if k != 'truncated_anchors'})[:300]}")
    test_blood_magic_family()
    test_path_shape_contract()
    test_iron_will_p1b_p1a()
    test_p1_inactive_for_tag_anchors()
    test_suppress_flask_anchor()
    test_zero_binding_operators()
    test_forbidden_traversal_absent()
    test_p3_status_preserved()
    test_dedup_identity()
    test_determinism()
    test_truncation_explicit()
    test_provenance_traceback()
    print('ALL PASS')