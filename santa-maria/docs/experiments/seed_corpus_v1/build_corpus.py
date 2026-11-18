"""Frozen seed corpus v1 builder — public Research API only.

Deterministic: same KB + same script -> same corpus (all seeds recorded).
Operations used: phase8_research.resolve (lookup + ascendancy enumeration),
phase6_api.get_start_seed (recorded-seed random draws). No KB internals.

Run:   uv run python santa-maria/docs/experiments/seed_corpus_v1/build_corpus.py
Emit:  seed_corpus_v1/corpus.json + verification summary on stdout.
"""
import datetime
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import phase6_api as api          # noqa: E402
import phase8_research as R       # noqa: E402

GLOBAL_SEED = 20260916
QUOTA = [('UniqueItem', 12), ('Passive', 8), ('Gem', 8), ('Stat', 8),
         ('Modifier', 6), ('Mechanic', 5), ('Tag', 4), ('ItemClass', 7)]
MAX_CALLS_PER_TYPE = 120

MANDATORY = [
    {'node_id': 'unique:1198', 'type': 'UniqueItem',
     'name': "Replica Alberon's Warpath", 'seed': None,
     'block': 'mandatory',
     'why': 'pinned mandatory concept: replica-stacking link (Minion Instability '
            'family / unique replica variant); tests replica-variant discovery'},
    {'node_id': 'unique:1461', 'type': 'UniqueItem',
     'name': 'Whispers of Infinity', 'seed': None,
     'block': 'mandatory',
     'why': 'pinned mandatory concept: timeless-jewel keystone transformation; '
            'tests passive-tree mutation discovery'},
    {'node_id': 'item_class:Boots', 'type': 'ItemClass',
     'name': None, 'seed': None,
     'block': 'mandatory',
     'why': 'pinned mandatory concept: rare-base Accuracy-stacking boots archetype '
            'as the ITEM CLASS (rare base), deliberately not a UniqueItem; '
            'tests base-archetype discovery (KB has no display name for ItemClass '
            'nodes: id is the anchor)'},
]

WHY = {
    'UniqueItem': 'build-assembly discovery: unique mechanics as consumer anchors',
    'Passive': 'tree/class-anchored discovery via passive_info (kind_flags preserved)',
    'Gem': 'skill/support interaction discovery via gem tags and stats',
    'Stat': 'reverse-carrier fan-out discovery (carriers) across mods/gems/passives',
    'Modifier': 'carrier-family discovery: which uniques share a resolved mod',
    'Mechanic': 'mechanic-consumer discovery via stat_mechanic relations',
    'Tag': 'coarse fan-out discovery via tag membership (deliberately broad)',
    'ItemClass': 'base-archetype discovery: rare-base families by item class',
}


def family(entry):
    """Near-duplicate key: normalized name (or id) base."""
    s = (entry.get('name') or entry.get('node_id')
         or entry.get('id') or '').lower()
    s = re.sub(r'^replica ', '', s)
    s = re.sub(r'^(awakened|anomalous|divergent|phantasmal) ', '', s)
    s = re.sub(r'(altx|alt\d+)$', '', s)
    s = re.sub(r'\d+$', '', s)
    return re.sub(r'[^a-z]', '', s)


def entry_of(node_id, ntype, name, seed, block, why, notes=None):
    e = {'node_id': node_id, 'type': ntype, 'name': name,
         'seed': seed, 'block': block, 'why': why}
    if notes:
        e['notes'] = notes
    return e


def build():
    entries = []
    seen_ids, seen_families = set(), set()

    def admits(node_id, fam):
        return node_id not in seen_ids and (fam is None or fam not in seen_families)

    def admit(e, fam):
        entries.append(e)
        seen_ids.add(e['node_id'])
        if fam is not None:
            seen_families.add(fam)

    # ---- block 1: mandatory pinned concepts --------------------------------
    for m in MANDATORY:
        env = R.resolve(m['node_id'])
        assert env['error'] is None, env
        hits = [r for r in env['results'] if r['id'] == m['node_id']]
        assert len(hits) == 1, (m['node_id'], env)
        r = hits[0]
        assert r['type'] == m['type'], (m['node_id'], r)
        assert r.get('name') == m['name'], (m['node_id'], r)
        admit(entry_of(m['node_id'], m['type'], m['name'], None,
                       m['block'], m['why']), family(r))

    # ---- block 2: ascendancy coverage (exactly one notable per BASE ascendancy)
    # Base namespace = passive:Ascendancy<Asc><n>; Phrecia alternates live in
    # passive:AscendancyCustom<Asc><n> and are excluded (id-namespace criterion,
    # observable through the public resolve substring search).
    env = R.resolve('Ascendancy', type='Passive')
    assert env['error'] is None, env
    assert not env['meta']['truncated'], 'ascendancy enumeration truncated?'
    groups, luminary_notables = {}, 0
    for r in env['results']:
        nid = r['id']
        if not nid.startswith('passive:Ascendancy'):        # AlternateAscendancy* out
            continue
        if nid.startswith('passive:AscendancyCustom'):      # Phrecia alternates out
            continue
        pi = r.get('passive_info') or {}
        k = pi.get('kind_flags') or {}
        asc = pi.get('ascendancy')
        if not (asc and k.get('is_notable')):
            continue
        if asc == 'Luminary':                               # excluded per corpus spec
            luminary_notables += 1
            continue
        groups.setdefault(asc, []).append(r['id'])
    assert luminary_notables > 0, 'Luminary must exist in base ns and be skipped'
    assert len(groups) == 20, f'base ascendancy labels: {sorted(groups)}'
    rng = random.Random(GLOBAL_SEED)
    for asc in sorted(groups):
        nid = rng.choice(sorted(groups[asc]))
        name = next(r['name'] for r in env['results'] if r['id'] == nid)
        admit(entry_of(nid, 'Passive', name, GLOBAL_SEED, 'ascendancy_coverage',
                       f'base ascendancy coverage: {asc} notable, one per '
                       f'ascendancy (deterministic rng over sorted notables)',
                       notes={'ascendancy': asc}), family({'name': name}))

    # ---- block 3: stratified recorded-seed random draws --------------------
    seed_cursor = GLOBAL_SEED
    calls = 0
    for typ, quota in QUOTA:
        got = 0
        type_calls = 0
        while got < quota and type_calls < MAX_CALLS_PER_TYPE:
            seed_cursor += 1
            type_calls += 1
            calls += 1
            env = api.get_start_seed({'seed': seed_cursor, 'type': typ,
                                      'count': 2,
                                      # reproduce the frozen corpus exactly:
                                      # opt into the pre-exclusion pool, the
                                      # builder rejects alternates itself
                                      'include_alternate_ascendancies': True})
            if env.get('error'):
                continue
            for s in env.get('seeds', []):
                nid, ntype = s['node_id'], s.get('type')
                name = s.get('name')
                if ntype != typ:                      # defensive
                    continue
                if 'AscendancyCustom' in nid or 'AlternateAscendancy' in nid:
                    continue                        # non-base ascendancy material
                pi = s.get('passive_info') or {}
                if pi.get('ascendancy'):            # asc nodes only in block 2
                    continue
                fam = family(s)
                if not admits(nid, fam):
                    continue
                notes = {'kind_flags': pi.get('kind_flags')} if pi else None
                admit(entry_of(nid, typ, name, seed_cursor, 'random_draw',
                               WHY[typ], notes=notes), fam)
                got += 1
                if got >= quota:
                    break
        if got < quota:
            print(f'WARN: {typ} filled {got}/{quota} '
                  f'({type_calls} calls)')

    # ---- verification ------------------------------------------------------
    assert len(entries) == 81, f'corpus size {len(entries)} != frozen 81'
    assert not any('<<' in (e.get('name') or '') for e in entries), \
        'placeholder-style display name leaked into corpus'
    assert len(seen_ids) == len(entries), 'duplicate node_id'
    fams = [family(e) for e in entries if family(e)]
    assert len(fams) == len(set(fams)), 'near-duplicate family collision'
    asc_entries = [e for e in entries if e['block'] == 'ascendancy_coverage']
    ascs = [e['notes']['ascendancy'] for e in asc_entries]
    assert len(ascs) == len(set(ascs)) == len(groups), 'asc coverage not 1-per-asc'
    for e in entries:
        env = R.resolve(e['node_id'])
        assert env['error'] is None and \
            any(r['id'] == e['node_id'] for r in env['results']), \
            f'unresolvable: {e["node_id"]}'
    return entries, groups, calls


def main():
    entries, groups, calls = build()
    doc = {
        'name': 'seed_corpus_v1',
        'built_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(
            timespec='seconds'),
        'selection_seed': GLOBAL_SEED,
        'seed_scheme': 'mandatory: seed=null (pinned); ascendancy_coverage: '
                       f'seed={GLOBAL_SEED}, deterministic rng over sorted '
                       'ascendancies and notables; random_draw: per-call '
                       'get_start_seed seed recorded per entry',
        'entries': [{'index': i, **e} for i, e in enumerate(entries)],
    }
    (Path(__file__).resolve().parent / 'corpus.json').write_text(
        json.dumps(doc, indent=1) + '\n')

    dist = {}
    for e in entries:
        dist[e['type']] = dist.get(e['type'], 0) + 1
    print(f'corpus: {len(entries)} entries ({calls} seed calls), '
          f'ascendancies covered: {len(groups)} ({", ".join(sorted(groups))})')
    print('type distribution:', json.dumps(dist, sort_keys=True))
    print('frozen corpus: resolve/carriers/seed starting points all API-resolvable')
    print('demo ok: corpus built + all verification asserts passed')


if __name__ == '__main__':
    main()
