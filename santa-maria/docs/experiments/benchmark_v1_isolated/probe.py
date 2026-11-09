#!/usr/bin/env python3
"""Stage C — bounded deep probes + validation calls (public API only).

Every call logged to audit/api_calls.jsonl with stage='C'. Budget per
promoted seed recorded in stagec_budget.json.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SANTA = HERE.parents[2]
sys.path.insert(0, str(SANTA / 'tools'))

import phase8_research as R          # noqa: E402
import phase6_api as api             # noqa: E402
import phase7_build_validity as bv   # noqa: E402
import phase7_build_feasibility as feas  # noqa: E402

AUDIT = HERE / 'audit'


class CAudit:
    def __init__(self):
        self.fh = (AUDIT / 'api_calls.jsonl').open('a', encoding='utf-8')
        self.n = 0

    def log(self, seed, op, args, meta):
        self.fh.write(json.dumps({'seed': seed, 'stage': 'C', 'op': op,
                                  'args': args, 'meta': meta}) + '\n')
        self.fh.flush()
        self.n += 1


A = CAudit()


def resolve(seed, q, type=None):
    env = R.resolve(q, type=type)
    A.log(seed, 'resolve', {'query': q, 'type': type},
          {'total': env.get('meta', {}).get('total'),
           'truncated': env.get('meta', {}).get('truncated'),
           'error': env.get('error', {}).get('code') if env.get('error') else None})
    if env.get('error'):
        print(f'    resolve({q!r}, {type}): ERROR {env["error"]["code"]} '
              f'candidates={[c for c in env["error"]["candidates"][:4]]}')
        return []
    rows = env.get('results', [])
    print(f'    resolve({q!r}, {type}): {env["meta"]["total"]} matches')
    for r in rows[:14]:
        extra = []
        if r.get('availability') is not None:
            extra.append(f"avail={r['availability']}")
        pi = r.get('passive_info')
        if pi and pi.get('ascendancy'):
            extra.append(f"asc={pi['ascendancy']}")
        print(f"      {r['id']} name={r.get('name')!r} {' '.join(extra)}")
    if env['meta'].get('truncated'):
        print(f'      TRUNCATED total={env["meta"]["truncated"]["total"]}')
    return rows


def carriers(seed, nid, edge_types=None, show=10):
    env = R.carriers(nid, edge_types=edge_types)
    A.log(seed, 'carriers', {'node_id': nid, 'edge_types': edge_types},
          {'counts': env.get('meta', {}).get('counts'),
           'total': env.get('meta', {}).get('total'),
           'truncated': env.get('meta', {}).get('truncated'),
           'error': env.get('error', {}).get('code') if env.get('error') else None})
    if env.get('error'):
        print(f'    carriers({nid}): ERROR {env["error"]["code"]}')
        return []
    m = env['meta']
    print(f'    carriers({nid.split(":",1)[1][:52]}): '
          f"{m['counts']} total={m['total']}"
          + (f' TRUNCATED={m["truncated"]["total"]}' if m.get('truncated') else ''))
    rows = env.get('results', [])
    # prefer ascendancy notables + uniques in display
    rows_s = sorted(rows, key=lambda r: (
        0 if (r.get('passive_info') or {}).get('ascendancy') else
        1 if r.get('availability') is not None else 2, r['carrier']))
    for r in rows_s[:show]:
        extra = []
        if r.get('availability') is not None:
            extra.append(f"avail={r['availability']}")
        pi = r.get('passive_info')
        if pi and pi.get('ascendancy'):
            extra.append(f"asc={pi['ascendancy']}")
        print(f"      [{r['edge_type'][:4]}] {r['carrier']} name={r.get('name')!r} {' '.join(extra)}")
    if m['total'] > show:
        print(f'      …+{m["total"] - show} more')
    return rows


def neighbour(seed, start, depth=1, direction='in', edge_types=None,
              max_nodes_per_level=200, include_provenance=True):
    filters = {'start': start, 'direction': direction,
               'max_nodes_per_level': max_nodes_per_level,
               'include_provenance': include_provenance}
    if edge_types:
        filters['edge_types'] = edge_types
    env = api.get_neighbour(depth, filters)
    A.log(seed, 'neighbour', {'depth': depth, **filters},
          {'levels': [len(l['edges']) for l in env.get('levels', [])],
           'truncated': env.get('truncated')})
    stats = {}
    roles = {}
    for lv in env.get('levels', []):
        for e in lv['edges']:
            if e['type'].startswith('stat_mechanic'):
                s = e['to'] if e['to'] != start else e['from']
                stats.add(s) if isinstance(stats, set) else None
                pv = e.get('provenance') or {}
                roles[s] = (e['type'].replace('stat_mechanic_', '')
                            + (f":{pv['role']}" if pv.get('role') else ''))
    if stats:
        print(f'    neighbour({start.split(":",1)[1]}): {len(stats)} related stats'
              + (' TRUNCATED' if env.get('truncated') else ''))
        by_role = {}
        for s, r in roles.items():
            by_role.setdefault(r.split(':')[0], []).append(s)
        for role, ids in sorted(by_role.items()):
            print(f'      {role} ({len(ids)}): ' + ', '.join(
                s.split(':', 1)[1] for s in sorted(ids)[:8])
                + ('…' if len(ids) > 8 else ''))
    else:
        for lv in env.get('levels', []):
            for e in lv['edges'][:10]:
                print(f"      {e['type']} {e['from']} -> {e['to']} ({e['direction']})")
    return env


def weapon_check(seed, gem):
    res = feas.weapon_check(gem)
    A.log(seed, 'weapon_check', {'gem': gem}, {'status': res.get('status')})
    print(f'    weapon_check({gem}): {res["status"]}: {res.get("reason", "")[:90]}')
    return res


def can_support(seed, support, skill):
    res = feas.can_support(support, skill)
    A.log(seed, 'can_support', {'support': support, 'skill': skill},
          {'result': res.get('result')})
    print(f'    can_support({support} -> {skill}): {res.get("result")}: '
          f'{res.get("reason", "")[:90]}')
    return res


def validate(seed, state):
    try:
        res = bv.validate_build(state)
    except ValueError as e:
        A.log(seed, 'validate_build',
              {'items': state.get('items'), 'gem_groups': state.get('gem_groups'),
               'passives': state.get('passives')}, {'status': 'input_error'})
        print(f'    VALIDATE items={state.get("items")} gems={[g["skill"] for g in state.get("gem_groups", [])]} '
              f'passives={state.get("passives")}')
        print(f'      -> INPUT ERROR: {e}')
        return {'status': 'input_error', 'reason': str(e)}
    A.log(seed, 'validate_build',
          {'items': state.get('items'), 'gem_groups': state.get('gem_groups'),
           'passives': state.get('passives')}, {'status': res['status']})
    print(f'    VALIDATE items={state.get("items")} gems={[g["skill"] for g in state.get("gem_groups", [])]} '
          f'passives={state.get("passives")}')
    print(f'      -> {res["status"]}: {res["reason"][:220]}')
    return res


if __name__ == '__main__':
    pass
