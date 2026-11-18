#!/usr/bin/env python3
"""Phase 4M — opaque-marker semantic extraction per the frozen seven-operator
contract (REDIRECT / SUBSTITUTE / CONVERT / DERIVE / EQUAL / COUNT_AS /
SUPPRESS).

Reads:   cache/nodes.db, cache/raw_records.db (deterministic corpus regen),
         tools/annotations/phase4_semantic_annotations.json (curated ground truth)
Writes:  cache/semantic_markers.json
         docs/phase4_semantic_extraction.md (with --report)

The corpus regenerator recomputes the 202 high-confidence core opaque markers
from the cache (const-1 flag stats with cross-referential translation prose,
excluding league/map / DNT / display categories). The regenerated marker set
MUST equal the committed annotation key set; any drift fails the run.

Semantics: this stage produces the marker SEMANTIC INTERMEDIATE only. Labels
such as "Mana", "Energy Shield", "Strength" are textual semantic labels, not
KB node ids. No graph edges, no candidate pairs, no node resolution.

Usage:
  python3 phase4_markers_extract.py             # regen + validate + emit
  python3 phase4_markers_extract.py --report    # + docs report
"""
import argparse, collections, json, re, sqlite3, sys, time
from pathlib import Path

SANTA = Path(__file__).resolve().parents[1]
CACHE = SANTA / 'cache'
DOCS = SANTA / 'docs'
TOOLS = SANTA / 'tools'
NODES_DB = CACHE / 'nodes.db'
RAW_DB = CACHE / 'raw_records.db'
ANN_PATH = TOOLS / 'annotations' / 'phase4_semantic_annotations.json'
OUT_PATH = CACHE / 'semantic_markers.json'
REPORT_PATH = DOCS / 'phase4_semantic_extraction.md'

CONTRACT_VERSION = 'seven-operator-1.0'
OPERATORS = ['REDIRECT', 'SUBSTITUTE', 'CONVERT', 'DERIVE', 'EQUAL',
             'COUNT_AS', 'SUPPRESS']
UNCERTAINTIES = ['convert-vs-substitute', 'redirect-vs-substitute',
                 'count-as-vs-equal']
EXCLUDE_CATS = {'league/map', 'DNT/disabled', 'display/quality'}

FIELDS = {
    'REDIRECT': {'source', 'target', 'mode', 'factor', 'scope', 'condition', 'polarity'},
    'SUBSTITUTE': {'event', 'from', 'to', 'mode', 'factor', 'probability',
                   'has_magnitude', 'dealt_vs_taken', 'condition', 'order', 'scope'},
    'CONVERT': {'pool_a', 'pool_b', 'fraction', 'extra_factor', 'dealt_vs_taken', 'condition'},
    'DERIVE': {'target', 'source', 'coefficient', 'per_n', 'base_vs_current', 'condition', 'scope'},
    'EQUAL': {'bound_value', 'reference_value', 'axis', 'entity_scope', 'binding',
              'condition', 'source_behavior'},
    'COUNT_AS': {'subject', 'predicate', 'enabling_condition', 'entity_type', 'scope'},
    'SUPPRESS': {'suppressed', 'subject', 'scope', 'condition'},
}

XR = re.compile(
    r'modifiers to|increases and reductions|appl(?:ies|y) to|instead|equal to|'
    r'as well|also affect|also applies|also apply|in place of|count as|converted|'
    r'treated as|damage bonus|provides no|rather than', re.I)


def js(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True)


def load_eng(con):
    """stat id -> set of English translation strings, from raw_records.db."""
    eng = collections.defaultdict(set)
    files = [r[0] for r in con.execute(
        "SELECT DISTINCT source_file FROM raw_records "
        "WHERE source_file LIKE 'repoe/stat_translations%'")]
    for sf in files:
        for (raw,) in con.execute(
                "SELECT raw_json FROM raw_records WHERE source_file=? "
                "AND raw_json LIKE '%\"ids\"%'", (sf,)):
            try:
                rec = json.loads(raw)
            except Exception:
                continue
            ids = rec.get('ids') or []
            if not isinstance(ids, list):
                continue
            for e in rec.get('English') or []:
                if isinstance(e, dict) and e.get('string'):
                    for sid in ids:
                        eng[sid].add(e['string'])
    return eng


def best_text(eng, sid):
    ss = eng.get(sid, [])
    if not ss:
        return ''
    no = [x for x in ss if '#' not in x and '{' not in x]
    pick = no or ss
    # deterministic across process runs: ties broken lexicographically
    return max(pick, key=lambda s: (len(s), s))


def category(sid, text):
    tl = text.lower()
    if '[dnt]' in tl:
        return 'DNT/disabled'
    if (sid.startswith('map_') or sid.startswith('atlas_')
            or 'your maps' in tl or 'in maps' in tl
            or 'found in your maps' in tl):
        return 'league/map'
    if (sid.startswith('display_') or sid.startswith('quality_display_')
            or sid.startswith('local_display_') or sid.startswith('dummy_')):
        return 'display/quality'
    if 'charges' in tl or sid.endswith('_charges_+'):
        return 'charges'
    if any(k in tl for k in ('strength', 'dexterity', 'intelligence', 'attributes')):
        return 'attribute-source redirect'
    if tl.startswith('modifiers to') or tl.startswith('increases and reductions') \
            or 'overcapped' in tl:
        return 'modifier-family redirect'
    if ' instead' in tl:
        return 'instead/substitution'
    if 'count as' in tl or 'counts as' in tl or ' equal to ' in tl:
        return 'count-as/equal-to'
    if any(k in tl for k in ('flask', 'link', 'totem', 'minion', 'aura', 'herald')):
        return 'targeting/aoe redirect'
    return 'other redirect'


def regenerate_corpus(con, nodes_con):
    """Deterministic marker corpus: const-1 flag stats whose translation prose
    is cross-referential, excluding league/map / DNT / display categories."""
    eng = load_eng(con)
    vals = collections.defaultdict(set)
    users = collections.defaultdict(collections.Counter)
    ranged = set()
    for (nid, ntype, payload) in nodes_con.execute(
            "SELECT node_id,type,payload FROM nodes "
            "WHERE type IN ('Passive','Modifier','Gem')"):
        try:
            j = json.loads(payload)
        except Exception:
            continue
        kind = nid.split(':')[0]
        if ntype == 'Passive':
            st = (j.get('shared') or {}).get('stats')
            if isinstance(st, dict):
                for sid, v in st.items():
                    if isinstance(v, (int, float)):
                        vals[sid].add(int(v))
                        users[sid][kind] += 1
        elif ntype == 'Modifier':
            for en in (j.get('stats') or []):
                if not isinstance(en, dict) or not en.get('id'):
                    continue
                sid = en['id']
                users[sid][kind] += 1
                lo, hi = en.get('min'), en.get('max')
                if lo == hi and isinstance(lo, (int, float)):
                    vals[sid].add(int(lo))
                elif lo is not None or hi is not None:
                    ranged.add(sid)
        else:
            for en in ((j.get('static') or {}).get('stats') or []):
                if isinstance(en, dict) and en.get('id') \
                        and isinstance(en.get('value'), (int, float)):
                    sid = en['id']
                    vals[sid].add(int(en['value']))
                    users[sid][kind] += 1
            for lvl, v in (j.get('per_level') or {}).items():
                if not isinstance(v, dict):
                    continue
                for en in (v.get('stats') or []):
                    if isinstance(en, dict) and en.get('id') \
                            and isinstance(en.get('value'), (int, float)):
                        sid = en['id']
                        vals[sid].add(int(en['value']))
                        users[sid][kind] += 1
    flags1 = [s for s, vs in vals.items() if s not in ranged and vs == {1}]
    markers = []
    for sid in sorted(flags1):
        if not any(XR.search(x) for x in eng.get(sid, [])):
            continue
        text = best_text(eng, sid)
        cat = category(sid, text)
        if cat in EXCLUDE_CATS:
            continue
        markers.append({'sid': sid, 'text': text, 'category': cat,
                        'users': dict(users[sid])})
    return markers


def validate_annotation(ann, core_sids):
    issues = []
    if set(ann) != core_sids:
        issues.append('annotation keys != regenerated corpus '
                      f'({len(ann)} vs {len(core_sids)})')
        return issues
    for sid, rec in ann.items():
        if rec['prose_only']:
            if not rec.get('out_of_vocabulary_reason'):
                issues.append(f'{sid}: prose record missing reason')
            continue
        if not rec.get('relations'):
            issues.append(f'{sid}: no relations')
            continue
        for r in rec['relations']:
            op = r.get('operator')
            if op not in OPERATORS:
                issues.append(f'{sid}: unknown operator {op!r}')
                continue
            fields = r.get('fields') or {}
            bad = set(fields) - FIELDS[op]
            if bad:
                issues.append(f'{sid} [{op}]: fields not allowed {sorted(bad)}')
            if op == 'EQUAL' and fields.get('source_behavior') != 'unspecified':
                issues.append(f'{sid}: EQUAL source_behavior must be unspecified')
            if 'order' in fields and op != 'SUBSTITUTE':
                issues.append(f'{sid}: order allowed only on SUBSTITUTE')
            u = r.get('classification_uncertainty')
            if u is not None and u not in UNCERTAINTIES:
                issues.append(f'{sid}: bad uncertainty {u!r}')
    return issues


def build_output(ann, corpus):
    by_sid = {c['sid']: c for c in corpus}
    out = {
        'contract_version': CONTRACT_VERSION,
        'operators': OPERATORS,
        'note': ('Semantic intermediate only. Labels are textual semantic '
                 'labels, not KB node ids. No graph edges emitted.'),
        'markers': [],
    }
    opcount = collections.Counter()
    n_rel = n_unc = 0
    for sid in sorted(ann):
        rec = ann[sid]
        c = by_sid[sid]
        entry = {'sid': sid, 'text': c['text'], 'category': c['category'],
                 'provenance': {'marker_stat_id': sid,
                                'observed_users': c['users']}}
        if rec['prose_only']:
            entry['prose_only'] = True
            entry['out_of_vocabulary_reason'] = rec['out_of_vocabulary_reason']
            entry['relations'] = []
        else:
            entry['prose_only'] = False
            rels = []
            for r in rec['relations']:
                e = {'operator': r['operator'], 'fields': dict(sorted(r['fields'].items()))}
                if 'classification_uncertainty' in r:
                    e['classification_uncertainty'] = r['classification_uncertainty']
                    n_unc += 1
                opcount[r['operator']] += 1
                n_rel += 1
                rels.append(e)
            entry['relations'] = rels
        out['markers'].append(entry)
    out['meta'] = {
        'markers_total': len(out['markers']),
        'relations_total': n_rel,
        'single_relation_markers': sum(1 for m in out['markers']
                                       if not m['prose_only'] and len(m['relations']) == 1),
        'decomposed_markers': sum(1 for m in out['markers']
                                  if not m['prose_only'] and len(m['relations']) > 1),
        'prose_only_markers': sum(1 for m in out['markers'] if m['prose_only']),
        'uncertainty_relations': n_unc,
        'relation_count_by_operator': dict(opcount),
    }
    return out


def write_report(out):
    m = out['meta']
    rows = ['# Phase 4M — Opaque-Marker Semantic Extraction Report', '',
            f'- **Contract**: `{out["contract_version"]}` — '
            f'{" / ".join(out["operators"])}', '',
            '## Validation summary', '',
            f'- Markers total: **{m["markers_total"]}**',
            f'- Semantic relations emitted: **{m["relations_total"]}**',
            f'- Single-relation markers: **{m["single_relation_markers"]}**',
            f'- Decomposed markers: **{m["decomposed_markers"]}**',
            f'- Prose-only / out-of-vocabulary markers: '
            f'**{m["prose_only_markers"]}**',
            f'- Relations carrying classification_uncertainty: '
            f'**{m["uncertainty_relations"]}**', '',
            '## Relation count by operator', '',
            '| operator | count |', '|---|---:|']
    for op in OPERATORS:
        rows.append(f'| {op} | {m["relation_count_by_operator"].get(op, 0)} |')
    rows += ['', '## Prose-only markers', '']
    for mkr in out['markers']:
        if mkr['prose_only']:
            rows.append(f'- `{mkr["sid"]}` — {mkr["out_of_vocabulary_reason"]}')
    REPORT_PATH.write_text('\n'.join(rows) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--report', action='store_true',
                    help='write docs/phase4_semantic_extraction.md')
    ap.add_argument('--ann', default=str(ANN_PATH))
    args = ap.parse_args()
    t0 = time.time()

    nodes_con = sqlite3.connect(NODES_DB)
    raw_con = sqlite3.connect(RAW_DB)
    ann = json.loads(Path(args.ann).read_text())

    corpus = regenerate_corpus(raw_con, nodes_con)
    core = {c['sid'] for c in corpus}
    issues = validate_annotation(ann, core)
    if issues:
        print('ANNOTATION VALIDATION FAILED:')
        for i in issues[:40]:
            print(' -', i)
        sys.exit(1)

    out = build_output(ann, corpus)
    OUT_PATH.write_text(js(out) + '\n')

    report = []
    if args.report:
        write_report(out)
        report.append(f'report: {REPORT_PATH}')
    print(f'OK  markers={out["meta"]["markers_total"]} '
          f'relations={out["meta"]["relations_total"]} '
          f'({time.time()-t0:.1f}s)  -> {OUT_PATH}')
    for r in report:
        print('   ', r)


if __name__ == '__main__':
    main()
