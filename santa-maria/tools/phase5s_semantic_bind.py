#!/usr/bin/env python3
"""Phase 5S — semantic binding extraction (relationship class sem_relation_binds).

Consumes cache/semantic_markers.json (Phase 4M, frozen) and materializes
reference bindings marker-stat -> concept node into cache/edges.db.

sem_relation_binds means ONLY: the Phase 4M participant explicitly refers to
this KB concept. It never asserts interaction. Contract:
docs/phase5s_semantic_binding_contract.json (v5S.1, frozen).

M1_tag:  phrase -> existing Tag node (casefold/underscores/singular; data-gated).
M2_label: phrase -> Stat node by exact unique full-string match against the
         stat_translations English label index.
Every participant outcome is recorded in cache/sem_binding_coverage.json.

Run after phase5_extract_edges.py. Idempotent: deletes its own rows, rewrites
meta under sem_* keys, ensures index idx_edges_target on edges(target_node_id).
"""
import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
SANTA = TOOL_DIR.parent
CACHE = SANTA / 'cache'
DATA = SANTA / 'data'
MARKERS_FILE = CACHE / 'semantic_markers.json'
NODES_DB = CACHE / 'nodes.db'
EDGES_DB = CACHE / 'edges.db'
COVERAGE_FILE = CACHE / 'sem_binding_coverage.json'
TRANSLATIONS_DIR = DATA / 'repoe' / 'stat_translations'
CONTRACT_FILE = SANTA / 'docs' / 'phase5s_semantic_binding_contract.json'

CONTRACT_VERSION = '5S.2'
SEM_TYPE = 'sem_relation_binds'
SEM_TIER = 'outside_this_vocabulary'
SEM_STATUSES = {'confirmed', 'resolved_not_validated'}
MARKERS_SOURCE = 'cache/semantic_markers.json'

PARTICIPANTS = {
    'REDIRECT': ('source', 'target'),
    'SUBSTITUTE': ('from', 'to'),
    'CONVERT': ('pool_a', 'pool_b'),
    'DERIVE': ('source', 'target'),
    'EQUAL': ('bound_value', 'reference_value'),
    'COUNT_AS': ('predicate',),
    'SUPPRESS': ('suppressed',),
}


def js(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True)


# ---------------------------------------------------------------------------
# normalization (frozen: contract 5S.2 resolution_methods)
# ---------------------------------------------------------------------------

def m1_forms(phrase):
    """Tag-key candidate forms, priority order: exact snake_case, singularized."""
    key = ' '.join(phrase.split()).casefold().replace(' ', '_')
    forms = [key]
    if key.endswith('s'):
        forms.append(key[:-1])
    return forms


def m2_key(phrase):
    return ' '.join(phrase.split()).casefold().rstrip(' .,;:')


# M2b stat-grammar: phrase tokens must equal the head of an existing Stat ID,
# with only an approved magnitude-tail remainder. Frozen vocabulary (5S.2).
M2B_TAILS = {'', '+%', '%', '+', 'per_minute', 'per_second'}
M2B_QUANTIFIERS = ('all ',)


def m2b_phrase(phrase):
    """Normalized phrase key for M2b, or None if not a plain concept phrase."""
    p = ' '.join(phrase.split()).casefold().rstrip(' .,;:')
    for q in M2B_QUANTIFIERS:
        if p.startswith(q):
            p = p[len(q):]
    if not p or '#' in p or '{' in p:
        return None
    return '_'.join(p.split())


def m2b_stat(phrase, stat_ids):
    """Unique Stat id whose token head equals the phrase (M2b), else None.
    Ambiguity (>1) and zero matches both return None (caller distinguishes
    via m2b_candidates when the coverage detail matters)."""
    want = m2b_phrase(phrase)
    if want is None:
        return None
    hits = [s for s in stat_ids if s.startswith(want) and s[len(want):].strip('_') in M2B_TAILS]
    return hits[0] if len(hits) == 1 else None


def m2b_candidates(phrase, stat_ids):
    """All tail-OK matches for coverage reporting (0 = unresolved, >1 = ambiguous)."""
    want = m2b_phrase(phrase)
    if want is None:
        return []
    return [s for s in stat_ids if s.startswith(want) and s[len(want):].strip('_') in M2B_TAILS]


# ---------------------------------------------------------------------------
# lookups
# ---------------------------------------------------------------------------

def load_tags(nodes_db=NODES_DB):
    con = sqlite3.connect(f'file:{nodes_db}?mode=ro', uri=True)
    tags = {r[0][4:] for r in con.execute("SELECT node_id FROM nodes WHERE type='Tag'")}
    con.close()
    return tags


def load_stat_ids(nodes_db=NODES_DB):
    con = sqlite3.connect(f'file:{nodes_db}?mode=ro', uri=True)
    ids = [r[0][5:] for r in con.execute("SELECT node_id FROM nodes WHERE type='Stat'")]
    con.close()
    return ids


def load_node_ids(nodes_db=NODES_DB):
    con = sqlite3.connect(f'file:{nodes_db}?mode=ro', uri=True)
    ids = {r[0] for r in con.execute('SELECT node_id FROM nodes')}
    con.close()
    return ids


def build_label_index(translations_dir=TRANSLATIONS_DIR):
    """normalized full string -> set of (stat_id, file). Placeholders excluded."""
    index = {}
    for path in sorted(translations_dir.glob('*.json')):
        d = json.loads(path.read_text())
        entries = d if isinstance(d, list) else d.get('data', [])
        for e in entries:
            ids = e.get('ids') or []
            for eng in e.get('English', []):
                s = eng.get('string')
                if not s or '#' in s or '{' in s:
                    continue
                k = m2_key(s)
                if k:
                    index.setdefault(k, set()).update((i, path.name) for i in ids)
    return index


def resolve_participant(phrase, tags, label_index, stat_ids=()):
    """Returns (outcome, target_id_or_ids, detail).

    outcome in {'M1_tag', 'M2b_stat', 'M2_label', 'unresolved', 'ambiguous',
    'placeholder'}. Precedence: M1_tag -> M2b_stat -> M2_label.
    """
    if '#' in phrase or '{' in phrase:
        return ('placeholder', None, 'value template, not a concept')
    for form in m1_forms(phrase):
        if form in tags:
            kind = 'exact' if form == m1_forms(phrase)[0] else 'singular'
            return ('M1_tag', 'tag:' + form, kind)
    if stat_ids:
        cand = m2b_candidates(phrase, stat_ids)
        if len(cand) == 1:
            return ('M2b_stat', 'stat:' + cand[0], 'stat-grammar')
        if len(cand) > 1:
            return ('ambiguous', sorted('stat:' + c for c in cand),
                    f'{len(cand)} stats match the stat-grammar head')
    k = m2_key(phrase)
    hits = label_index.get(k)
    if hits:
        ids = sorted({sid for sid, _ in hits})
        if len(ids) == 1:
            return ('M2_label', 'stat:' + ids[0], {'label_file': sorted(hits)[0][1]})
        return ('ambiguous', ids, f'{len(ids)} stats share the label')
    return ('unresolved', None, 'no tag node, no unique label')


# ---------------------------------------------------------------------------
# binding extraction (pure; no DB writes)
# ---------------------------------------------------------------------------

def extract_bindings(markers, tags, label_index, node_ids, stat_ids=()):
    """Returns (edges, coverage). edges keyed (src, tgt, type) with merged prov."""
    edges = {}
    cov_rows = []
    counts = {'participants_total': 0, 'bound_m1': 0, 'bound_m2b': 0, 'bound_m2': 0,
              'unresolved': 0, 'placeholder': 0, 'ambiguous': 0,
              'prose_only': 0, 'partial_binding_dropped': 0, 'bindings_before_dedup': 0}

    def add_row(sid, i, f, op, phrase, outcome, detail, target=None):
        r = {'sid': sid, 'relation_index': i, 'field': f, 'operator': op,
             'phrase': phrase, 'outcome': outcome, 'detail': detail}
        if target:
            r['target'] = target
        cov_rows.append(r)

    for marker in sorted(markers, key=lambda m: m['sid']):
        sid = marker['sid']
        src = 'stat:' + sid
        if marker.get('prose_only') or marker.get('out_of_vocabulary_reason'):
            reason = marker.get('out_of_vocabulary_reason') or 'prose_only'
            for i, rel in enumerate(marker.get('relations', [])):
                counts['prose_only'] += 1
                for f in PARTICIPANTS.get(rel['operator'], ()):
                    add_row(sid, i, f, rel['operator'], rel['fields'].get(f, ''),
                            'prose_only', reason)
            continue
        assert src in node_ids, f'marker stat node missing: {src}'
        for i, rel in enumerate(marker.get('relations', [])):
            op = rel['operator']
            fields = rel['fields']
            reqs = PARTICIPANTS[op]
            results = {}
            for f in reqs:
                counts['participants_total'] += 1
                phrase = fields.get(f, '')
                outcome, target, detail = resolve_participant(phrase, tags, label_index, stat_ids)
                results[f] = (outcome, target, detail)
                add_row(sid, i, f, op, phrase, outcome, detail, target)
                if outcome == 'M1_tag':
                    counts['bound_m1'] += 1
                elif outcome == 'M2b_stat':
                    counts['bound_m2b'] += 1
                elif outcome == 'M2_label':
                    counts['bound_m2'] += 1
                elif outcome == 'unresolved':
                    counts['unresolved'] += 1
                elif outcome == 'placeholder':
                    counts['placeholder'] += 1
                else:
                    counts['ambiguous'] = counts.get('ambiguous', 0) + 1
            failed = [f for f in reqs if results[f][0] not in ('M1_tag', 'M2b_stat', 'M2_label')]
            if len(reqs) > 1 and failed:
                counts['partial_binding_dropped'] += 1
                add_row(sid, i, '', op, '', 'partial_binding_dropped', f'unbound: {failed}')
                continue
            for f in reqs:
                outcome, target, detail = results[f]
                if outcome not in ('M1_tag', 'M2b_stat', 'M2_label'):
                    continue
                unc = rel.get('classification_uncertainty')
                status = ('resolved_not_validated'
                          if (unc or outcome in ('M2b_stat', 'M2_label')) else 'confirmed')
                fact = {'source_file': MARKERS_SOURCE, 'record_key': sid,
                        'source_version': 'seven-operator-1.0',
                        'field': f'relation[{i}].{f}', 'operator': op,
                        'relation_fields': fields, 'phrase': fields.get(f, ''),
                        'normalized': m2_key(fields.get(f, '')), 'method': outcome,
                        'matched': target}
                if outcome == 'M1_tag':
                    fact['form'] = detail
                elif outcome == 'M2b_stat':
                    fact['form'] = 'stat-grammar'
                else:
                    fact['label_file'] = detail['label_file']
                if unc:
                    fact['classification_uncertainty'] = unc
                merge_edge(edges, {'src': src, 'tgt': target, 'type': SEM_TYPE,
                                   'status': status, 'secondary': None,
                                   'tier': 'outside_this_vocabulary', 'prov': [fact]})
                counts['bindings_before_dedup'] += 1
    cov_rows.sort(key=js)
    return edges, {'contract_version': CONTRACT_VERSION, 'summary': counts,
                   'participants': cov_rows}


def merge_edge(edges, e):
    key = (e['src'], e['tgt'], e['type'])
    if key in edges:
        for f in e['prov']:
            if f not in edges[key]['prov']:
                edges[key]['prov'].append(f)
        edges[key]['prov'].sort(key=js)
        return
    e['prov'] = sorted(e['prov'], key=js)
    edges[key] = e


# ---------------------------------------------------------------------------
# validation + write
# ---------------------------------------------------------------------------

def canonical_hash(edges):
    import hashlib
    h = hashlib.sha256()
    for e in sorted(edges.values(), key=lambda x: (x['src'], x['tgt'])):
        h.update(e['src'].encode()); h.update(b'\0')
        h.update(e['tgt'].encode()); h.update(b'\0')
        h.update(e['type'].encode()); h.update(b'\0')
        h.update(e['status'].encode()); h.update(b'\0')
        h.update((e['tier'] or '').encode()); h.update(b'\0')
        h.update(js(e['prov']).encode()); h.update(b'\n')
    return h.hexdigest()


def write_db(edges, node_ids, edges_db=EDGES_DB):
    for e in edges.values():
        assert e['src'] in node_ids, f'source node missing: {e["src"]}'
        assert e['tgt'] in node_ids, f'target node missing: {e["tgt"]}'
        assert e['src'].startswith('stat:'), e['src']
        assert e['tgt'].startswith(('tag:', 'stat:')), e['tgt']
        assert e['status'] in SEM_STATUSES
    con = sqlite3.connect(edges_db)
    have = con.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='edges'").fetchone()[0]
    if not have:
        con.close()
        raise SystemExit('edges table missing — run phase5_extract_edges.py first')
    con.execute('CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_node_id)')
    con.execute("DELETE FROM edges WHERE relationship_type=?", (SEM_TYPE,))
    rows = sorted(edges.values(), key=lambda x: (x['src'], x['tgt']))
    con.executemany(
        "INSERT INTO edges (source_node_id,target_node_id,relationship_type,"
        "confidence_status,secondary_status,tier,provenance) VALUES (?,?,?,?,?,?,?)",
        [(e['src'], e['tgt'], e['type'], e['status'], None, e['tier'], js(e['prov']))
         for e in rows])
    by_type = {SEM_TYPE: len(rows)}
    con.execute("INSERT OR REPLACE INTO meta VALUES ('sem_contract_version',?)", (CONTRACT_VERSION,))
    con.execute("INSERT OR REPLACE INTO meta VALUES ('sem_edge_count',?)", (str(len(rows)),))
    con.execute("INSERT OR REPLACE INTO meta VALUES ('sem_edges_by_type',?)", (js(by_type),))
    con.execute("INSERT OR REPLACE INTO meta VALUES ('sem_canonical_hash',?)", (canonical_hash(edges),))
    con.commit()
    con.close()
    return len(rows)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description='Phase 5S semantic binding extraction')
    ap.add_argument('--report', action='store_true', help='print summary')
    args = ap.parse_args()

    markers = json.loads(MARKERS_FILE.read_text())
    tags = load_tags()
    stat_ids = load_stat_ids()
    node_ids = load_node_ids()
    label_index = build_label_index()
    edges, coverage = extract_bindings(markers['markers'], tags, label_index, node_ids, stat_ids)
    n = write_db(edges, node_ids, EDGES_DB)
    COVERAGE_FILE.write_text(js(coverage) + '\n')

    if args.report:
        s = coverage['summary']
        print(f"phase5s: markers={len(markers['markers'])} sem_relation_binds edges written: {n}")
        print(f"  participants: {s['participants_total']}  M1_tag: {s['bound_m1']}  "
              f"M2_label: {s['bound_m2']}  unresolved: {s['unresolved']}  "
              f"placeholder: {s['placeholder']}  prose_only: {s.get('prose_only', 0)}  "
              f"dropped(partial): {s['partial_binding_dropped']}")
        print(f"  coverage: {COVERAGE_FILE.relative_to(SANTA)}")


if __name__ == '__main__':
    main()