#!/usr/bin/env python3
"""Phase 4E — literal node extraction per the approved 4D.3 contract.

Reads:   cache/raw_records.db, docs/phase4d_extraction_rules.json (4D.3)
Writes:  cache/nodes.db  (nodes table: node_id | type | origin | payload)

Rules: origin = "source" for every node; derived nodes are NOT produced; no
edges; no semantic inference. Extraction is deterministic: the same raw
snapshot yields identical nodes on every run.

Live-only invariant: unique→modifier association targets (methods 1/4/5) are
emitted only when the mod text is verifiably present in the unique's CURRENT
PoB block; blockless uniques carry no associations. What lands in the KB is
live; the API does no filtering. Vestigial (method 6, alt-quality implicits)
is retired from the KB until separately modelled. Mod families pinned as
unobtainable in tools/sources/unobtainable_mod_families.json (reviewed
classification; the authoritative source is the list itself, not in-graph
evidence) are excluded from node extraction entirely.

Usage:
  python3 extract_nodes.py [--out cache/nodes.db] [--verify] [--dump-hash]
"""
import argparse, hashlib, json, re, sqlite3, sys, time
from pathlib import Path

SANTA = Path(__file__).resolve().parents[1]
CACHE = SANTA / 'cache'
DOCS = SANTA / 'docs'
DEFAULT_DB = CACHE / 'nodes.db'
RAW = CACHE / 'raw_records.db'
CONTRACT_PATH = DOCS / 'phase4d_extraction_rules.json'

NODE_SCHEMA = ['node_id', 'type', 'origin', 'payload']
ORIGIN = 'source'

# node types implemented (must match contract node_types keys; Buff is deferred;
# Rule + Mechanic nodes are created post-hoc by phase5r_rules.py / phase7_consumer_project.py)
NODE_TYPES = ['Stat', 'Modifier', 'ModifierGroup', 'UniqueItem', 'Passive',
              'Gem', 'Tag', 'ItemClass']

UNIQUE_TOKEN_RE = re.compile(r'Unique[A-Za-z0-9_]*')
STRIP_BRACES = re.compile(r'\{[^}]*\}')


def norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())


# ---- Live-only invariant -----------------------------------------------------
# The KB contains only live data: an association target is emitted only when its
# mod text is verifiably present in the unique's CURRENT PoB block (number-
# preserving, formatting-insensitive). Anything unverifiable (no parsed block)
# or text-mismatched (legacy item-version / removed) is dropped at build time;
# the API does no filtering. Vestigial/alt-quality associations (method 6) are
# retired from the KB entirely until separately modelled.

LIVE_GATE_DROPS = {}    # reason -> count, reported by main() after extract_all


def _gate_drop(reason):
    LIVE_GATE_DROPS[reason] = LIVE_GATE_DROPS.get(reason, 0) + 1


# m5 disambiguation diagnostics (whispers04): deterministic fail-closed
# unique->modifier resolution. Counters are global (per process/run) and
# printed next to the live-gate drop report.
M5_DIAG = {}


def _m5_diag(key, n=1):
    M5_DIAG[key] = M5_DIAG.get(key, 0) + n


ALT_QUALITY_PREFIXES = ('Divergent', 'Anomalous', 'Phantasmal')


def live_tokens(s):
    """Tokenize for the liveness gate: RePoE [id|display] markers collapse to
    the display form; decimals canonicalized ('8.00'->'8'); '-'-separated
    number pairs range-ordered ('(60-50)'->'(50-60)'); 'reduced'=='increased'
    (sign lives in the range); trailing 's' stripped (charge/charges); digits
    kept as boundary-safe tokens so '20' never matches '120'."""
    s = (s or '').lower()
    s = re.sub(r'\[[^\]|]*\|([^\]]*)\]', r'\1', s)
    s = re.sub(r'\[[^\]]*\]', ' ', s)
    s = re.sub(r'\d+\.\d+', lambda m: f'{float(m.group(0)):g}', s)
    s = re.sub(r'(\d+)-(\d+)',
               lambda m: '-'.join(sorted(m.groups(), key=int)), s)
    toks = []
    for t in re.split(r'[^a-z0-9]+', s):
        if not t:
            continue
        if t == 'reduced':
            t = 'increased'
        elif len(t) > 3 and t.endswith('s') and not t.isdigit():
            t = t[:-1]
        toks.append(t)
    return tuple(toks)


def _tok_subseq(small, big):
    L = len(small)
    return any(tuple(big[i:i + L]) == small for i in range(len(big) - L + 1))


def live_text_ok(text, lines_tokens):
    """True iff ANY line of the (possibly multi-line) mod text appears
    (token-subsequence) in a current-variant block line — same per-line
    semantics as the m5 template matcher. Empty/missing text can never be
    verified -> not live."""
    for ln in (text or '').split('\n'):
        toks = live_tokens(ln)
        if toks and any(_tok_subseq(toks, lt) for lt in lines_tokens):
            return True
    return False


def js(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True)


def trailing_tier(key):
    m = re.search(r'(\d+)$', key)
    return int(m.group(1)) if m else 0


def load_contract():
    d = json.load(open(CONTRACT_PATH))
    assert str(d.get('contract_version', '')).startswith('4D'), CONTRACT_PATH
    assert set(d['node_types'].keys()) == set(NODE_TYPES), 'contract node_types != implemented'
    assert d['deferred_node_types']['Buff']['extractable_now'] is False
    # node_id prefixes derived from the contract
    prefixes = {}
    for t, c in d['node_types'].items():
        pid = c['node_id'].split(':')[0].split()[0]
        prefixes[t] = pid
    return d, prefixes


UNOBTAINABLE_SRC = SANTA / 'tools' / 'sources' / 'unobtainable_mod_families.json'
_unobtainable_cache = None


def unobtainable_prefixes():
    """Family prefixes excluded from node extraction.

    The pinned reviewed list is the authoritative classification (see the
    JSON's _authority note); in-graph evidence is supporting material only.
    Fail fast if the file is missing or malformed."""
    global _unobtainable_cache
    if _unobtainable_cache is None:
        d = json.load(open(UNOBTAINABLE_SRC))
        fams = d.get('families')
        assert isinstance(fams, list) and fams, UNOBTAINABLE_SRC
        out = tuple(sorted(f['family_prefix'] for f in fams))
        assert all(isinstance(p, str) and p for p in out), UNOBTAINABLE_SRC
        _unobtainable_cache = out
    return _unobtainable_cache


def iter_raw(con, rel):
    """Yield (record_key, parsed_value) for every raw_records row of a source."""
    for rk, rj in con.execute(
            "SELECT record_key, raw_json FROM raw_records WHERE source_file=? ORDER BY record_key", (rel,)):
        yield rk, json.loads(rj)


def iter_like(con, prefix):
    for rk, rj in con.execute(
            "SELECT record_key, raw_json FROM raw_records WHERE source_file LIKE ? ORDER BY record_key", (prefix,)):
        yield rk, json.loads(rj)


def source_files(con, like):
    return [r[0] for r in con.execute(
        "SELECT DISTINCT source_file FROM raw_records WHERE source_file LIKE ? ORDER BY source_file", (like,))]


# ---------------------------------------------------------------------------
# loaders
# ---------------------------------------------------------------------------

def load_mods(con):
    mods = []
    mod_ids = set()
    group_members = {}   # group -> [mod]
    tag_used = {}        # tag -> set('spawn_weights'|'implicit_tags'|'adds_tags')
    tag_count = {}
    key_tokens = {}      # mod key -> set('Unique...' tokens)
    keys = []
    unobtainable = unobtainable_prefixes()
    for k, rec in iter_raw(con, 'repoe/mods.json'):
        if k.startswith(unobtainable):
            # authoritative exclusion: pinned reviewed family list
            # (tools/sources/unobtainable_mod_families.json) — NOT inferred
            # from in-edge counts; those are supporting evidence only.
            _gate_drop('unobtainable_mod_family:' +
                       next(p for p in unobtainable if k.startswith(p)))
            continue
        mods.append((k, rec))
        keys.append(k)
        for s in rec.get('stats', []):
            if isinstance(s, dict) and isinstance(s.get('id'), str):
                mod_ids.add(s['id'])
        for g in rec.get('groups', []):
            group_members.setdefault(g, []).append((k, rec))
        for t in rec.get('spawn_weights', []):
            if isinstance(t, dict) and isinstance(t.get('tag'), str):
                tag = t['tag']
                tag_used.setdefault(tag, set()).add('spawn_weights')
                tag_count[tag] = tag_count.get(tag, 0) + 1
        for t in rec.get('implicit_tags', []):
            if isinstance(t, str):
                tag_used.setdefault(t, set()).add('implicit_tags')
                tag_count[t] = tag_count.get(t, 0) + 1
        for t in rec.get('adds_tags', []):
            if isinstance(t, str):
                tag_used.setdefault(t, set()).add('adds_tags')
                tag_count[t] = tag_count.get(t, 0) + 1
        toks = set(UNIQUE_TOKEN_RE.findall(k))
        if toks:
            key_tokens[k] = toks
    token_index = {}
    for k, toks in key_tokens.items():
        for t in toks:
            token_index.setdefault(t, []).append(k)
    return mods, mod_ids, group_members, tag_used, tag_count, keys, token_index


def load_stats(con):
    canon = {}   # stat_id -> record
    for k, rec in iter_raw(con, 'repoe/stats.json'):
        canon[k] = rec
    return canon


def load_passives(con):
    trees = {}
    for f in source_files(con, 'repoe/passive_skill_trees/%'):
        (rj,) = con.execute("SELECT raw_json FROM raw_records WHERE source_file=? AND record_key=''", (f,)).fetchone()
        trees[f] = json.loads(rj).get('passives', {})
    pkeys = set()
    for pas in trees.values():
        for p in pas.values():
            pkeys.update((p.get('stats') or {}).keys())
    return trees, pkeys


def load_gems(con):
    gems = []
    gem_ids = set()
    for k, rec in iter_raw(con, 'repoe/gems.json'):
        gems.append((k, rec))
        for cs in (rec.get('constant_stats') or []):
            if isinstance(cs, list) and cs and isinstance(cs[0], str):
                gem_ids.add(cs[0])
        for pl in (rec.get('per_level') or {}).values():
            if not isinstance(pl, dict):
                continue
            for x in (pl.get('stats') or []):
                if isinstance(x, dict) and isinstance(x.get('id'), str):
                    gem_ids.add(x['id'])
        for alias, target in ((rec.get('active_skill') or {}).get('stat_conversions') or {}).items():
            if isinstance(target, str):
                gem_ids.add(target)
    return gems, gem_ids


def load_uniques(con):
    return list(iter_raw(con, 'repoe/uniques.json'))


def load_pob_blocks(con):
    name2block = {}
    for f in source_files(con, 'pob/Uniques/%'):
        for _rk, rec in iter_raw(con, f):
            if isinstance(rec, str) and rec.strip():
                first = rec.split('\n', 1)[0].strip()
                if first:
                    name2block.setdefault(first, rec)
    return name2block


# PoB-compatible template resolution (Phase 5.x amendment v5.5, methods 5/6).
# Approved template pools for method-5 promotion (excluded pools are loaded but
# never promotable). See phase5_edge_contract.json v5.5 approved-pool rule.
POB_TEMPLATE_POOLS = [
    'pob/ModItemExclusive.json', 'pob/ModItem.json', 'pob/ModImplicit.json',
    'pob/ModExplicit.json', 'pob/ModJewel.json', 'pob/ModJewelAbyss.json',
    'pob/ModJewelCluster.json', 'pob/ModJewelCharm.json', 'pob/ModFlask.json',
]
POB_CLASS_TOK = ['TwoHandSword', 'TwoHandMace', 'TwoHandAxe', 'OneHandSword',
                 'OneHandMace', 'OneHandAxe', 'ThrustingOneHandSword', 'FishingRod',
                 'Warstaff', 'Body', 'Amulet', 'Belt', 'Boots', 'Bow', 'Claw',
                 'Dagger', 'Flask', 'Gloves', 'Helmet', 'Jewel', 'Quiver', 'Ring',
                 'Shield', 'Staff', 'Tincture', 'Wand']
POB_ICM = {'Amulet': 'Amulet', 'Belt': 'Belt', 'Boots': 'Boots',
           'Body Armour': 'Body', 'Gloves': 'Gloves', 'Helmet': 'Helmet',
           'Ring': 'Ring', 'Shield': 'Shield', 'Bow': 'Bow', 'Claw': 'Claw',
           'Dagger': 'Dagger', 'One Hand Axe': 'OneHandAxe',
           'Two Hand Axe': 'TwoHandAxe', 'One Hand Mace': 'OneHandMace',
           'Two Hand Mace': 'TwoHandMace', 'One Hand Sword': 'OneHandSword',
           'Two Hand Sword': 'TwoHandSword', 'Staff': 'Staff',
           'Warstaff': 'Warstaff', 'Wand': 'Wand', 'Jewel': 'Jewel',
           'Flask': 'Flask', 'Quiver': 'Quiver', 'Fishing Rod': 'FishingRod',
           'Tincture': 'Tincture', 'Thrusting One Hand Sword': 'ThrustingOneHandSword'}
_TAG_RE = re.compile(r'\{[^}]*\}')
_PERN_RE = re.compile(r'\((\d+(?:\.\d+)?)-(?:(\d+(?:\.\d+)?))\)')


def _pob_strip(s):
    return _TAG_RE.sub('', s).strip()


def _pob_skeleton(s):
    s = _PERN_RE.sub('(#-#)', s)
    return re.sub(r'\d+(?:\.\d+)?', '#', s)


def _pob_mod_classes(key):
    """Item-class tokens in a PoB mod key. The class designator follows 'Unique' or
    'Implicit' (e.g. UniqueHelmetStr3 -> Helmet, FireResistImplicitRing1 -> Ring).
    This avoids substring collisions like 'Shield' inside 'EnergyShield'."""
    runs = [m.group(1) for m in re.finditer(r'(?:Unique|Implicit)([A-Z][A-Za-z]*)', key)]
    found = set()
    for run in runs:
        for c in POB_CLASS_TOK:
            if run == c or run.startswith(c) or run.endswith(c):
                found.add(c)
    kept = set()
    for c in sorted(found, key=len, reverse=True):
        if not any(c in o and o != c for o in kept):
            kept.add(c)
    return kept


def load_pob_templates(con):
    """approved pool: stripped template text -> set of mod keys; skeleton index."""
    exact, skel = {}, {}
    for f in POB_TEMPLATE_POOLS:
        for k, rec in iter_raw(con, f):
            if not isinstance(rec, dict):
                continue
            for i in range(1, 9):
                v = rec.get(str(i))
                if isinstance(v, str):
                    t = _pob_strip(v)
                    if t:
                        exact.setdefault(t, set()).add(k)
                        skel.setdefault(_pob_skeleton(t), set()).add(k)
    return exact, skel


def load_base2class(con):
    out = {}
    for _rk, rec in iter_raw(con, 'repoe/base_items.json'):
        if isinstance(rec, dict) and rec.get('name'):
            out.setdefault(rec['name'], rec.get('item_class'))
    return out


def load_moditemexclusive(con):
    rows = list(iter_raw(con, 'pob/ModItemExclusive.json'))
    return rows


def load_baseitem_classes(con):
    classes = set()
    for f in source_files(con, 'repoe/base_items/%'):
        for _rk, rec in iter_raw(con, f):
            if isinstance(rec, dict) and isinstance(rec.get('item_class'), str):
                classes.add(rec['item_class'])
    # repoe/base_items.json root (aggregated base items) also carries item_class
    for _rk, rec in iter_raw(con, 'repoe/base_items.json'):
        if isinstance(rec, dict) and isinstance(rec.get('item_class'), str):
            classes.add(rec['item_class'])
    return classes


def load_item_class_influences(con):
    """item_class category_id -> sorted influence-tag list (repoe/item_classes.json
    influence_tags). None/absent -> empty list. Consumed by extract_item_classes
    (payload enrichment) and by the influence projection (phase5i)."""
    out = {}
    for rk, rec in iter_raw(con, 'repoe/item_classes.json'):
        if isinstance(rec, dict) and isinstance(rk, str):
            tags = rec.get('influence_tags')
            if isinstance(tags, list):
                out[rk] = sorted(t for t in tags if isinstance(t, str))
    return out


# ---- Highest-tier-only mod pruning (whispers08 plan, conservative) ----------
# Invariant the user pinned: pruning may NEVER lose valid mod information.
# A lower-tier member is dropped only when a pruning key is demonstrably
# correct, i.e. ALL of the following hold for a strictly-higher sibling in the
# SAME group + generation_type + domain + influence context:
#   (a) higher required_level (missing level on either side -> never prune),
#   (b) stat-id set of the lower mod is a subset of the higher sibling's
#       (mod_grants_stat coverage is preserved by the survivor),
#   (c) spawn-weight tag set of the lower mod is a subset of the sibling's
#       (spawn-class / influence constraints are preserved),
#   (d) the lower mod's text is NOT referenced by any PoB unique block
#       (normalized-line containment — a SUPERSET of the live-gate per-line
#       token match, so it over-keeps, never under-keeps),
#   (e) generation_type is 'prefix' or 'suffix' — the only contexts where
#       RePoE's group + required_level ladder demonstrably orders tiers.
#       Unique / corrupted / enchantment / delve / crucible / ... mods are
#       per-item bespoke (required_level is not a tier ladder there) and are
#       never pruned,
#   (f) the mod is not referenced by any committed phase-5 contract test case
#       (docs/phase5_test_cases.json) — the regression contract is a KB
#       promise, read data-derived from the pinned JSON, never hand-listed.
# Influence variants never collapse: the influence suffix set is part of the
# key. Every drop is counted and re-derivable deterministically by rerunning
# this pure function over mods.json (tests pin the re-derivation).

TIER_PRUNE_DROPS = {}   # reason -> count (reported by main())
TIER_PRUNE_KEEP = None  # mod keys pinned by the phase-5 regression contract
TIER_PRUNE_DISABLED = False     # audit escape hatch (--no-prune)


def _contract_keep_mods():
    """Mod keys referenced anywhere in the pinned phase-5 test cases (the
    Step 0 regression contract). Data-derived — no hand-maintained list."""
    global TIER_PRUNE_KEEP
    if TIER_PRUNE_KEEP is None:
        import re as _re
        path = DOCS / 'phase5_test_cases.json'
        TIER_PRUNE_KEEP = frozenset(
            m for m in re.findall(r'mod:[A-Za-z0-9_]+', path.read_text()))
    return TIER_PRUNE_KEEP


def _mod_influence_tags(rec):
    """Spawn-weight tags of a mod (strings, weight>0 rows included even at 0 —
    context only; the projection enforces weight>0)."""
    out = set()
    for s in rec.get('spawn_weights') or []:
        if isinstance(s, dict) and isinstance(s.get('tag'), str):
            out.add(s['tag'])
    return out


# ---------------------------------------------------------------------------
# loaders
# ---------------------------------------------------------------------------

def _block_live_index(name2block):
    """[(name, per-line token lists)] for every PoB unique block, plus an
    inverted index alpha-token(len>=4) -> names, for guard (d). Guard (d) is
    authoritative: a mod is kept when live_text_ok() — the EXACT live-gate
    matcher used for association extraction — matches some unique block. The
    inverted index only bounds the candidate set (superset, over-keeps)."""
    per_name = []
    index = {}
    for name, b in (name2block or {}).items():
        lt = [live_tokens(ln) for ln in (b or '').split('\n')]
        lt = [t for t in lt if t]
        per_name.append((name, lt))
        for toks in lt:
            for tok in toks:
                if len(tok) >= 4 and tok.isalpha():
                    index.setdefault(tok, set()).add(name)
    return per_name, index


def prune_lower_tiers(mods, name2block=None, assoc_keys=frozenset()):
    """Pure: [(key, rec), ...] -> (kept, dropped).

    Groups mods by (groups, generation_type, domain, influence-suffix set);
    inside a bucket, a member is dropped only when every guard above holds
    against a strictly higher required_level sibling. All comparisons are
    exact data; any uncertainty keeps the mod (fail-open toward retention).
    """
    kept = list(mods)
    dropped = []                       # (key, reason)
    if not mods:
        return kept, dropped
    # guard (d) machinery: authoritative = the live-gate matcher itself
    per_name, tok_index = _block_live_index(name2block)
    lt_by_name = dict(per_name)
    names_all = list(lt_by_name)

    def live_referenced(text):
        """True when the EXACT live-gate matcher matches some unique block
        (candidates bounded by the alpha-token inverted index; a mod line
        with no indexable token falls back to scanning every block)."""
        lines = [live_tokens(ln) for ln in (text or '').split('\n')]
        lines = [t for t in lines if t]
        if not lines:
            return False
        cand = set()
        for toks in lines:
            for tok in toks:
                if len(tok) >= 4 and tok.isalpha():
                    cand |= tok_index.get(tok, set())
        if not cand:
            cand = names_all
        for name in cand:
            if live_text_ok(text, lt_by_name[name]):
                return True
        return False

    def key_of(k, rec):
        groups = tuple(sorted(g for g in (rec.get('groups') or [])
                              if isinstance(g, str)))
        gen = rec.get('generation_type')
        dom = rec.get('domain')
        infl = frozenset(t.rsplit('_', 1)[1] for t in
                         (s.get('tag') for s in rec.get('spawn_weights') or [])
                         if isinstance(t, str) and '_' in t)
        return (groups, gen, dom, infl)

    def tier_of(rec):
        lv = rec.get('required_level')
        return lv if isinstance(lv, int) else None

    buckets = {}
    for k, rec in kept:
        buckets.setdefault(key_of(k, rec), []).append((k, rec))

    drop = set()
    for _key, members in buckets.items():
        if len(members) < 2:
            continue
        # max tier strictly above each candidate?
        keep_mods = _contract_keep_mods()
        for k_lo, rec_lo in members:
            lv_lo = tier_of(rec_lo)
            if lv_lo is None:
                continue
            if rec_lo.get('generation_type') not in ('prefix', 'suffix'):
                continue        # guard (e): only the tier-ladder contexts
            if f'mod:{k_lo}' in keep_mods:
                continue        # guard (f): regression-contract pin
            if f'mod:{k_lo}' in assoc_keys:
                continue        # guard (g): build-referenced association target
            stats_lo = {s['id'] for s in rec_lo.get('stats') or []
                        if isinstance(s, dict) and isinstance(s.get('id'), str)}
            tags_lo = {s['tag'] for s in rec_lo.get('spawn_weights') or []
                       if isinstance(s, dict) and isinstance(s.get('tag'), str)}
            text_lo = rec_lo.get('text') or ''
            # guard (d): the EXACT live-gate matcher against every candidate
            # unique block — the arbiter the association layer itself uses
            if live_referenced(text_lo):
                continue
            k_hi = None
            for cand_hi, rec_hi in members:
                if cand_hi == k_lo:
                    continue
                lv_hi = tier_of(rec_hi)
                if lv_hi is None or lv_hi <= lv_lo:
                    continue
                stats_hi = {s['id'] for s in rec_hi.get('stats') or []
                            if isinstance(s, dict) and isinstance(s.get('id'), str)}
                if not stats_lo <= stats_hi:
                    continue
                tags_hi = {s['tag'] for s in rec_hi.get('spawn_weights') or []
                           if isinstance(s, dict) and isinstance(s.get('tag'), str)}
                if not tags_lo <= tags_hi:
                    continue
                k_hi = cand_hi
                break
            if k_hi is not None:
                dropped.append((k_lo, k_hi))
                TIER_PRUNE_DROPS['pruned_lower_tier'] = \
                    TIER_PRUNE_DROPS.get('pruned_lower_tier', 0) + 1
    drop_keys = {k for k, _ in dropped}
    kept = [(k, rec) for k, rec in mods if k not in drop_keys]
    return kept, dropped


# ---------------------------------------------------------------------------
# per-type extractors (return (node_id, type, origin, payload_dict))
# ---------------------------------------------------------------------------

def extract_stats(canon, mod_ids, pkeys, gem_ids):
    nodes = []
    positions = [('mods', mod_ids), ('passives', pkeys), ('gems', gem_ids)]
    canonical_ids = set(canon)

    def observed_in(sid):
        out = ['stats_json'] if sid in canonical_ids else []
        for name, s in positions:
            if sid in s:
                out.append(name)
        return out

    def flags(sid, rec, obs_only):
        f = []
        if 'old_do_not_use_' in sid:
            f.append('legacy')
        if 'dummy' in sid:
            f.append('dummy')
        if not obs_only and (rec.get('is_aliased') or (rec.get('alias') or {}).get('when_in_main_hand')
                             or (rec.get('alias') or {}).get('when_in_off_hand')):
            f.append('alias')
        if obs_only:
            f.append('observed_only')
        return sorted(f)

    for sid, rec in canon.items():
        payload = {
            'stat_id': sid,
            'is_local': rec.get('is_local'),
            'is_aliased': rec.get('is_aliased'),
            'alias': rec.get('alias'),
            'flags': flags(sid, rec, False),
            'observed_in': observed_in(sid),
        }
        nodes.append((f'stat:{sid}', 'Stat', ORIGIN, payload))

    # observed-only: ids at the four stat positions not in stats.json
    all_obs = (mod_ids | pkeys | gem_ids) - canonical_ids
    for sid in sorted(all_obs):
        payload = {
            'stat_id': sid,
            'is_local': None,
            'is_aliased': None,
            'alias': None,
            'flags': flags(sid, {}, True),
            'observed_in': observed_in(sid),
        }
        nodes.append((f'stat:{sid}', 'Stat', ORIGIN, payload))
    return nodes


def extract_modifiers(mods):
    return [(f'mod:{k}', 'Modifier', ORIGIN, {'record_key': k, **rec}) for k, rec in mods]


def extract_modifier_groups(mods, group_members, excl, excl_groups):
    nodes = []

    def rep_of(members):
        # members: list of (key, rec). Elevated precedence, then largest
        # trailing-integer tier, then lexicographically smallest key (contract).
        elevated = [(k, m) for k, m in members if 'Elevated' in (m.get('name') or '')]
        pool = elevated or members
        k_rep, m_rep = sorted(pool, key=lambda km: (-trailing_tier(km[0]), km[0]))[0]
        return k_rep, m_rep

    # RePoE vocabulary
    for group in sorted(group_members):
        members = group_members[group]
        _k, rep = rep_of(members)
        payload = {
            'group': group,
            'source_vocab': 'repoe_groups',
            'domains': sorted({m.get('domain') for _k, m in members if m.get('domain') is not None}),
            'generation_types': sorted({m.get('generation_type') for _k, m in members if m.get('generation_type') is not None}),
            'member_count': len(members),
            'representative_text': rep.get('text'),
        }
        nodes.append((f'modgroup:{group}', 'ModifierGroup', ORIGIN, payload))
    # PoB vocabulary (ModItemExclusive.group); no domain/generation_type fields
    for group in sorted(excl_groups):
        members = excl_groups[group]
        _k, rep = rep_of(members)
        payload = {
            'group': group,
            'source_vocab': 'pob_group',
            'domains': [],
            'generation_types': [],
            'member_count': len(members),
            'representative_text': rep.get('text'),
        }
        nodes.append((f'modgroup_pob:{group}', 'ModifierGroup', ORIGIN, payload))
    return nodes


def unique_filter_mod(mod, key):
    """Deterministic unique-mod filter from the contract (method 1):
    generation_type=='unique', non-null text, exclude Royale variants,
    exclude old_do_not_use_* / dummy stat ids."""
    if 'Royale' in key:
        return False
    if mod.get('generation_type') != 'unique':
        return False
    if not mod.get('text'):
        return False
    if any(s.get('id') and (s['id'].startswith('old_do_not_use_') or s['id'].startswith('dummy_'))
           for s in mod.get('stats', [])):
        return False
    return True


def parse_unique_block(block):
    """PoB unique block -> (base_type, current-variant mod lines with {tags:}/{variant:}
    stripped, metadata/header removed, base-type line removed). Deterministic."""
    rest = block.split('\n')[1:]
    base = rest[0] if rest else None
    cur = None
    for ln in rest:
        m = re.search(r'\{variant:([0-9,]+)\}', ln)
        if m:
            nums = [int(x) for x in m.group(1).split(',')]
            cur = max(nums) if cur is None else max(cur, *nums)
    out = []
    for ln in rest[1:]:
        if ln.startswith(('Requires', 'LevelReq', 'Implicits:', 'Variant:', 'Source:',
                          'League:', 'Selected', 'Implicit')):
            continue
        m = re.match(r'\{variant:([0-9,]+)\}', ln)
        if m and cur is not None and cur not in [int(x) for x in m.group(1).split(',')]:
            continue
        t = _pob_strip(ln)
        if t:
            out.append(t)
    return base, out


def resolve_unique_all(uniques, mods_by_key, key_tokens, token_index,
                       mods_text_norm, excl_text_norm, name2block, passive_ids,
                       pob=None):
    results = {}
    key_set = set(mods_by_key)
    pob_exact = (pob or {}).get('exact') or {}
    pob_skel = (pob or {}).get('skel') or {}
    pob_base2class = (pob or {}).get('base2class') or {}
    for ukey, rec in uniques:
        uid = rec.get('id') or ''
        vid = (rec.get('visual_identity') or {}).get('id') or ''
        block = name2block.get(uid)
        is_replica = uid.startswith('Replica ')
        base, lines5 = parse_unique_block(block) if block else (None, [])
        lines5_tokens = [live_tokens(ln) for ln in lines5]
        targets = {}
        evidence = []

        # method 1: vid matching over mods keys with DIGIT-BOUNDARY (a vid must not
        # match merely as a numeric prefix of a longer identifier, e.g.
        # UniqueTwoHandAxe1 must not match UniqueTwoHandAxe10/11/12).
        # Live-only gate: the association is emitted only when the mod's text is
        # verifiably present in the current-variant block; blockless uniques carry
        # no verifiable associations at all.
        m1_keys = []
        if vid:
            cand = set()
            for t, keys in token_index.items():
                if t.startswith(vid):
                    cand.update(keys)
            for k in sorted(cand):
                i = k.find(vid)
                if i < 0:
                    continue
                if k[i + len(vid):i + len(vid) + 1].isdigit():
                    continue
                if unique_filter_mod(mods_by_key[k], k):
                    m1_keys.append(k)
        for k in m1_keys:
            if block is None:
                _gate_drop('m1_blockless')
                continue
            if not live_text_ok(mods_by_key[k].get('text'), lines5_tokens):
                _gate_drop('m1_text')
                continue
            targets[(k, 1)] = {'target_type': 'Modifier', 'target_key': k, 'method': 1,
                               'validated': False, 'status': 'resolved'}
        if m1_keys:
            evidence.append({'method': 1, 'matched_text': None,
                             'candidate_keys': m1_keys, 'validated': False})

        # method 3 (replica -> base inheritance) is REJECTED per contract v5.5.
        # Replicas resolve from their own PoB block (method 5, candidate-only).
        # No code path emits method-3 targets.

        # method 4: passive-grant ("Adds <Name>" effect -> key/pid containing it)
        m4_mod = []
        m4_pass = []
        if block:
            for ln in effect_lines(block, uid):
                m = re.match(r'^Adds\s+(.+)$', ln)
                if not m:
                    continue
                cand = norm(m.group(1))
                if len(cand) < 4:
                    continue
                for k in sorted(key_set):
                    if cand in k.lower():
                        m4_mod.append(k)
                for pid in sorted(passive_ids):
                    if cand in pid.lower():
                        m4_pass.append(pid)
            if m4_mod or m4_pass:
                evidence.append({'method': 4, 'matched_text': block.split('\n')[0],
                                 'candidate_keys': sorted(set(m4_mod)) + sorted(set(m4_pass)),
                                 'validated': False})
        for k in sorted(set(m4_mod)):
            if not live_text_ok(mods_by_key[k].get('text'), lines5_tokens):
                _gate_drop('m4_text')
                continue
            targets[(k, 4)] = {'target_type': 'Modifier', 'target_key': k, 'method': 4,
                               'validated': False, 'status': 'resolved'}
        for pid in sorted(set(m4_pass)):
            targets[(pid, 4)] = {'target_type': 'Passive', 'target_key': pid, 'method': 4,
                                 'validated': False, 'status': 'resolved'}

        # method 2: normalized effect/display-text matching (candidate only)
        if block:
            for ln in effect_lines(block, uid):
                q = norm(ln)
                if len(q) < 14:
                    continue
                ph = q[:24]
                matches = [k for k, nt in mods_text_norm if ph in nt] + \
                          [k for k, nt in excl_text_norm if ph in nt]
                if not matches:
                    continue
                matches = sorted(set(matches))
                evidence.append({'method': 2, 'matched_text': ln,
                                 'candidate_keys': matches, 'validated': False})
                for k in matches:
                    if (k, 2) not in targets:
                        targets[(k, 2)] = {'target_type': 'Modifier', 'target_key': k, 'method': 2,
                                           'validated': False, 'status': 'partial_or_indirect'}

        # method 5: PoB-compatible template matching (contract v5.5).
        # Exact-singleton + approved pool + item-class + non-replica -> resolved.
        # Multi-candidate lines are disambiguated deterministically, fail-closed
        # (whispers04): (a) alt-quality twins (Divergent*/Anomalous*/Phantasmal*)
        # are demoted when a non-alt candidate remains for the same line; (b) a
        # multi-line mod keeps a claiming line only when ANOTHER line of its text
        # also matches a block line that still lists it (cross-line ownership
        # evidence); (c) anything still multi-candidate stays ambiguous — no edge,
        # never guess. Every outcome is counted in M5_DIAG.
        m5 = {}
        line_cands = []
        if block and pob_exact:
            ic = pob_base2class.get(base)
            tok = POB_ICM.get(ic) if ic else None
            for ln in lines5:
                keys = pob_exact.get(ln)
                if keys is None:
                    keys = pob_skel.get(_pob_skeleton(ln))
                if not keys:
                    continue
                if tok:
                    keys = {k for k in keys
                            if not _pob_mod_classes(k) or tok in _pob_mod_classes(k)}
                if keys:
                    line_cands.append((ln, keys, ln in pob_exact))

        def _line_match(t, ln2):
            """Bracket- and number-tolerant line equality (live_tokens
            normalizes [id|display] markers, decimals, ranges, s-plurals)."""
            tt, lt = live_tokens(t), live_tokens(ln2)
            return bool(tt) and tt == lt

        owned_cache = {}

        def _owned(key, claiming_ln):
            """Cross-line ownership evidence: a single-line mod always owns its
            line; a multi-line mod needs one OTHER text line to match a block
            line whose (pre-demotion) candidate set still contains it."""
            if key in owned_cache:
                return owned_cache[key]
            text = ((mods_by_key.get(key) or {}).get('text') or '')
            tlines = [t for t in text.split('\n') if t]
            if len(tlines) <= 1:
                owned_cache[key] = True
                return True
            t_claim = next((t for t in tlines if _line_match(t, claiming_ln)), None)
            others = list(tlines)
            if t_claim is not None:
                others.remove(t_claim)      # first occurrence only
            owned = any(key in keys3 and _line_match(t, ln3)
                        for t in others
                        for ln3, keys3, _ex in line_cands)
            owned_cache[key] = owned
            return owned

        for ln, keys, is_exact in line_cands:
            alts = {k for k in keys if k.startswith(ALT_QUALITY_PREFIXES)}
            demoted_alt = bool(alts) and len(keys) > len(alts)
            kept = keys - alts if demoted_alt else set(keys)
            if demoted_alt:
                _m5_diag('m5_demoted_alt_twin', len(alts))
            if len(kept) > 1:
                # ownership evidence exists only to break ambiguity; sole
                # candidates keep the legacy resolution semantics (their other
                # text lines may be helper lines no item block ever shows)
                pre_own = len(kept)
                kept = {k for k in kept if _owned(k, ln)}
                demoted_ml = pre_own - len(kept)
                if demoted_ml:
                    _m5_diag('m5_demoted_multiline', demoted_ml)
            else:
                demoted_ml = 0
            if len(kept) > 1:
                _m5_diag('m5_ambiguous_lines')
            approved = {k for k in kept if k in mods_by_key
                        and mods_by_key[k].get('generation_type') == 'unique'}
            resolved = (is_exact and len(kept) == 1 and len(approved) == 1
                        and not is_replica)
            kind = 'disambiguated' if (demoted_alt or demoted_ml) else 'exact'
            for k in sorted(kept):
                cur = m5.get(k)
                if resolved:
                    if cur is None or cur['status'] != 'resolved':
                        m5[k] = {'status': 'resolved', 'line': ln, 'kind': kind}
                    # resolved stays resolved; first-resolving line defines kind
                elif cur is None:
                    m5[k] = {'status': 'candidate', 'line': ln}
                    # never downgrade a resolved target to candidate
        for k, info in sorted(m5.items()):
            if info['status'] == 'resolved':
                _m5_diag('m5_resolved_' + info.get('kind', 'exact'))
            else:
                _m5_diag('m5_unresolved_candidates')
        for k, info in sorted(m5.items()):
            targets[(k, 5)] = {'target_type': 'Modifier', 'target_key': k, 'method': 5,
                               'validated': False,
                               'status': 'resolved' if info['status'] == 'resolved'
                               else 'partial_or_indirect',
                               'matched_line': info['line'],
                               'source': 'pob/Uniques/*'}
            if m5:
                evidence.append({'method': 5, 'matched_text': None,
                                 'candidate_keys': sorted(m5), 'validated': False})

        resolved_targets = [targets[k] for k in sorted(targets, key=lambda x: (x[1], x[0]))]

        # node resolution_status
        if any(t['method'] in (1, 4, 5) and t['status'] == 'resolved'
               for t in resolved_targets):
            status = 'resolved'
        elif any(t['status'] == 'partial_or_indirect' for t in resolved_targets):
            status = 'partial_or_indirect'
        elif block is None and not resolved_targets:
            status = 'no_source_text_for_current_method'
        else:
            status = 'unresolved_by_current_resolver'

        results[ukey] = {
            'resolved_targets': resolved_targets,
            'resolution_status': status,
            'resolution_evidence': {'per_association': evidence, 'notes': ''},
        }
    return results


def effect_lines(block, name):
    lines = [ln.strip() for ln in block.split('\n')]
    kept = []
    for i, ln in enumerate(lines):
        if not ln or i == 0:
            continue
        if ln.startswith(('Requires', 'LevelReq', 'Implicits', 'Variant:', 'League:',
                          'Source:', 'Selected ')):
            continue
        kept.append(ln)
    if not kept:
        return []
    eff = []
    for ln in kept[1:]:
        clean = STRIP_BRACES.sub('', ln).strip()
        if clean:
            eff.append(clean)
    return eff


def extract_uniques(uniques, resolver):
    nodes = []
    for key, rec in uniques:
        r = resolver[key]
        payload = {
            'record_key': key,
            'id': rec.get('id'),
            'name': rec.get('name'),
            'item_class': rec.get('item_class'),
            'inventory_width': rec.get('inventory_width'),
            'inventory_height': rec.get('inventory_height'),
            'is_alternate_art': rec.get('is_alternate_art'),
            'visual_identity': rec.get('visual_identity'),
            'base_version': rec.get('base_version'),
            'renamed_version': rec.get('renamed_version'),
            'resolved_targets': r['resolved_targets'],
            'resolution_status': r['resolution_status'],
            'resolution_evidence': r['resolution_evidence'],
        }
        nodes.append((f'unique:{key}', 'UniqueItem', ORIGIN, payload))
    return nodes


def extract_passives(trees):
    nodes = []
    grouped = {}
    for tree, pas in trees.items():
        for h, rec in pas.items():
            grouped.setdefault(rec.get('id'), []).append(
                {'tree': tree, 'hash': rec.get('hash'), 'record': rec})
    for pid in sorted(grouped):
        variants = grouped[pid]
        recs = [v['record'] for v in variants]
        trees_union = sorted([{'file': v['tree'], 'hash': v['hash']} for v in variants],
                             key=lambda x: x['file'])
        same = all(js(recs[0]) == js(r) for r in recs[1:])
        if same:
            rec = recs[0]
            payload = {'id': pid, 'name': rec.get('name'), 'conflict': False,
                       'shared': rec, 'kind_flags': kind_flags_of(rec),
                       'variants': None, 'trees': trees_union}
        else:
            shared = {k: recs[0][k] for k in recs[0]
                      if all(k in r and r[k] == recs[0][k] for r in recs[1:])}
            kf = kind_flags_of(recs[0])
            kf_same = all(kind_flags_of(r) == kf for r in recs[1:])
            payload = {'id': pid, 'name': recs[0].get('name'), 'conflict': True,
                       'shared': shared, 'kind_flags': kf if kf_same else None,
                       'variants': sorted([{'tree': v['tree'], 'hash': v['hash'],
                                            'record': v['record']} for v in variants],
                                          key=lambda x: x['tree']),
                       'trees': trees_union}
        nodes.append((f'passive:{pid}', 'Passive', ORIGIN, payload))
    return nodes


def kind_flags_of(rec):
    return {k: bool(rec.get(k)) for k in
            ('is_keystone', 'is_notable', 'is_jewel_socket',
             'is_ascendancy_starting_node', 'is_multiple_choice')}


def extract_gems(gems):
    return [(f'gem:{k}', 'Gem', ORIGIN, {'record_key': k, **rec}) for k, rec in gems]


def extract_tags(tag_used, tag_count):
    nodes = []
    for tag in sorted(tag_used):
        nodes.append((f'tag:{tag}', 'Tag', ORIGIN, {
            'tag': tag,
            'used_as': sorted(tag_used[tag]),
            'observed_count': tag_count.get(tag, 0),
            'inherits_from': None,
        }))
    return nodes


def extract_item_classes(uniques, base_classes, ic_influences):
    classes = {}
    for _k, rec in uniques:
        if isinstance(rec.get('item_class'), str):
            classes.setdefault(rec['item_class'], set()).add('uniques')
    for c in base_classes:
        classes.setdefault(c, set()).add('base_items')
    nodes = []
    for c in sorted(classes):
        nodes.append((f'item_class:{c}', 'ItemClass', ORIGIN, {
            'item_class': c,
            'observed_from': sorted(classes[c]),
            'influence_tags': list(ic_influences.get(c, [])),
        }))
    return nodes


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def extract_all(con):
    contract, prefixes = load_contract()

    mods, mod_ids, group_members, tag_used, tag_count, mod_keys, token_index = load_mods(con)
    canon = load_stats(con)
    trees, pkeys = load_passives(con)
    gems, gem_ids = load_gems(con)
    uniques = load_uniques(con)
    excl = load_moditemexclusive(con)
    name2block = load_pob_blocks(con)
    base_classes = load_baseitem_classes(con)
    ic_influences = load_item_class_influences(con)

    # PoB-compatible resolution data (contract v5.5, method 5)
    pob_exact, pob_skel = load_pob_templates(con)
    pob = {'exact': pob_exact, 'skel': pob_skel,
           'base2class': load_base2class(con)}
    excl_text_norm = [(k, norm(rec.get('1') or ''))
                      for k, rec in excl if rec.get('1')]
    excl_groups = {}
    for k, rec in excl:
        g = rec.get('group')
        if isinstance(g, str):
            excl_groups.setdefault(g, []).append((k, rec))

    # highest-tier-only pruning (conservative guards; see prune_lower_tiers).
    # The final arbiter is guard (g)+the equivalence self-check below: pruning
    # must preserve the association layer EXACTLY (same resolved targets per
    # unique as the unpruned resolver). Any divergence reverts the whole prune
    # (fail-open toward retention).
    if TIER_PRUNE_DISABLED:
        dropped_tiers = []
        resolver_full = None
    else:
        # resolver over the FULL mod set first: association targets are the
        # authoritative build-time reference set (guard g)
        full_text_norm = [(k, norm(rec.get('text') or ''))
                          for k, rec in mods if rec.get('text')]
        full_token_index = {}
        for k, rec in mods:
            for t in set(UNIQUE_TOKEN_RE.findall(k)):
                full_token_index.setdefault(t, []).append(k)
        resolver_full = resolve_unique_all(
            uniques, {k: rec for k, rec in mods}, None, full_token_index,
            full_text_norm, excl_text_norm, name2block,
            set(pkeys), pob=pob)
        assoc_keys = frozenset(
            t['target_key']
            for r in resolver_full.values()
            for t in r['resolved_targets']
            if t.get('target_type') == 'Modifier')
        mods, dropped_tiers = prune_lower_tiers(mods, name2block, assoc_keys)
    mod_keys = [k for k, _rec in mods]
    token_index = {}
    for k, rec in mods:
        toks = set(UNIQUE_TOKEN_RE.findall(k))
        for t in toks:
            token_index.setdefault(t, []).append(k)
    mods_by_key = {k: rec for k, rec in mods}
    group_members = {}
    tag_used = {}
    tag_count = {}
    for k, rec in mods:
        for g in rec.get('groups') or []:
            group_members.setdefault(g, []).append((k, rec))
        for s in rec.get('spawn_weights') or []:
            if isinstance(s, dict) and isinstance(s.get('tag'), str):
                tag_used.setdefault(s['tag'], set()).add('spawn_weights')
                tag_count[s['tag']] = tag_count.get(s['tag'], 0) + 1
        for t in rec.get('implicit_tags') or []:
            if isinstance(t, str):
                tag_used.setdefault(t, set()).add('implicit_tags')
                tag_count[t] = tag_count.get(t, 0) + 1
        for t in rec.get('adds_tags') or []:
            if isinstance(t, str):
                tag_used.setdefault(t, set()).add('adds_tags')
                tag_count[t] = tag_count.get(t, 0) + 1

    # normalized text for resolver method 2 (mods + ModItemExclusive '1')
    mods_text_norm = [(k, norm(rec.get('text') or '')) for k, rec in mods if rec.get('text')]

    resolver = resolve_unique_all(uniques, mods_by_key, None, token_index,
                                  mods_text_norm, excl_text_norm, name2block,
                                  set(pkeys), pob=pob)

    # equivalence self-check: pruning must preserve the association layer
    # exactly. Any divergence reverts to the full (unpruned) mod set.
    rfull = None
    if not TIER_PRUNE_DISABLED and dropped_tiers and resolver_full is not None:
        rfull = resolver_full
        same = all(
            sorted((t['target_type'], t['target_key'], t['method'])
                   for t in resolver[ukey]['resolved_targets'])
            == sorted((t['target_type'], t['target_key'], t['method'])
                      for t in rfull_u['resolved_targets'])
            for ukey, rfull_u in rfull.items())
        if not same:
            TIER_PRUNE_DROPS['tier_prune_reverted'] = 1
            TIER_PRUNE_DROPS.pop('pruned_lower_tier', None)
            mods, _mod_ids, group_members, _tu, _tc, _mk, token_index = load_mods(con)
            mods_by_key = {k: rec for k, rec in mods}
            mods_text_norm = [(k, norm(rec.get('text') or ''))
                              for k, rec in mods if rec.get('text')]
            resolver = rfull
    del rfull

    nodes = []
    nodes.extend(extract_stats(canon, mod_ids, pkeys, gem_ids))
    nodes.extend(extract_modifiers(mods))
    nodes.extend(extract_modifier_groups(mods, group_members, excl, excl_groups))
    nodes.extend(extract_uniques(uniques, resolver))
    nodes.extend(extract_passives(trees))
    nodes.extend(extract_gems(gems))
    nodes.extend(extract_tags(tag_used, tag_count))
    nodes.extend(extract_item_classes(uniques, base_classes, ic_influences))

    # enforce schema + deterministic order
    for node in nodes:
        assert len(node) == 4
        assert node[2] == ORIGIN
    nodes.sort(key=lambda n: (n[1], n[0]))
    return nodes


def write_db(nodes, out):
    con = sqlite3.connect(out)
    con.execute("CREATE TABLE IF NOT EXISTS nodes (node_id TEXT PRIMARY KEY, type TEXT, origin TEXT, payload TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
    con.execute("DELETE FROM nodes")
    con.execute("DELETE FROM meta")
    con.executemany("INSERT INTO nodes (node_id,type,origin,payload) VALUES (?,?,?,?)",
                    [(nid, typ, origin, js(payload)) for nid, typ, origin, payload in nodes])
    con.execute("INSERT OR REPLACE INTO meta VALUES ('contract_version', ?)", ('4D.3',))
    con.execute("INSERT OR REPLACE INTO meta VALUES ('node_count', ?)", (str(len(nodes)),))
    con.execute("INSERT OR REPLACE INTO meta VALUES ('canonical_hash', ?)", (dump_hash(nodes),))
    counts = {}
    for _nid, typ, _origin, _payload in nodes:
        counts[typ] = counts.get(typ, 0) + 1
    con.execute("INSERT OR REPLACE INTO meta VALUES ('nodes_by_type', ?)", (json.dumps(counts, sort_keys=True),))
    con.commit()
    con.close()


def dump_hash(nodes):
    h = hashlib.sha256()
    for nid, typ, origin, payload in sorted(nodes, key=lambda n: n[0]):
        h.update(nid.encode())
        h.update(b'\0')
        h.update(typ.encode())
        h.update(b'\0')
        h.update(origin.encode())
        h.update(b'\0')
        h.update(js(payload).encode())
        h.update(b'\n')
    return h.hexdigest()


def verify(out):
    con = sqlite3.connect(out)
    tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    assert tables == ['nodes', 'meta'], tables
    cols = [r[1] for r in con.execute("PRAGMA table_info(nodes)")]
    assert cols == NODE_SCHEMA, cols
    total = con.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
    assert total == con.execute("SELECT COUNT(DISTINCT node_id) FROM nodes").fetchone()[0]
    assert con.execute("SELECT COUNT(*) FROM nodes WHERE origin != ?", (ORIGIN,)).fetchone()[0] == 0
    types = [r[0] for r in con.execute("SELECT DISTINCT type FROM nodes ORDER BY type")]
    assert types == sorted(NODE_TYPES), types
    bad = con.execute("SELECT COUNT(*) FROM nodes WHERE json_valid(payload) = 0").fetchone()[0]
    assert bad == 0
    counts = dict(con.execute("SELECT type, COUNT(*) FROM nodes GROUP BY type"))
    con.close()
    return total, counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=str(DEFAULT_DB))
    ap.add_argument('--verify', action='store_true')
    ap.add_argument('--dump-hash', action='store_true')
    ap.add_argument('--no-prune', action='store_true',
                    help='disable highest-tier pruning (audit/derivation aid)')
    args = ap.parse_args()
    global TIER_PRUNE_DISABLED
    TIER_PRUNE_DISABLED = args.no_prune

    t0 = time.time()
    con = sqlite3.connect(RAW)
    nodes = extract_all(con)
    con.close()
    write_db(nodes, args.out)
    elapsed = time.time() - t0

    counts = {}
    for nid, typ, origin, payload in nodes:
        counts[typ] = counts.get(typ, 0) + 1
    print(f"extracted {len(nodes)} nodes -> {args.out} ({elapsed:.1f}s)")
    for t in NODE_TYPES:
        print(f"  {t}: {counts.get(t, 0)}")
    print(f"live-gate dropped association targets: "
          f"{json.dumps(LIVE_GATE_DROPS, sort_keys=True)}")
    print(f"tier-prune dropped lower-tier mods: "
          f"{json.dumps(TIER_PRUNE_DROPS, sort_keys=True)}")
    print(f"m5 disambiguation diagnostics: {json.dumps(M5_DIAG, sort_keys=True)}")
    if args.dump_hash:
        print("canonical_hash:", dump_hash(nodes))
    if args.verify:
        total, vcounts = verify(args.out)
        print(f"verify OK: {total} nodes, types={sorted(vcounts)}")


if __name__ == '__main__':
    sys.exit(main())
