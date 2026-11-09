#!/usr/bin/env python3
"""Benchmark v1 (isolated run) — Stage A probe program.

Public API ONLY (discovery-api-usage): phase8_research.resolve/carriers,
phase6_api.get_neighbour. No graph internals, no DB access, no reading of
the earlier benchmark_v1 run's artifacts.

Fixed per-entry budget (Stage A, uniform for all 81 entries, <= 6 calls):
  A0  resolve(node_id)            resolvability + name/availability
  A1  neighbour(depth=3, both, carrier_grouping, cap=60)
  A2  carriers(node_id)           reverse fan-out with counts
  A3  carriers(stat) on top-2 downstream stats (rank: mech-linked desc,
      observed fan-in desc, id asc)
  A4  neighbour(mechanic, depth=1, in, mech edge types, cap=200, prov on)
      — at most 1 mechanic per entry, only when a mechanic was seen

Every call is appended to audit/api_calls.jsonl (auditable usage).
Digests land in digests/digest_<idx>.json + digests_all.json.
"""
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SANTA = HERE.parents[2]
sys.path.insert(0, str(SANTA / 'tools'))

import phase8_research as R          # noqa: E402  (public research API)
import phase6_api as api             # noqa: E402  (public discovery API)

CORPUS = SANTA / 'docs' / 'experiments' / 'seed_corpus_v1' / 'corpus.json'
AUDIT = HERE / 'audit'
DIGESTS = HERE / 'digests'

GRANT = {'unique_modifier_association', 'modifier_grants_stat',
         'passive_grants_stat', 'gem_grants_stat', 'attribute_grants_stat'}
MECH = ('stat_mechanic_relation', 'stat_mechanic_operand',
        'stat_mechanic_variant')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class Audit:
    def __init__(self):
        AUDIT.mkdir(parents=True, exist_ok=True)
        self.fh = (AUDIT / 'api_calls.jsonl').open('a', encoding='utf-8')

    def call(self, seed_idx, op, **kw):
        t0 = time.time()
        if op == 'resolve':
            res = R.resolve(kw['query'], type=kw.get('type'))
        elif op == 'carriers':
            res = R.carriers(kw['node_id'], edge_types=kw.get('edge_types'))
        elif op == 'neighbour':
            res = api.get_neighbour(kw['depth'], kw['filters'])
        else:
            raise ValueError(op)
        dt = round(time.time() - t0, 3)
        m = res.get('meta') or {}
        if op == 'neighbour':
            summary = {'levels': [len(l['edges']) for l in res.get('levels', [])],
                       'truncated': res.get('truncated')}
        else:
            summary = {'total': m.get('total'), 'counts': m.get('counts'),
                       'truncated': m.get('truncated')}
        if res.get('error'):
            summary['error'] = res['error']['code']
        rec = {'seed': seed_idx, 'op': op, 'args': kw, 'dt_s': dt, 'meta': summary}
        self.fh.write(json.dumps(rec) + '\n')
        self.fh.flush()
        return res


def carrier_summary(env, limit=8):
    """Group carriers() rows per edge type: count + up to `limit` named
    samples, preferring ascendancy notables and uniques."""
    out = {}
    by_et = {}
    for r in env.get('results', []):
        by_et.setdefault(r['edge_type'], []).append(r)
    for et, rs in sorted(by_et.items()):
        rs = sorted(rs, key=lambda r: (
            0 if (r.get('passive_info') or {}).get('ascendancy') else 1,
            0 if r.get('availability') is not None else 1, r['carrier']))
        samples = []
        for r in rs[:limit]:
            s = {'id': r['carrier'], 'name': r.get('name')}
            if r.get('availability') is not None:
                s['avail'] = r['availability']
            pi = r.get('passive_info')
            if pi and pi.get('ascendancy'):
                s['asc'] = pi['ascendancy']
            samples.append(s)
        out[et] = {'count': len(rs), 'samples': samples}
    return out


def analyze_bfs(nid, a1, a0):
    """Post-process a public get_neighbour envelope: downstream stats along
    grant chains, observed carrier fan-in, mechanic links, asc passives."""
    names = {r['id']: r.get('name') for r in (a0.get('results') or [])}
    adj = {}
    mech_links = {}
    passives = {}
    for lv in a1.get('levels', []):
        for e in lv['edges']:
            if e['direction'] == 'out' and e['type'] in GRANT:
                adj.setdefault(e['from'], []).append((e['to'], e['type']))
            if e['type'] in MECH:
                for s in (e['from'], e['to']):
                    if s.startswith('stat:'):
                        mech_links.setdefault(s, set()).add(e['type'])
        for pn in lv.get('passive_nodes', []):
            pi = pn.get('passive_info') or {}
            if pi.get('ascendancy'):
                passives[pn['id']] = {'name': pn['name'], 'asc': pi['ascendancy']}
    fanin = {}
    for lv in a1.get('levels', []):
        for g in lv.get('carrier_groups', []):
            for m in g['members']:
                fanin[m] = fanin.get(m, 0) + g['count']
    seen, dstats, frontier = {nid}, [], [(nid, [])]
    while frontier:
        nxt = []
        for node, chain in frontier:
            for tgt, et in adj.get(node, []):
                if tgt in seen:
                    continue
                seen.add(tgt)
                ch = chain + [f'{et}>{tgt}']
                if tgt.startswith('stat:'):
                    dstats.append({'stat': tgt,
                                   'chain': ' -> '.join(ch) or nid,
                                   'mech': sorted(mech_links.get(tgt, [])),
                                   'fanin_seen': fanin.get(tgt, 0)})
                nxt.append((tgt, ch))
        frontier = nxt
    dstats.sort(key=lambda d: d['stat'])
    return names, dstats, mech_links, passives


def rank_stats(dstats, mech_links, fanin):
    """Deterministic A3 selection: mech-linked first, then observed fan-in,
    then id — top 2."""
    return [d['stat'] for d in sorted(
        dstats, key=lambda d: (d['stat'] in mech_links,
                               -fanin.get(d['stat'], 0), d['stat']))[:2]]


COLLAPSE_IN = {'unique_in_class', 'gem_has_tag', 'modifier_has_tag'}


def rollup_level(lv):
    fwd, rev = [], {}
    for e in lv['edges']:
        if e['direction'] == 'in' and e['type'] in COLLAPSE_IN:
            rev.setdefault((e['type'], e['from']), []).append(e['to'])
        else:
            fwd.append(f"{e['type']}|{e['from']}|{e['to']}|{e['direction']}")
    return fwd + [f"{t}|{f}|<{len(ms)} in: {', '.join(sorted(ms)[:3])}"
                  f"{'…' if len(ms) > 3 else ''}>"
                  for (t, f), ms in sorted(rev.items())]


def digest_for(entry, calls, a0, a1, a2, dstats, a3_detail, a4):
    nid, typ = entry['node_id'], entry['type']
    hits = a0.get('results') or []
    start_name = hits[0].get('name') if hits else None
    avail = hits[0].get('availability') if hits else None
    d = {
        'index': entry['index'], 'node_id': nid, 'type': typ,
        'name': start_name, 'block': entry['block'],
        'availability': avail,
        'calls': [{op: args} for op, args, _ in calls],
        'start_carriers': carrier_summary(a2) if a2 else None,
        'bfs_truncated': a1.get('truncated'),
        'bfs_levels': [{'depth': lv['depth'],
                        'edges': rollup_level(lv),
                        'groups': lv.get('carrier_groups', [])}
                       for lv in a1.get('levels', [])],
        'downstream_stats': dstats,
        'stat_carriers': a3_detail,
        'mechanic_view': a4,
    }
    flags = []
    src = [et for et, v in (d['start_carriers'] or {}).items() if v['count']]
    if hits and not a1.get('levels') and all(
            v['count'] == 0 for v in (d['start_carriers'] or {}).values()):
        flags.append('zero_edges')
    elif not src and typ in ('Stat', 'Modifier', 'Gem', 'Passive'):
        flags.append('zero_carrier_start')
    for st, det in a3_detail.items():
        if sum(1 for v in det['carriers'].values() if v['count']) >= 3:
            flags.append(f'multi_source:{st.split(":",1)[1]}')
    if any(ds['mech'] for ds in dstats):
        flags.append('mech_linked')
    if any('|stat_scales_with|' in e for lv in d['bfs_levels'] for e in lv['edges']):
        flags.append('scales_with')
    tot = sum(v['count'] for v in (d['start_carriers'] or {}).values())
    if tot >= 50:
        flags.append(f'big_fanin:{tot}')
    if d['bfs_truncated']:
        flags.append('truncated_bfs')
    if a4 and a4['related_stats'] >= 80:
        flags.append(f"mech_hub:{a4['related_stats']}")
    d['flags'] = flags
    return d


def main(argv=None):
    only = None
    if argv and argv[0] == '--only':
        only = {int(x) for x in argv[1].split(',')}
    corpus = json.loads(CORPUS.read_text())
    audit = Audit()
    all_d = []
    for entry in corpus['entries']:
        idx, nid = entry['index'], entry['node_id']
        if only is not None and idx not in only:
            continue
        calls = []
        a0 = audit.call(idx, 'resolve', query=nid)
        calls.append(('resolve', {'query': nid}, a0))
        a1 = audit.call(idx, 'neighbour', depth=3, filters={
            'start': nid, 'direction': 'both', 'carrier_grouping': True,
            'max_nodes_per_level': 60})
        calls.append(('neighbour', {'depth': 3, 'start': nid}, a1))
        a2 = audit.call(idx, 'carriers', node_id=nid)
        calls.append(('carriers', {'node_id': nid}, a2))
        names, dstats, mech_links, _ = analyze_bfs(nid, a1, a0)
        a3s = []
        for st in rank_stats(dstats, mech_links, _fanin_of(a1)):
            env = audit.call(idx, 'carriers', node_id=st)
            calls.append(('carriers', {'node_id': st}, env))
            a3s.append((st, env))
        a4 = None
        mech_ids = sorted({n for lv in a1.get('levels', []) for e in lv['edges']
                           if e['type'] in MECH
                           for n in (e['from'], e['to'])
                           if n.startswith('mechanic:')})
        if mech_ids:
            env = audit.call(idx, 'neighbour', depth=1, filters={
                'start': mech_ids[0], 'direction': 'in',
                'edge_types': list(MECH), 'max_nodes_per_level': 200,
                'include_provenance': True})
            calls.append(('neighbour', {'mechanic': mech_ids[0]}, env))
            stats, roles = set(), {}
            for lv in env.get('levels', []):
                for e in lv['edges']:
                    s = e['from'] if e['from'] != mech_ids[0] else e['to']
                    stats.add(s)
                    pv = e.get('provenance') or {}
                    roles[s] = (f"{e['type'].replace('stat_mechanic_', '')}"
                                + (f":{pv['role']}" if pv.get('role') else ''))
            a4 = {'mechanic': mech_ids[0], 'related_stats': len(stats),
                  'truncated': env.get('truncated'),
                  'sample': [{'stat': s, 'role': roles[s]}
                             for s in sorted(stats)[:24]]}
        a3_detail = {st: {'carriers': carrier_summary(env)} for st, env in a3s}
        d = digest_for(entry, calls, a0, a1, a2, dstats, a3_detail, a4)
        all_d.append(d)
        print(f"[{idx:02d}] {entry['type']:12s} {str(entry.get('name'))[:34]:34s} "
              f"calls={len(calls)} flags={','.join(d['flags']) or '-'}", flush=True)
        DIGESTS.mkdir(parents=True, exist_ok=True)
        (DIGESTS / f'digest_{idx:02d}.json').write_text(json.dumps(d, indent=1))
    (DIGESTS / 'digests_all.json').write_text(json.dumps(all_d))
    (HERE / 'audit' / 'run_meta.json').write_text(json.dumps({
        'corpus_sha256': sha(CORPUS),
        'nodes_db_sha256': sha(SANTA / 'cache' / 'nodes.db')[:16],
        'edges_db_sha256': sha(SANTA / 'cache' / 'edges.db')[:16]}, indent=1))
    print('stage A complete:', len(all_d), 'entries')


def _fanin_of(a1):
    fanin = {}
    for lv in a1.get('levels', []):
        for g in lv.get('carrier_groups', []):
            for m in g['members']:
                fanin[m] = fanin.get(m, 0) + g['count']
    return fanin


if __name__ == '__main__':
    main(sys.argv[1:])
