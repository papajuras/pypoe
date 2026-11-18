#!/usr/bin/env python3
"""Phase 5V — semantic candidate validation (results artifact, NOT edges).

Consumes cache/sem_candidates.json (Phase 5D) and validates each candidate
against the candidate's OWN source-backed payload. Read-only over
nodes.db/edges.db. Output: cache/sem_validation_results.json.

Result model (contract 5V.1, three tiers):
  validated            — E1: candidate's payload.stats[] grants the relation's
                         own marker stat (the exact source-backed fact).
  validated_family     — E2: candidate's granted stat ids exhibit the frozen
                         operator morphology with the relation's exact
                         participants (audited vocabulary, direction-verified).
                         Family evidence, NOT proof of the full relation.
  insufficient_evidence — everything else (summarized, not materialized).
  contradicted         — RESERVED; the KB currently contains no derivable
                         negative facts, so this is never emitted.

Frozen rule vocabulary (exhaustive KB audit 2026-09-02):
  displacement constructs: instead_of | in_place_of ; direction is ALWAYS
    <to-resource> ... <indicator> ... <from-resource>  (verified over every
    resource-bearing displacement sid in nodes.db).
  conversion constructs: to_convert_to | added_as ; direction
    <pool_a> ... <construct> ... <pool_b>, pool token sequences matched with
    an optional trailing '_damage' token (audited: '...to_convert_to_chaos',
    '...added_as_fire_damage').
  SUPPRESS/REDIRECT/DERIVE/EQUAL/COUNT_AS: V1 only (SUPPRESS V2 REJECTED —
    measured subject-mismatch false positives).

Uniques compose evidence through their associated modifiers
(unique_modifier_association); every such result carries status_cap
'resolved_not_validated'.

Run: python3 tools/phase5v_validate.py --report   (after phase5d_candidates.py)
"""
import argparse
import hashlib
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
SANTA = TOOL_DIR.parent
CACHE = SANTA / 'cache'
NODES_DB = CACHE / 'nodes.db'
EDGES_DB = CACHE / 'edges.db'
CANDIDATES_FILE = CACHE / 'sem_candidates.json'
OUT_FILE = CACHE / 'sem_validation_results.json'

CONTRACT_VERSION = '5V.1'
GRANT_EDGES = ('modifier_grants_stat', 'passive_grants_stat', 'gem_grants_stat')
UMA = 'unique_modifier_association'

V1 = 'V1'
V2_RULES = {
    'SUBSTITUTE': {
        'constructs': ('instead_of', 'in_place_of'),
        'order': 'to_construct_from',
    },
    'CONVERT': {
        'constructs': ('to_convert_to', 'added_as'),
        'order': 'pool_a_construct_pool_b',
        'optional_trailing_damage': True,
    },
}
V1_ONLY_OPS = ('SUPPRESS', 'REDIRECT', 'DERIVE', 'EQUAL', 'COUNT_AS')
CAP_UMA = 'resolved_not_validated'

RESULT_VALIDATED = 'validated'
RESULT_FAMILY = 'validated_family'
RESULT_INSUFFICIENT = 'insufficient_evidence'
RESULT_CONTRADICTED = 'contradicted'   # reserved; never emitted by current rules


def js(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


# ---------------------------------------------------------------------------
# loading
# ---------------------------------------------------------------------------

def load_candidates(path=CANDIDATES_FILE):
    return json.loads(path.read_text())


def load_payloads(nodes_db=NODES_DB):
    con = sqlite3.connect(f'file:{nodes_db}?mode=ro', uri=True)
    out = {r[0]: json.loads(r[1])
           for r in con.execute("SELECT node_id, payload FROM nodes "
                                 "WHERE type IN ('Modifier', 'Gem', 'UniqueItem')")}
    con.close()
    return out


def load_grant_map(edges_db=EDGES_DB):
    """node -> set of granted stat ids (via *_grants_stat edges)."""
    con = sqlite3.connect(f'file:{edges_db}?mode=ro', uri=True)
    q = ("SELECT source_node_id, target_node_id FROM edges WHERE "
         f"relationship_type IN {GRANT_EDGES}")
    g = defaultdict(set)
    for src, tgt in con.execute(q):
        g[src].add(tgt)
    con.close()
    return g


def load_uma_map(edges_db=EDGES_DB):
    """mod -> [(unique_id, status), ...] (reverse unique_modifier_association)."""
    con = sqlite3.connect(f'file:{edges_db}?mode=ro', uri=True)
    m = defaultdict(list)
    for src, tgt, st in con.execute(
            "SELECT source_node_id, target_node_id, confidence_status FROM edges "
            "WHERE relationship_type=?", (UMA,)):
        m[tgt].append((src, st))
    con.close()
    return m


# ---------------------------------------------------------------------------
# frozen rules (pure functions over granted stat-id lists)
# ---------------------------------------------------------------------------

def _contains_tokens(sid, tokens):
    """Exact token-subsequence containment (no substring/fuzzy)."""
    t = sid.split('_')
    L = len(tokens)
    return any(t[i:i + L] == tokens for i in range(len(t) - L + 1))


def _with_optional_damage(resource, flag):
    toks = resource.split('_')
    variants = [toks]
    if flag and toks[-1] == 'damage':
        variants.append(toks[:-1])
    return variants


def v1_rule(marker_sid, granted):
    return marker_sid in granted


def v2_substitute_rule(granted_stat_ids, from_res, to_res):
    """Granted sid must read <to>...<indicator>...<from> (audited direction)."""
    hits = []
    for s in granted_stat_ids:
        for ind in V2_RULES['SUBSTITUTE']['constructs']:
            if ind not in s:
                continue
            for to_v in _with_optional_damage(to_res, False):
                for from_v in _with_optional_damage(from_res, False):
                    if (_contains_tokens(s, to_res.split('_'))
                            and _contains_tokens(s, from_res.split('_'))):
                        i = s.find(ind)
                        if s.find(to_res.replace('_', ' ')) < 0:
                            pass
                        # direction: to-tokens before indicator, from-tokens after
                        pre, post = s[:i], s[i + len(ind):]
                        pt = '_'.join(pre.split('_'))
                        if _contains_tokens(pre, to_res.split('_')) and \
                           _contains_tokens(post, from_res.split('_')):
                            hits.append(s)
    return sorted(set(hits))


def v2_convert_rule(granted_stat_ids, pool_a, pool_b):
    hits = []
    for s in granted_stat_ids:
        for ind in V2_RULES['CONVERT']['constructs']:
            if ind not in s:
                continue
            pre, post = s.split(ind, 1)
            a_ok = any(_contains_tokens(pre, v) for v in _with_optional_damage(pool_a, True))
            b_ok = any(_contains_tokens(post, v) for v in _with_optional_damage(pool_b, True))
            if a_ok and b_ok:
                hits.append(s)
    return sorted(set(hits))


def _resources_by_role(anchors):
    """{field: resource_token_string} from 5D anchor entries."""
    out = {}
    for a in sorted((x for x in anchors), key=js):
        out.setdefault(a['field'], a['node_id'].split(':', 1)[1])
    return out


# ---------------------------------------------------------------------------
# validation (pure)
# ---------------------------------------------------------------------------

def validate(candidates_artifact, payloads, grant_map, uma_map):
    cands = candidates_artifact['candidates']
    results = []
    insuff = defaultdict(int)
    by_op_rule = defaultdict(int)

    # unique -> associated mod stat union cache
    uniq_cache = {}

    def unique_stats(uid):
        if uid in uniq_cache:
            return uniq_cache[uid]
        mods = sorted(uma_map.get(uid, []))
        stat_sets = {}
        union = set()
        for mod_id, st in mods:
            sids = grant_map.get(mod_id, set())
            stat_sets[mod_id] = sorted(sids)
            union |= sids
        uniq_cache[uid] = (mods, stat_sets, union)
        return uniq_cache[uid]

    for r in sorted(cands, key=js):
        op = r['operator']
        sid = r['sid']
        node = r['candidate_node_id']
        ctype = r['candidate_type']
        v2 = None if op in V1_ONLY_OPS else V2_RULES.get(op)
        marker_stat = 'stat:' + sid

        # candidate-side granted stats
        cap = None
        via_mods = None
        if ctype == 'UniqueItem':
            mods, stat_sets, granted = unique_stats(node)
            if mods:
                cap = CAP_UMA
                via_mods = sorted(stat_sets)
        else:
            granted = grant_map.get(node, set())

        hit = None
        if granted:
            if v1_rule(marker_stat, granted):
                hit = {'rule_id': 'V1', 'evidence_stat_ids': [marker_stat],
                       'result': RESULT_VALIDATED}
            elif v2 and r.get('anchors'):
                roles = {}
                for a in r['anchors']:
                    roles.setdefault(a['field'], a['node_id'].split(':', 1)[1])
                if op == 'SUBSTITUTE' and 'from' in roles and 'to' in roles:
                    ev = v2_substitute_rule(granted, roles['from'], roles['to'])
                    if ev:
                        hit = {'rule_id': 'V2-SUBSTITUTE', 'evidence_stat_ids': ev,
                               'result': RESULT_FAMILY}
                elif op == 'CONVERT' and 'pool_a' in roles and 'pool_b' in roles:
                    ev = v2_convert_rule(granted, roles['pool_a'], roles['pool_b'])
                    if ev:
                        hit = {'rule_id': 'V2-CONVERT', 'evidence_stat_ids': ev,
                               'result': RESULT_FAMILY}
        if hit is None:
            insuff[(op, ctype)] += 1
            continue
        rec = {'sid': sid, 'relation_index': r['relation_index'], 'operator': op,
               'candidate_node_id': node, 'candidate_type': ctype,
               'relation_fields': r['relation_fields'],
               'classification_uncertainty': r.get('classification_uncertainty'),
               'result': hit['result'], 'rule_id': hit['rule_id'],
               'evidence_stat_ids': hit['evidence_stat_ids'],
               'evidence_source': (
                   'payload.stats[] via unique_modifier_association (mods: '
                   + js(via_mods) + ')'
                   if ctype == 'UniqueItem' else 'payload.stats[]'),
               'status_cap': cap,
               'anchors': r['anchors'], 'paths': r['paths'],
               'contract_chain': ['seven-operator-1.0', '5S.1', '5D.1', CONTRACT_VERSION]}
        results.append(rec)
        by_op_rule[(op, hit['rule_id'])] += 1

    by_result = defaultdict(int)
    for rec in results:
        by_result[rec['result']] += 1
    capped = sum(1 for rec in results if rec['status_cap'])
    artifact = {
        'contract_version': CONTRACT_VERSION,
        'note': ('validated = source-backed evidence for the specific marker '
                 'relation; validated_family = source-backed evidence for the '
                 'semantic family only; insufficient_evidence is summarized, '
                 'not materialized. contradicted is reserved (no derivable '
                 'negative facts in the current KB).'),
        'rules': {'V1': 'marker stat granted by candidate payload (or associated mod)',
                  'V2-SUBSTITUTE': 'constructs instead_of|in_place_of, order to..from',
                  'V2-CONVERT': 'constructs to_convert_to|added_as, pool order a..b',
                  'v1_only_operators': list(V1_ONLY_OPS)},
        'results': sorted(results, key=js),
        'meta': {
            'candidates_validated': by_result[RESULT_VALIDATED],
            'candidates_validated_family': by_result[RESULT_FAMILY],
            'candidates_insufficient_evidence': dict(sorted(
                ((f'{op}/{ct}', n) for (op, ct), n in insuff.items()))),
            'insufficient_evidence_total': sum(insuff.values()),
            'by_operator_rule': {f'{op}/{rid}': n
                                 for (op, rid), n in sorted(by_op_rule.items())},
            'status_capped_uma': capped,
        },
    }
    payload = js({'results': artifact['results']})
    artifact['meta']['sha256'] = hashlib.sha256(payload.encode()).hexdigest()
    return artifact


def write_artifact(artifact, out=OUT_FILE):
    out.write_text(js(artifact) + '\n')
    return out


def main():
    ap = argparse.ArgumentParser(description='Phase 5V semantic candidate validation')
    ap.add_argument('--report', action='store_true')
    args = ap.parse_args()

    candidates = load_candidates()
    payloads = load_payloads()
    grant_map = load_grant_map()
    uma_map = load_uma_map()
    artifact = validate(candidates, payloads, grant_map, uma_map)
    write_artifact(artifact)

    if args.report:
        m = artifact['meta']
        print(f"phase5v: validated={m['candidates_validated']} "
              f"validated_family={m['candidates_validated_family']} "
              f"insufficient_evidence={m['insufficient_evidence_total']}")
        print(f"  by operator/rule: {m['by_operator_rule']}")
        print(f"  status-capped (unique composition): {m['status_capped_uma']}")
        print(f"  sha256: {m['sha256'][:16]}…  -> {OUT_FILE.relative_to(SANTA)}")


if __name__ == '__main__':
    main()