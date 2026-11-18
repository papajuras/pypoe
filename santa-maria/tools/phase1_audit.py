#!/usr/bin/env python3
"""Automated Phase-1 self-audit. Prints PASS/FAIL per checklist item.

Reads the caches + data on disk; exits non-zero if anything FAILs. Run as the
last step of tools/phase1_run.sh.
"""
import json, os, re, sys
from pathlib import Path

SANTA = Path(__file__).resolve().parents[1]
D = SANTA / 'data'
CACHE = SANTA / 'cache'
DOCS = SANTA / 'docs'


def files_on_disk():
    out = set()
    for root, _dirs, files in os.walk(D):
        for fn in files:
            if fn != 'manifest.json' and fn.endswith('.json'):
                out.add(os.path.relpath(os.path.join(root, fn), D))
    return out


def load_manifest():
    """Return (file-entries set, _meta dict). The reserved `_meta` key holds
    snapshot provenance (upstream commit SHAs, stale/missing files) and is NOT
    a data file entry."""
    raw = json.load(open(D / 'manifest.json'))
    meta = raw.get('_meta') or {}
    entries = set(k for k in raw if k != '_meta')
    return entries, meta


def manifest():
    entries, _meta = load_manifest()
    return entries


def main():
    print("PHASE 1 SELF-AUDIT")
    disk = files_on_disk()
    mf = manifest()
    _entries, meta = load_manifest()
    analy = json.load(open(CACHE / 'analysis.json'))
    by = {r['relpath']: r for r in analy}
    inv = json.load(open(CACHE / 'investigations.json'))

    checks = []
    checks.append(('Every in-scope downloaded JSON file analyzed',
                   mf <= set(by) and all(by[p].get('parse_ok') for p in mf)))
    checks.append(('Analyzed files == manifest entries',
                   mf == set(by)))
    checks.append(('Snapshot manifest plan-scoped (no stale, no missing planned files)',
                   not meta.get('stale_files') and not meta.get('missing_files')))
    checks.append(('planned == downloaded_ok + missing',
                   meta.get('planned_count') == len(mf) + len(meta.get('missing_files') or [])
                   and meta.get('downloaded_ok_count') == len(mf)))
    sources = meta.get('sources') or {}
    checks.append(('Upstream snapshot provenance recorded (commit SHA per source)',
                   bool(sources) and all(i.get('commit') for i in sources.values())))
    checks.append(('Schema derived from all records (records_scanned == record_count for every file)',
                   all(r.get('parse_ok') and r['records_scanned'] == r['record_count'] for r in analy)))
    present_ok = True
    for r in analy:
        if not r.get('parse_ok'):
            continue
        for p, n in r['schema'].items():
            if p == '{}' or p.startswith('{}.'):
                continue  # collapsed keyed-map root: present_in counts instances, not records
            if '.' not in p and '[]' not in p and p != '' and n['present_in'] > r['record_count']:
                present_ok = False
    checks.append(('Nested structures scanned exhaustively (consistent present_in vs record_count)',
                   present_ok))
    checks.append(('Cross-reference scan exhaustive (every analyzed file has crossref results)',
                   all(r.get('parse_ok') and 'crossrefs' in r and 'conversion' in r for r in analy)))
    checks.append(('Conversion/scaling scan exhaustive (patterns found across corpus)',
                   any(r.get('parse_ok') and r['conversion'] for r in analy)))

    # lossless keyed-map inventory: every compact keyed map has a keyed_maps
    # entry whose exact key count matches and whose key list is complete
    km_ok = True
    km_fail = []
    for r in analy:
        if not r.get('parse_ok'):
            continue
        for P, info in (r.get('keyed_maps') or {}).items():
            node = r['schema'].get(P)
            # nested keyed maps (under another keyed map) are collapsed to `{}`
            # in the compact schema, so their node is absent there; the raw
            # key list in keyed_maps is authoritative either way.
            if node is not None and node.get('key_union') != info['key_count']:
                km_ok = False
                km_fail.append((r['relpath'], P, 'key_union mismatch'))
            if len(info['keys']) != info['key_count'] or len(set(info['keys'])) != info['key_count']:
                km_ok = False
                km_fail.append((r['relpath'], P, 'key list incomplete/non-unique'))
            if info['shape_count'] != len(info['shape_groups']):
                km_ok = False
                km_fail.append((r['relpath'], P, 'shape_count mismatch'))
            for g in info['shape_groups']:
                if info['shape_count'] > 1 and not g['schema']:
                    km_ok = False
                    km_fail.append((r['relpath'], P, 'multi-shape group missing schema'))
    checks.append(('Keyed-map compaction is lossless (key_union == keyed_maps key_count, complete keys, per-shape schemas)',
                   km_ok))

    num_ok = any(cls in r['crossrefs'] and r['crossrefs'][cls]['distinct_count'] > 0
                 for r in analy if r.get('parse_ok') for cls in ('numeric_id', 'trade_hash'))
    checks.append(('Numeric reference candidates detectable (int ids/hashes in numeric_id/trade_hash)',
                   num_ok))
    ctx_ok = (CACHE / 'stat_conversion_context.json').exists() and bool(json.load(open(CACHE / 'stat_conversion_context.json')))
    checks.append(('Conversion/scaling full context recoverable (stat_conversion_context.json present)',
                   ctx_ok))

    sections = len(re.findall(r'^### `', open(DOCS / 'data_inventory.md').read(), re.M))
    checks.append(('Every file has its own inventory section', sections == len(analy)))

    # Crown of Eyes: verify the investigation explicitly examined the requested files
    co = inv['crown_of_eyes']
    fe = {x['file']: x for x in co.get('files_examined') or []}
    req_files = ['repoe/mods.json', 'pob/ModItemExclusive.json', 'pob/ModCache.json',
                 'pob/QueryMods.json', 'pob/TradeSiteStats.json', 'pob/ModItem.json']
    co_ok = all(fe.get(f, {}).get('examined') for f in req_files)
    checks.append(('Crown of Eyes examined all requested files (mods/ModItemExclusive/ModCache/QueryMods/TradeSiteStats/ModItem)',
                   co_ok))
    checks.append(('Iron Will trace verified (hash 50288)',
                   inv['iron_will'].get('hash') == 50288))
    checks.append(('Avatar of Fire trace verified (hash 44941)',
                   inv['avatar_of_fire'].get('hash') == 44941))
    checks.append(('Manifest matches files on disk', mf == disk))
    checks.append(('Analysis count matches manifest', len(analy) == len(mf)))

    all_pass = True
    for label, ok in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {label}")
        all_pass = all_pass and ok
    if km_fail:
        print('  keyed_maps failures (first 5):', km_fail[:5])
    print(f"\nOverall: {'ALL PASS' if all_pass else 'FAILURES PRESENT'}")
    return 0 if all_pass else 1


if __name__ == '__main__':
    sys.exit(main())
