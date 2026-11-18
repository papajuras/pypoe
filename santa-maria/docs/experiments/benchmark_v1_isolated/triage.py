#!/usr/bin/env python3
"""Render per-seed triage text from digests (post-processing of API data)."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
D = HERE / 'digests'

SHORT = {
    'unique_modifier_association': 'UMA', 'modifier_grants_stat': 'mgs',
    'passive_grants_stat': 'pgs', 'gem_grants_stat': 'ggs',
    'attribute_grants_stat': 'ags', 'stat_scales_with': 'scales',
    'stat_mechanic_relation': 'smr', 'stat_mechanic_operand': 'smo',
    'stat_mechanic_variant': 'smv', 'gem_has_tag': 'ght',
    'modifier_has_tag': 'mht', 'modifier_in_group': 'mig',
    'unique_in_class': 'uic',
}


def s(x):
    return SHORT.get(x, x)


def base(nid):
    return nid.split(':', 1)[1] if ':' in nid else nid


def main():
    sel = None
    if len(sys.argv) > 1:
        sel = {int(x) for x in sys.argv[1].split(',')}
    for f in sorted(D.glob('digest_*.json')):
        d = json.loads(f.read_text())
        if sel is not None and d['index'] not in sel:
            continue
        out = [f"== {d['index']:02d} {d.get('name') or base(d['node_id'])} "
               f"({d['type']}{'/' + d['availability'] if d['availability'] else ''}) "
               f"flags: {','.join(d['flags']) or '-'}"]
        if d['start_carriers']:
            parts = [f"{s(k)}={v['count']}" for k, v in d['start_carriers'].items()]
            out.append('  IN(carriers of start): ' + ', '.join(parts))
            for k, v in d['start_carriers'].items():
                if v['count'] and k != 'modifier_grants_stat':
                    out.append(f"    {s(k)}: " + '; '.join(
                        (f"{x['name'] or base(x['id'])}"
                         + (f" [{x['asc']}]" if x.get('asc') else '')
                         + (f" (unavail)" if x.get('avail') == 'unavailable' else ''))
                        for x in v['samples'][:6]))
        for lv in d['bfs_levels']:
            e_lines = [e for e in lv['edges'] if '|<' not in e]
            c_lines = [e for e in lv['edges'] if '|<' in e]
            if lv['depth'] == 1 and not e_lines and not c_lines and not lv['groups']:
                out.append(f"  L{lv['depth']}: (no edges)")
            elif lv['depth'] <= 2:
                for e in e_lines[:14]:
                    p = e.split('|')
                    out.append(f"  L{lv['depth']} {s(p[0])} {base(p[1])} -> {base(p[2])} ({p[3]})")
                if len(e_lines) > 14:
                    out.append(f"  L{lv['depth']} …+{len(e_lines)-14} more edges")
                for e in c_lines[:4]:
                    p = e.split('|')
                    out.append(f"  L{lv['depth']} {s(p[0])} {base(p[1])} <- {p[2][1:]}")
            else:
                # level 3: only show out-edges from stats (mech/scales), collapse rest
                keep = [e for e in e_lines
                        if e.split('|')[0] in ('stat_scales_with', 'stat_mechanic_relation',
                                               'stat_mechanic_operand', 'stat_mechanic_variant')
                        or e.split('|')[0].endswith('_grants_stat')]
                for e in keep[:12]:
                    p = e.split('|')
                    out.append(f"  L3 {s(p[0])} {base(p[1])} -> {base(p[2])} ({p[3]})")
                if len(keep) > 12:
                    out.append(f"  L3 …+{len(keep)-12} more stat edges")
            for g in lv['groups']:
                out.append(f"  L{lv['depth']} grp {g['carrier_type']}={g['count']}: "
                           + ', '.join(base(m) for m in g['members'][:6])
                           + ('…' if g['count'] > 6 else ''))
        for ds in d['downstream_stats']:
            out.append(f"  DST {base(ds['stat'])} mech={','.join(ds['mech']) or '-'} "
                       f"fanin_seen={ds['fanin_seen']} via={ds['chain'][:110]}")
        for st, det in (d.get('stat_carriers') or {}).items():
            parts = [f"{s(k)}={v['count']}" for k, v in det['carriers'].items()]
            out.append(f"  A3 {base(st)}: " + ', '.join(parts) if parts else
                       f"  A3 {base(st)}: 0 carriers")
            for k, v in det['carriers'].items():
                if v['count'] and k in ('unique_modifier_association', 'passive_grants_stat',
                                        'gem_grants_stat'):
                    out.append(f"    {s(k)}: " + '; '.join(
                        (f"{x['name'] or base(x['id'])}"
                         + (f" [{x['asc']}]" if x.get('asc') else '')
                         + (f" (unavail)" if x.get('avail') == 'unavailable' else ''))
                        for x in v['samples'][:6]))
        mv = d.get('mechanic_view')
        if mv:
            out.append(f"  MECH {base(mv['mechanic'])}: {mv['related_stats']} related stats"
                       + (' TRUNCATED' if mv['truncated'] else ''))
            out.append('    ' + ' | '.join(
                f"{base(x['stat'])}:{x['role']}" for x in mv['sample'][:14]))
        print('\n'.join(out), flush=True)


if __name__ == '__main__':
    main()
