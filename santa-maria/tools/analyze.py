#!/usr/bin/env python3
"""Exhaustive per-file analysis of every downloaded JSON file.

Input:  santa-maria/data/  (produced by tools/download.py)
Output: santa-maria/cache/analysis.json, cache/stat_conversion_context.json

Every file is scanned in full: ALL records, ALL fields, ALL nested objects,
ALL array elements, ALL string AND numeric values. No record/field/array/
depth sampling.

The per-file `schema` is a STRUCTURALLY COMPACTED view: per-instance keyed
maps (e.g. `passives.<hash>`) are rendered as a `{}` placeholder. The
companion `keyed_maps` structure in analysis.json is LOSSLESS with respect to
the observed schema: for every keyed map it preserves the exact set of
concrete keys, the number of distinct child shapes, and (when shapes differ)
a representative child schema per shape group. Raw JSON in data/ stays
authoritative.

Cross-reference and conversion/scaling scans are exhaustive over string AND
numeric values; display samples are capped, counts are exact. A companion
`stat_conversion_context.json` makes every stat-id conversion/scaling match's
source context recoverable without re-scanning the raw files.
"""
import bisect, json, os
from pathlib import Path

from common import SCAN_PATTERNS, REF_CLASSES, KEY_CLASSES, KEYED_MIN_KEYS, KEYED_MAX_FIELDS, KEYED_RATIO

SANTA = Path(__file__).resolve().parents[1]
ROOT = SANTA / 'data'
CACHE = SANTA / 'cache'
ANALYSIS_CACHE = CACHE / 'analysis.json'
STAT_CTX_CACHE = CACHE / 'stat_conversion_context.json'
VOCAB_CACHE = CACHE / 'stat_vocab.json'
META_KEY = '_meta'

SAMPLE_CAP = 5        # schema/cref sample rows stored per path (display only)
DISTINCT_CAP = 200    # distinct values stored per class/context (count stays exact)
KEY_SAMPLE_CAP = 10   # concrete keys kept per keyed-map node (report preview only)


def json_type(v):
    if isinstance(v, bool): return 'bool'
    if isinstance(v, int): return 'int'
    if isinstance(v, float): return 'float'
    if isinstance(v, str): return 'string'
    if isinstance(v, list): return 'array'
    if isinstance(v, dict): return 'object'
    return 'null'


def classify(data):
    """Return (shape, records, record_count, semantics). records = list of
    (record_key_or_None, value) pairs covering 100% of the file."""
    if isinstance(data, list):
        elem = sorted(set(json_type(x) for x in data))
        if elem and all(t not in ('object', 'array') for t in elem):
            shape = 'list<' + '/'.join(elem) + '>'
        else:
            shape = 'list'
        return shape, list(enumerate(data)), len(data), \
            'top-level list → record_count = number of list elements'
    if isinstance(data, dict):
        vals = list(data.values())
        val_types = {json_type(v) for v in vals}
        if vals and all(t in ('object', 'array') for t in val_types) and len(data) >= 8:
            return 'dict', list(data.items()), len(data), \
                f'top-level dict keyed by record id → record_count = number of top-level keys ({len(data)})'
        if vals and all(t in ('string', 'int', 'float', 'bool') for t in val_types):
            return 'dict<scalar>', list(data.items()), len(data), \
                'top-level dict of scalar values → each key/value pair is a record'
        return 'dict', [(None, data)], 1, \
            'top-level dict is a single record object (nested maps shown as keyed `{}`)'
    return 'scalar', [(None, data)], 1, 'scalar top-level → single value, not a record collection'


class FileAnalyzer:
    def __init__(self, records, vocab, relpath):
        self.records = records
        self.vocab = vocab
        self.relpath = relpath
        self.schema = {}          # path -> {types:set, present_in:int, instances:int, key_union:set|None, key_idlike:set, arr_elem_types:set, nested:bool, sample:list}
        self.crossrefs = {}       # class -> {field_occurrences, records:set, distinct:set, sample:list, paths:{path:{occurrences, distinct:set, sample:list}}}
        self.conversion = {}      # pattern -> {field_occurrences, record_occurrences, unique:set, sample:list, ctx:{path:{kind:{occurrences, values:set}}}}
        self.stat_ctx = {}        # stat_id -> {path: {kind: {pattern: count}}}  (companion source)
        self.max_depth = 0

    # ---- cross-reference helpers ----
    def _cref(self, cls, path, value, ridx, rkey, cref_rec):
        c = self.crossrefs.get(cls)
        if c is None:
            c = self.crossrefs[cls] = {'field_occurrences': 0, 'records': set(),
                                       'distinct': set(), 'sample': [], 'paths': {}}
        c['field_occurrences'] += 1
        if cls not in cref_rec:
            cref_rec.add(cls)
            c['records'].add(ridx)
        c['distinct'].add(value)
        if len(c['sample']) < SAMPLE_CAP:
            c['sample'].append([rkey, path, value])
        p = c['paths'].get(path)
        if p is None:
            p = c['paths'][path] = {'occurrences': 0, 'distinct': set(), 'sample': []}
        p['occurrences'] += 1
        p['distinct'].add(value)
        if len(p['sample']) < SAMPLE_CAP:
            p['sample'].append([rkey, value])

    def _cref_value(self, v, path, ridx, rkey, cref_rec):
        for cls, (_desc, pred) in REF_CLASSES.items():
            if pred(v, self.vocab):
                self._cref(cls, path, v, ridx, rkey, cref_rec)

    def _cref_int(self, v, path, ridx, rkey, cref_rec):
        """Numeric reference candidates: integers with >= 4 digits. Passive
        hashes / mod ids are candidates; small ints (levels, weights, stat
        values) are not treated as references."""
        sv = str(v)
        if 8 <= len(sv) <= 10:
            self._cref('trade_hash', path, v, ridx, rkey, cref_rec)
        elif len(sv) >= 4:
            self._cref('numeric_id', path, v, ridx, rkey, cref_rec)

    # ---- conversion/scaling helpers ----
    def _conv(self, pat, path, value, kind, ridx, rkey, conv_rec):
        c = self.conversion.get(pat)
        if c is None:
            c = self.conversion[pat] = {'field_occurrences': 0, 'record_occurrences': 0,
                                        'unique': set(), 'sample': [], 'ctx': {}}
        c['field_occurrences'] += 1
        conv_rec.add(pat)
        c['unique'].add(value)
        if len(c['sample']) < SAMPLE_CAP:
            c['sample'].append([rkey, path, value, kind])
        ctx = c['ctx'].get(path)
        if ctx is None:
            ctx = c['ctx'][path] = {}
        kctx = ctx.get(kind)
        if kctx is None:
            kctx = ctx[kind] = {'occurrences': 0, 'values': set()}
        kctx['occurrences'] += 1
        kctx['values'].add(value)
        if isinstance(value, str) and value in self.vocab:
            sc = self.stat_ctx.setdefault(value, {})
            by_path = sc.setdefault(path, {})
            by_kind = by_path.setdefault(kind, {})
            by_kind[pat] = by_kind.get(pat, 0) + 1

    def _conv_scan_key(self, k, path, ridx, rkey, conv_rec):
        for pat in SCAN_PATTERNS:
            if pat in k:
                self._conv(pat, path, k, 'key', ridx, rkey, conv_rec)

    def _conv_scan_value(self, v, path, ridx, rkey, conv_rec):
        for pat in SCAN_PATTERNS:
            if pat in v:
                self._conv(pat, path, v, 'value', ridx, rkey, conv_rec)

    # ---- exhaustive walk ----
    def run(self):
        for ridx, (rkey, rec) in enumerate(self.records):
            stack = [(rec, '', 0)]
            seen_paths = set()
            conv_rec = set()
            cref_rec = set()
            while stack:
                v, path, depth = stack.pop()
                if depth > self.max_depth:
                    self.max_depth = depth
                node = self.schema.get(path)
                if node is None:
                    node = self.schema[path] = {'types': set(), 'present_in': 0, 'instances': 0,
                                                'key_union': None, 'key_idlike': set(),
                                                'arr_elem_types': set(), 'nested': False, 'sample': []}
                node['instances'] += 1
                if path not in seen_paths:
                    seen_paths.add(path)
                    node['present_in'] += 1
                t = json_type(v)
                if isinstance(v, dict):
                    node['types'].add(t)
                    node['nested'] = True
                    if node['key_union'] is None:
                        node['key_union'] = set()
                    for k, val in v.items():
                        node['key_union'].add(k)
                        if k.isdigit():
                            node['key_idlike'].add(k)
                        child = f'{path}.{k}' if path else k
                        for kcls, (_desc, pred) in KEY_CLASSES.items():
                            if pred(k):
                                self._cref(kcls, child, str(k), ridx, rkey, cref_rec)
                        self._conv_scan_key(k, child, ridx, rkey, conv_rec)
                        stack.append((val, child, depth + 1))
                elif isinstance(v, list):
                    node['types'].add(t)
                    node['nested'] = True
                    for x in v:
                        node['arr_elem_types'].add(json_type(x))
                        stack.append((x, path + '[]', depth + 1))
                else:
                    node['types'].add(t)
                    if len(node['sample']) < SAMPLE_CAP:
                        node['sample'].append(v)
                    if isinstance(v, str):
                        self._conv_scan_value(v, path, ridx, rkey, conv_rec)
                        self._cref_value(v, path, ridx, rkey, cref_rec)
                    elif type(v) is int:
                        self._cref_int(v, path, ridx, rkey, cref_rec)
            for pat in conv_rec:
                self.conversion[pat]['record_occurrences'] += 1
        return self._finalize()

    # ---- keyed-map detection ----
    @staticmethod
    def _detect_keyed(schema):
        keyed = set()
        for p, n in schema.items():
            if n['key_union'] is None:
                continue
            if len(n['key_union']) > KEYED_MAX_FIELDS:
                keyed.add(p)
            elif n['instances'] >= 2 and len(n['key_union']) > KEYED_MIN_KEYS \
                    and len(n['key_union']) >= KEYED_RATIO * n['instances']:
                keyed.add(p)
            elif len(n['key_union']) == len(n['key_idlike']) and len(n['key_union']) >= 2:
                keyed.add(p)
        return keyed

    # ---- lossless keyed-map inventory ----
    def _keyed_inventory(self, schema, keyed):
        """LOSSLESS per-keyed-map inventory. For every keyed map path P store:
        key_count (exact), the full sorted list of concrete keys, shape_count
        (distinct child shapes across keys), and per shape-group the keys that
        share it. When a map has several distinct child shapes, each group
        carries a representative relative child schema. When all keys share
        one shape (the common case), schema is null and the per-key child
        schema equals the compact `P.{}` subtree in the report schema."""
        paths = sorted(schema)
        memo = {}

        def signature(q):
            if q in memo:
                return memo[q]
            n = schema[q]
            if q in keyed:
                inst_paths = [q + '.' + k if q else k for k in n['key_union']]
                vtypes = tuple(sorted({tuple(sorted(schema[ip]['types'])) for ip in inst_paths}))
                sig = ('keyed', vtypes)
            elif n['key_union'] is not None:
                children = []
                for k in n['key_union']:
                    cp = f'{q}.{k}' if q else k
                    if cp in keyed:
                        children.append(('*', signature(cp)))  # data-keyed child: name is data, drop it
                    elif k in self.vocab:
                        children.append(('@stat', signature(cp)))  # stat-id key: name is data
                    else:
                        children.append((k, signature(cp)))
                vals = [c for _name, c in children]
                if len(vals) >= 2 and len(set(vals)) == 1:
                    # all children share one shape -> a data-keyed map (mods, stat maps);
                    # names are data, canonicalize to the single child shape
                    sig = ('map', vals[0])
                else:
                    sig = ('obj', tuple(sorted(children)))
            elif n['arr_elem_types'] is not None:
                elem = signature(q + '[]') if (q + '[]') in schema else None
                sig = ('arr', tuple(sorted(n['arr_elem_types'])), elem)
            else:
                sig = ('sc', tuple(sorted(n['types'])))
            memo[q] = sig
            return sig

        def subtree(q):
            lo = bisect.bisect_left(paths, q)
            hi = bisect.bisect_left(paths, q + '.' + '\uffff')
            return [p for p in paths[lo:hi] if p == q or p.startswith(q + '.')]

        out = {}
        for P in sorted(keyed):
            keys = sorted(schema[P]['key_union'])
            groups = {}
            for K in keys:
                PK = f'{P}.{K}' if P else K
                groups.setdefault(signature(PK), []).append(K)
            entries = [{'keys': gk, 'schema': None} for gk in groups.values()]
            if len(entries) > 1:
                for e in entries:
                    K0 = e['keys'][0]
                    PK = f'{P}.{K0}' if P else K0
                    rel_schema = {}
                    for q in subtree(PK):
                        n = schema[q]
                        rel = '' if q == PK else q[len(PK) + 1:]
                        rel_schema[rel] = {'types': sorted(n['types']),
                                           'arr_elem_types': sorted(n['arr_elem_types']) if n['arr_elem_types'] else None,
                                           'keyed': q in keyed,
                                           'nested': n['nested']}
                    e['schema'] = rel_schema
            out[P] = {'key_count': len(keys), 'keys': keys,
                      'shape_count': len(entries), 'shape_groups': entries}
        return out

    # ---- compact schema (report view) ----
    @staticmethod
    def _collapse_keyed(schema, keyed):
        """STRUCTURAL compact schema for the report. See _keyed_inventory for
        the lossless counterpart; this view is NOT a complete key listing."""

        def emit(n):
            ku = n['key_union'] if n.get('key_union') is not None else None
            return {'types': sorted(n['types']), 'present_in': n['present_in'],
                    'instances': n['instances'],
                    'key_union': len(ku) if ku is not None else None,
                    'key_idlike': len(n['key_idlike']),
                    'key_sample': sorted(ku)[:KEY_SAMPLE_CAP] if ku else None,
                    'arr_elem_types': sorted(n['arr_elem_types']) if n['arr_elem_types'] else None,
                    'nested': n['nested'], 'sample': n['sample']}

        if not keyed:
            return {p: emit(n) for p, n in schema.items()}

        def remap(p):
            if not p:
                return ''
            out = []
            orig = ''
            for seg in p.split('.'):
                if orig in keyed:
                    out.append('{}')  # `seg` is an instance key of the keyed map at `orig`
                else:
                    out.append(seg)
                orig = f'{orig}.{seg}' if orig else seg
            return '.'.join(out)

        merged = {}
        for p, n in schema.items():
            mapped = remap(p)
            t = merged.get(mapped)
            if t is None:
                t = merged[mapped] = {'types': set(n['types']), 'present_in': n['present_in'],
                                      'instances': n['instances'],
                                      'key_union': set(n['key_union'] or []),
                                      'key_idlike': set(n['key_idlike']),
                                      'arr_elem_types': set(n['arr_elem_types'] or []),
                                      'nested': n['nested'], 'sample': list(n['sample'])}
            else:
                t['types'].update(n['types'])
                t['present_in'] += n['present_in']
                t['instances'] += n['instances']
                t['key_union'].update(n['key_union'] or [])
                t['key_idlike'].update(n['key_idlike'])
                if n['arr_elem_types']:
                    t['arr_elem_types'].update(n['arr_elem_types'])
                t['nested'] = t['nested'] or n['nested']
                if len(t['sample']) < SAMPLE_CAP:
                    t['sample'].extend(n['sample'][:SAMPLE_CAP - len(t['sample'])])
        return {p: emit(n) for p, n in merged.items()}

    # ---- finalize ----
    def _finalize(self):
        keyed = self._detect_keyed(self.schema)
        schema = self._collapse_keyed(self.schema, keyed)
        keyed_maps = self._keyed_inventory(self.schema, keyed)
        crossrefs = {}
        for cls, c in self.crossrefs.items():
            paths = {}
            for p, pn in c['paths'].items():
                ds = sorted(pn['distinct'])
                paths[p] = {'occurrences': pn['occurrences'],
                            'distinct_count': len(ds),
                            'distinct_sample': ds[:DISTINCT_CAP],
                            'sample': pn['sample']}
            ds = sorted(c['distinct'])
            crossrefs[cls] = {
                'field_occurrences': c['field_occurrences'],
                'records_touched': len(c['records']),
                'distinct_count': len(ds),
                'distinct_sample': ds[:DISTINCT_CAP],
                'sample': c['sample'],
                'paths': paths,
            }
        conversion = {}
        for pat, c in self.conversion.items():
            us = sorted(c['unique'])
            contexts = {}
            for path, kinds in c['ctx'].items():
                contexts[path] = {}
                for kind, kctx in kinds.items():
                    vs = sorted(kctx['values'])
                    contexts[path][kind] = {
                        'occurrences': kctx['occurrences'],
                        'distinct_count': len(vs),
                        'distinct_sample': vs[:DISTINCT_CAP],
                    }
            conversion[pat] = {
                'field_occurrences': c['field_occurrences'],
                'record_occurrences': c['record_occurrences'],
                'unique_count': len(us),
                'unique_sample': us[:DISTINCT_CAP],
                'contexts': contexts,
                'sample': c['sample'],
            }
        return {'schema': schema, 'keyed_maps': keyed_maps, 'max_nesting_depth': self.max_depth,
                'crossrefs': crossrefs, 'conversion': conversion,
                'stat_ctx': self.stat_ctx}


def examples_of(records, n=5, maxlen=2000):
    out = []
    for rkey, rec in records[:n]:
        if isinstance(rkey, str):
            s = json.dumps(rec)[:maxlen]
            out.append({'key': rkey, 'record': s + ('…[truncated]' if len(json.dumps(rec)) > maxlen else '')})
        else:
            s = json.dumps(rec)[:maxlen]
            out.append({'index': rkey, 'record': s + ('…[truncated]' if len(json.dumps(rec)) > maxlen else '')})
    return out


def analyze_file(relpath, vocab):
    full = ROOT / relpath
    if not full.exists():
        return {'relpath': relpath, 'size': 0, 'parse_ok': False, 'error': 'planned file missing on disk'}
    size = full.stat().st_size
    try:
        with open(full, encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return {'relpath': relpath, 'size': size, 'parse_ok': False, 'error': str(e)}
    shape, records, count, semantics = classify(data)
    fa = FileAnalyzer(records, vocab, relpath)
    scanned = fa.run()
    stat_ctx = scanned.pop('stat_ctx')
    return {
        'relpath': relpath, 'size': size, 'parse_ok': True,
        'shape': shape, 'record_count': count, 'record_count_semantics': semantics,
        'records_scanned': len(records),
        'schema': scanned['schema'], 'keyed_maps': scanned['keyed_maps'],
        'max_nesting_depth': scanned['max_nesting_depth'],
        'crossrefs': scanned['crossrefs'], 'conversion': scanned['conversion'],
        'examples': examples_of(records),
        'stat_ctx': stat_ctx,
    }


def load_vocab():
    if VOCAB_CACHE.exists():
        return set(json.load(open(VOCAB_CACHE)))
    from vocab import collect_ids
    return collect_ids()


def main():
    vocab = load_vocab()
    manifest = json.load(open(ROOT / 'manifest.json'))
    rels = sorted(r for r in manifest if r != META_KEY)
    results = []
    for rel in rels:
        results.append(analyze_file(rel, vocab))
    results.sort(key=lambda r: r['relpath'])

    # global stat-id conversion-context companion: stat_id -> {file: {path: {kind: {pattern: count}}}}
    stat_ctx = {}
    for r in results:
        if not r.get('parse_ok'):
            continue
        for sid, by_path in (r.pop('stat_ctx') or {}).items():
            s = stat_ctx.setdefault(sid, {})
            s[r['relpath']] = by_path
    CACHE.mkdir(parents=True, exist_ok=True)
    json.dump(results, open(ANALYSIS_CACHE, 'w'), indent=1)
    json.dump(stat_ctx, open(STAT_CTX_CACHE, 'w'), indent=1)

    errs = [r['relpath'] for r in results if not r.get('parse_ok')]
    print(f"analyzed {len(results)} files, errors: {len(errs)}")
    for e in errs[:10]:
        print('  ERR', e)
    paths = sum(len(r['schema']) for r in results if r.get('parse_ok'))
    kmaps = sum(len(r.get('keyed_maps') or {}) for r in results if r.get('parse_ok'))
    print(f"total compact schema paths: {paths}; lossless keyed maps: {kmaps}")
    print(f"stat-id conversion context entries: {len(stat_ctx)}")


if __name__ == '__main__':
    main()
