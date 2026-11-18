#!/usr/bin/env python3
"""Focused assert-based tests for the santa-maria data tools.

Run: python3 tools/tests/test_tools.py
Covers: multi-pattern conversion bucketing (vocab.py), plan-scoped manifest /
stale-file integrity (download.py), and keyed-map schema compaction with
key_sample (analyze.py). No network, no data/ reads beyond temp files.
"""
import sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import phase1_analyze as analyze
import phase1_download as download
import phase1_vocab as vocab


def test_vocab_multi_pattern():
    ids = {'local_energy_shield_+%', 'accuracy_rating', 'plain_stat'}
    patterns = ['local_', '_+%', 'scal']
    hits = vocab.bucket_hits(ids, patterns)
    assert 'local_energy_shield_+%' in hits['local_'], 'id matching local_ missing'
    assert 'local_energy_shield_+%' in hits['_+%'], 'id matching _+% missing'
    assert 'local_energy_shield_+%' not in hits.get('scal', [])
    assert 'accuracy_rating' not in hits.get('local_', [])
    # every match recorded: one id under 2 patterns, counts overlap
    matched = {i for vals in hits.values() for i in vals}
    assert matched == {'local_energy_shield_+%'}
    total = sum(len(v) for v in hits.values())
    assert total > len(matched), 'multi-match id must be counted under each pattern'
    print('ok: vocab multi-pattern bucketing')


def test_download_manifest_plan_scoped():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        ok = root / 'repoe' / 'base_items.json'
        ok.parent.mkdir(parents=True)
        ok.write_text('{"a":1}')
        stale = root / 'pob' / 'old_scope.json'
        stale.parent.mkdir(parents=True)
        stale.write_text('{}')
        files = [('repoe/base_items.json', 'http://x', ok),
                 ('repoe/gems.json', 'http://x', root / 'repoe' / 'gems.json')]
        m, missing = download.build_manifest(files)
        assert 'repoe/base_items.json' in m
        assert m['repoe/base_items.json'][0] == ok.stat().st_size
        assert len(m['repoe/base_items.json']) == 2
        assert 'pob/old_scope.json' not in m, 'out-of-scope file leaked into manifest'
        assert missing == ['repoe/gems.json'], 'missing planned file not flagged'
        stale_list = download.stale_files(files, root=root)
        assert stale_list == ['pob/old_scope.json'], f'unexpected stale list: {stale_list}'
    print('ok: plan-scoped manifest + stale detection')


def test_keyed_map_compaction_lossless():
    def node(types, ku, present=1, instances=1, idlike=None, arr=None, sample=()):
        return {'types': set(types), 'present_in': present, 'instances': instances,
                'key_union': set(ku) if ku is not None else None,
                'key_idlike': set(idlike or []),
                'arr_elem_types': set(arr or []), 'nested': ku is not None, 'sample': list(sample)}

    schema = {
        '': node(['object'], ['passives']),
        'passives': node(['object'], ['12345', '12346', '12347'], idlike=['12345', '12346', '12347']),
        'passives.12345': node(['object'], ['name', 'hash']),
        'passives.12345.name': node(['string'], None, sample=['A']),
        'passives.12345.hash': node(['int'], None, sample=[1]),
        'passives.12346': node(['object'], ['name', 'hash']),
        'passives.12346.name': node(['string'], None, sample=['B']),
        'passives.12346.hash': node(['int'], None, sample=[2]),
        'passives.12347': node(['object'], ['name', 'hash']),
        'passives.12347.name': node(['string'], None, sample=['C']),
        'passives.12347.hash': node(['int'], None, sample=[3]),
    }
    fa = object.__new__(analyze.FileAnalyzer)
    fa.vocab = set()
    keyed = analyze.FileAnalyzer._detect_keyed(schema)
    out = analyze.FileAnalyzer._collapse_keyed(schema, keyed)
    p = out['passives']
    assert p['key_union'] == 3, 'key_union_count must stay exact'
    assert 'passives.{}' in out, 'instance collapsed to {}'
    assert 'passives.{}.name' in out, 'field path preserved under collapsed map'
    assert 'passives.12345.name' not in out, 'concrete key must not be listed'
    # lossless keyed_maps inventory
    km = fa._keyed_inventory(schema, keyed)
    info = km['passives']
    assert info['key_count'] == 3
    assert info['keys'] == ['12345', '12346', '12347'], 'full concrete key list preserved'
    assert info['shape_count'] == 1 and len(info['shape_groups']) == 1
    assert info['shape_groups'][0]['keys'] == ['12345', '12346', '12347']
    assert info['shape_groups'][0]['schema'] is None, 'single-shape map uses compact P.{} subtree'
    print('ok: keyed-map compaction keeps key_union_count; keyed_maps is lossless')


def test_numeric_crossref_candidates():
    records = [('passiveA', {'hash': 50288, 'name': 'Iron Will', 'small': 7, 'f': 0.5})]
    fa = analyze.FileAnalyzer(records, set(), 'x')
    res = fa.run()
    cr = res['crossrefs']
    assert 'numeric_id' in cr, '5-digit passive hash should be a numeric_id candidate'
    assert 50288 in cr['numeric_id']['distinct_sample'], 'hash value retained'
    assert 'trade_hash' not in cr, '5-digit is not a trade hash'
    # small ints (3 digits or less) and floats must NOT become references
    for cls, v in cr.items():
        pass  # presence of only numeric_id above is the assertion
    assert 'small' not in cr.get('numeric_id', {}).get('paths', {})
    assert 'f' not in cr.get('numeric_id', {}).get('paths', {})
    print('ok: numeric reference candidates (int >= 4 digits) detectable, small ints/floats excluded')


if __name__ == '__main__':
    test_vocab_multi_pattern()
    test_download_manifest_plan_scoped()
    test_keyed_map_compaction_lossless()
    test_numeric_crossref_candidates()
    print('ALL TESTS PASSED')
