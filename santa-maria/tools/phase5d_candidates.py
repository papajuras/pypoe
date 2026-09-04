#!/usr/bin/env python3
"""Phase 5D — semantic candidate discovery (regenerable cache, NOT graph data).

Consumes cache/semantic_markers.json (Phase 4M) + the Phase 5S
sem_relation_binds edges in cache/edges.db and materializes candidate records
into cache/sem_candidates.json.

A candidate means ONLY: this node is reachable from a Phase 5S-bound concept
through an explicitly allowed discovery path. It is NOT a relationship claim.

Allowed templates (contract 5D.2, frozen):
  P1a anchor Stat <- *_grants_stat <- carrier      (Stat-anchored bindings only)
  P1b marker Stat <- *_grants_stat <- carrier      (Stat-anchored relations only)
  P2  anchor Tag  <- modifier_has_tag <- Modifier
  P2g anchor Tag  <- gem_has_tag      <- Gem
  P3  anchor Tag  <- modifier_has_tag <- Modifier <- unique_modifier_association <- UniqueItem

Forbidden: modifier_in_group, stat_scales_with, deeper paths, arbitrary walks.
Tag-anchored relations keep the carrier exclusion (no P1 for tags).

Run: python3 tools/phase5d_candidates.py --report   (after phase5s_semantic_bind.py)
"""
import argparse
import hashlib
import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
SANTA = TOOL_DIR.parent
CACHE = SANTA / 'cache'
MARKERS_FILE = CACHE / 'semantic_markers.json'
EDGES_DB = CACHE / 'edges.db'
OUT_FILE = CACHE / 'sem_candidates.json'

CONTRACT_VERSION = '5D.2'
SEM_TYPE = 'sem_relation_binds'
CAP = 5000

ALLOWED_STRUCTURAL = {'modifier_has_tag', 'gem_has_tag', 'unique_modifier_association'}
P3_LAST_HOP = 'unique_modifier_association'
PTYPE_BY_HOP = {'modifier_has_tag': 'P2', 'gem_has_tag': 'P2g', P3_LAST_HOP: 'P3'}
GRANT_TYPES = {'modifier_grants_stat', 'passive_grants_stat', 'gem_grants_stat'}

# anchor role = explicit Phase 4M participant field -> role vocabulary.
# Unknown operator/field falls back to the field name itself (never invented
# semantics); future 5S bindings are driven by the same explicit model.
ROLES = {
    'SUBSTITUTE': {'from': 'displaced_resource', 'to': 'replacement_resource'},
    'CONVERT': {'pool_a': 'conversion_pool', 'pool_b': 'conversion_pool'},
    'SUPPRESS': {'suppressed': 'suppressed_target'},
}

REL_FIELD_RE = re.compile(r'^relation\[(\d+)\]\.(\w+)$')


def js(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def sha256(s):
    return hashlib.sha256(s.encode()).hexdigest()


# ---------------------------------------------------------------------------
# loading
# ---------------------------------------------------------------------------

def load_markers(path=MARKERS_FILE):
    return json.loads(path.read_text())['markers']


def load_sem_edges(edges_db=EDGES_DB):
    """sem_relation_binds edges -> sorted list of {src, tgt, status, facts}."""
    con = sqlite3.connect(f'file:{edges_db}?mode=ro', uri=True)
    rows = con.execute(
        "SELECT source_node_id, target_node_id, confidence_status, provenance "
        "FROM edges WHERE relationship_type=?", (SEM_TYPE,)).fetchall()
    con.close()
    out = []
    for src, tgt, status, prov in rows:
        out.append({'src': src, 'tgt': tgt, 'status': status,
                    'facts': json.loads(prov)})
    return sorted(out, key=js)


def load_reverse_maps(edges_db=EDGES_DB):
    """Reverse adjacency for the three allowed structural classes only:
    {edge_type: {target_node_id: [(source_node_id, status), ...]}}"""
    con = sqlite3.connect(f'file:{edges_db}?mode=ro', uri=True)
    rev = {}
    for t in sorted(ALLOWED_STRUCTURAL):
        m = defaultdict(list)
        for src, tgt, st in con.execute(
                "SELECT source_node_id, target_node_id, confidence_status "
                "FROM edges WHERE relationship_type=?", (t,)):
            m[tgt].append((src, st))
        rev[t] = dict(m)
    con.close()
    return rev


# ---------------------------------------------------------------------------
# discovery (pure)
# ---------------------------------------------------------------------------

def anchor_role(operator, field):
    return ROLES.get(operator, {}).get(field, field)


def nodes_for_anchor(anchor_id, rev):
    """Candidate nodes reachable from one anchor tag, per allowed template.
    Returns ({mod: status}, {gem: status}, {unique: (mod, status)})."""
    mods = dict(rev['modifier_has_tag'].get(anchor_id, []))
    gems = dict(rev['gem_has_tag'].get(anchor_id, []))
    uniqs = {}
    for mod_id in mods:
        for u, st in rev['unique_modifier_association'].get(mod_id, []):
            prev = uniqs.get(u)
            if prev is None or (st, mod_id) < (prev[1], prev[0]):
                uniqs[u] = (mod_id, st)
    return mods, gems, uniqs


def load_reverse_grants(edges_db=EDGES_DB):
    """Reverse *_grants_stat adjacency for P1a/P1b:
    {target_stat_id: [(source_node_id, edge_type, status), ...]}"""
    con = sqlite3.connect(f'file:{edges_db}?mode=ro', uri=True)
    rev = defaultdict(list)
    for t in sorted(GRANT_TYPES):
        for src, tgt, st in con.execute(
                "SELECT source_node_id, target_node_id, confidence_status "
                "FROM edges WHERE relationship_type=?", (t,)):
            rev[tgt].append((src, t, st))
    con.close()
    return dict(rev)


def _candidate_type(node_id):
    return {'mod:': 'Modifier', 'passive:': 'Passive', 'gem:': 'Gem',
            'unique:': 'UniqueItem'}.get(node_id.split(':', 1)[0] + ':', 'Modifier')


def _ptype(path):
    """Discovery-template label for one path (5D.2)."""
    if len(path) == 1:
        return 'P1b'
    h = path[1]['edge_type']
    if h in GRANT_TYPES:
        return 'P1a'
    return PTYPE_BY_HOP[h]


def discover(markers, sem_edges, rev, rev_grants=None, cap=CAP):
    """Returns the full artifact dict (meta.sha256 added by finalize())."""
    if rev_grants is None:
        rev_grants = load_reverse_grants()
    by_sid = {m['sid']: m for m in markers}

    # ---- index 5S facts: (sid, idx, op, field) -> {anchor: (method, status, src)} ----
    anchored = defaultdict(dict)
    invalid = []
    for e in sem_edges:
        for f in e['facts']:
            m = REL_FIELD_RE.match(f.get('field', ''))
            sid = f.get('record_key')
            if (e['src'] != 'stat:' + str(sid) or e['tgt'] != f.get('matched')
                    or m is None):
                invalid.append({'reason': 'provenance/edge mismatch', 'fact': f,
                                'edge': [e['src'], e['tgt']]})
                continue
            marker = by_sid.get(sid)
            if marker is None:
                invalid.append({'reason': 'marker missing', 'sid': sid})
                continue
            idx, field = int(m.group(1)), m.group(2)
            rels = marker.get('relations', [])
            if idx >= len(rels) or rels[idx]['operator'] != f['operator']:
                invalid.append({'reason': 'operator/index mismatch', 'sid': sid,
                                'relation_index': idx, 'operator': f['operator']})
                continue
            anchored[(sid, idx, f['operator'], field)][e['tgt']] = (
                f['method'], e['status'], e['src'])

    # ---- relation summary over ALL 4M relations (silence stays visible) ----
    relation_summary = []
    for marker in sorted(markers, key=lambda m: m['sid']):
        sid = marker['sid']
        for i, rel in enumerate(marker.get('relations', [])):
            op = rel['operator']
            bound = sorted({fld for (s, j, o, fld) in anchored
                            if s == sid and j == i and o == op})
            reason = None
            if marker.get('prose_only') or marker.get('out_of_vocabulary_reason'):
                reason = marker.get('out_of_vocabulary_reason') or 'prose_only'
            elif not bound:
                reason = 'no_binding'
            relation_summary.append({'sid': sid, 'relation_index': i, 'operator': op,
                                     'bound_fields': bound, 'candidates': 0,
                                     **({'reason': reason} if reason else {})})
    summary_by_key = {(r['sid'], r['relation_index'], r['operator']): r
                      for r in relation_summary}

    # ---- walk allowed templates per (relation-instance, anchor) ----
    records = {}
    raw_pairs = 0
    truncated = []
    stat_anchored_rels = set()
    for key in sorted(anchored):
        sid, idx, op, field = key
        rel = by_sid[sid]['relations'][idx]
        rel_fields = rel['fields']
        unc = rel.get('classification_uncertainty')
        for anchor_id in sorted(anchored[key]):
            method, sem_status, sem_src = anchored[key][anchor_id]
            base_path = [{'edge_type': SEM_TYPE, 'from': sem_src, 'to': anchor_id,
                          'direction': 'forward', 'status': sem_status}]
            if anchor_id.startswith('stat:'):
                # P1a — stat-anchored binding discovers carriers via reverse grants
                stat_anchored_rels.add((sid, idx, op))
                reached = [(c, _candidate_type(c), gtype, st)
                           for c, gtype, st in rev_grants.get(anchor_id, [])]
                hop_target = anchor_id
            else:
                mods, gems, uniqs = nodes_for_anchor(anchor_id, rev)
                reached = ([(m, 'Modifier', 'modifier_has_tag', st) for m, st in mods.items()]
                           + [(g, 'Gem', 'gem_has_tag', st) for g, st in gems.items()]
                           + [(u, 'UniqueItem', P3_LAST_HOP, st) for u, (md, st) in uniqs.items()])
                hop_target = anchor_id
            total = len(reached)
            if total > cap:
                truncated.append({'sid': sid, 'relation_index': idx, 'operator': op,
                                  'field': field, 'anchor': anchor_id,
                                  'kept': cap, 'known_total': total})
                reached = reached[:cap]
            raw_pairs += len(reached)
            for node_id, ntype, hop_type, hop_status in reached:
                identity = (sid, idx, op, node_id)
                rec = records.get(identity)
                if rec is None:
                    rec = {'sid': sid, 'relation_index': idx, 'operator': op,
                           'candidate_node_id': node_id, 'candidate_type': ntype,
                           'relation_fields': rel_fields, 'status': 'discovered',
                           'anchors': [], 'paths': []}
                    if unc:
                        rec['classification_uncertainty'] = unc
                    records[identity] = rec
                anchor_entry = {'node_id': anchor_id, 'field': field,
                                'anchor_role': anchor_role(op, field),
                                'method': method, 'binding_status': sem_status,
                                'sem_edge': [sem_src, anchor_id]}
                if anchor_entry not in rec['anchors']:
                    rec['anchors'].append(anchor_entry)
                path = base_path + [{'edge_type': hop_type, 'from': node_id,
                                     'to': hop_target, 'direction': 'reverse',
                                     'status': hop_status}]
                if path not in rec['paths']:
                    rec['paths'].append(path)
                summary_by_key[(sid, idx, op)]['candidates'] += 1

    # ---- P1b: marker-stat carriers for Stat-anchored relations (1-hop) ----
    for (sid, idx, op) in sorted(stat_anchored_rels):
        rel = by_sid[sid]['relations'][idx]
        rel_fields = rel['fields']
        unc = rel.get('classification_uncertainty')
        marker_stat = 'stat:' + sid
        reached = [(c, _candidate_type(c), gtype, st)
                   for c, gtype, st in rev_grants.get(marker_stat, [])]
        total = len(reached)
        if total > cap:
            truncated.append({'sid': sid, 'relation_index': idx, 'operator': op,
                              'field': 'P1b', 'anchor': marker_stat,
                              'kept': cap, 'known_total': total})
            reached = reached[:cap]
        raw_pairs += len(reached)
        for node_id, ntype, hop_type, hop_status in reached:
            identity = (sid, idx, op, node_id)
            rec = records.get(identity)
            if rec is None:
                rec = {'sid': sid, 'relation_index': idx, 'operator': op,
                       'candidate_node_id': node_id, 'candidate_type': ntype,
                       'relation_fields': rel_fields, 'status': 'discovered',
                       'anchors': [], 'paths': []}
                if unc:
                    rec['classification_uncertainty'] = unc
                records[identity] = rec
            path = [{'edge_type': hop_type, 'from': node_id, 'to': marker_stat,
                     'direction': 'reverse', 'status': hop_status}]
            if path not in rec['paths']:
                rec['paths'].append(path)
            summary_by_key[(sid, idx, op)]['candidates'] += 1

    # ---- finalize: deterministic ordering + counts ----
    cand_list = []
    by_op = defaultdict(int)
    by_ptype = defaultdict(int)
    for identity in sorted(records):
        rec = records[identity]
        rec['anchors'].sort(key=js)
        rec['paths'].sort(key=js)
        cand_list.append(rec)
        by_op[rec['operator']] += 1
        for pt in {_ptype(p) for p in rec['paths']}:
            by_ptype[pt] += 1
    silent_ops = sorted({op for op in ('REDIRECT', 'DERIVE', 'EQUAL', 'COUNT_AS')
                         if by_op.get(op, 0) == 0})
    return {
        'contract_version': CONTRACT_VERSION,
        'note': ('Candidate = reachable from a Phase 5S-bound concept through an '
                 'allowed discovery path. NOT a relationship claim. Status is '
                 'always "discovered"; per-hop statuses are preserved verbatim.'),
        'candidates': cand_list,
        'relation_summary': sorted(relation_summary, key=js),
        'meta': {
            'relations_examined': len(relation_summary),
            'bound_relation_instances': len(anchored),
            'candidates_deduped': len(cand_list),
            'candidate_pairs_raw': raw_pairs,
            'candidates_by_operator': dict(sorted(by_op.items())),
            'candidates_by_path_type': dict(sorted(by_ptype.items())),
            'zero_binding_operators': silent_ops,
            'truncated_anchors': truncated,
            'skipped_invalid': invalid,
            'cap': cap,
        },
    }


def finalize(artifact):
    """Content hash over the payload (candidates + relation_summary)."""
    payload = js({'contract_version': artifact['contract_version'],
                  'candidates': artifact['candidates'],
                  'relation_summary': artifact['relation_summary']})
    artifact['meta']['sha256'] = hashlib.sha256(payload.encode()).hexdigest()
    return artifact


def write_artifact(artifact, out=OUT_FILE):
    out.write_text(js(artifact) + '\n')
    return out


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description='Phase 5D semantic candidate discovery')
    ap.add_argument('--report', action='store_true')
    args = ap.parse_args()

    markers = load_markers()
    sem_edges = load_sem_edges()
    rev = load_reverse_maps()
    artifact = finalize(discover(markers, sem_edges, rev))
    write_artifact(artifact)

    if args.report:
        m = artifact['meta']
        print(f"phase5d: relations={m['relations_examined']} bound_instances="
              f"{m['bound_relation_instances']} candidates={m['candidates_deduped']} "
              f"(raw pairs {m['candidate_pairs_raw']})")
        print(f"  by operator: {m['candidates_by_operator']}")
        print(f"  by path type: {m['candidates_by_path_type']}")
        print(f"  silent operators: {m['zero_binding_operators']}")
        print(f"  truncated anchors: {len(m['truncated_anchors'])}  "
              f"invalid: {len(m['skipped_invalid'])}")
        print(f"  sha256: {m['sha256'][:16]}…  -> {OUT_FILE.relative_to(SANTA)}")


if __name__ == '__main__':
    main()