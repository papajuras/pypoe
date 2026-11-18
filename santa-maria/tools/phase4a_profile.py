#!/usr/bin/env python3
"""Phase 4A — raw-snapshot profiling pass (validation/inventory only).

Reads cache/raw_records.db (Phase 2 lossless snapshot) and produces:
  docs/phase4a_profile.json   (machine-readable, one key per source)
  docs/phase4a_summary.md     (human-skim table)

Per source (priority: mods/stats/uniques/passive_skill_trees/gems;
supporting: ModItemExclusive/QueryMods/TradeSiteStats/ModCache):
  1 record_count
  2 distinct values for type/category discriminator fields
  3 naming patterns in id-like fields (token/marker/digit-suffix counts)
  4 every stat_id-like value (deduplicated) with matched_via signal list:
      record_key | field_id | stat_map_key | stat_regex
      (heuristic intentionally unrestricted: tag-like ids such as
      has_attack_mod are included; real-vs-tag is a 4B taxonomy decision)
  5 cross-reference field patterns -> apparent target source
  6 structurally distinct record shapes (grouped + counted)
  7 representative verbatim example records covering the variants
  8 candidate record classes (label-only, no node decisions)

Also checks the full local manifest (417 in-scope files) for files that
are neither priority nor supporting but appear to hold mod/stat/skill/
passive data, and flags them in `unlisted_sources_found` WITHOUT profiling
them in depth.

No network, no data/ reads, no DB/schema/Phase-1-3 changes.
"""
import json, re, sqlite3, sys
from collections import Counter, defaultdict
from pathlib import Path

SANTA = Path(__file__).resolve().parents[1]
CACHE = SANTA / 'cache'
DOCS = SANTA / 'docs'
DB = CACHE / 'raw_records.db'
META_KEY = '_meta'

PRIORITY = ['repoe/mods.json', 'repoe/stats.json', 'repoe/uniques.json', 'repoe/gems.json']
SUPPORTING = ['pob/ModItemExclusive.json', 'pob/QueryMods.json',
              'pob/TradeSiteStats.json', 'pob/ModCache.json']
PASSIVE_FILES = ['repoe/passive_skill_trees/Atlas.json',
                 'repoe/passive_skill_trees/AtlasCurrentLeague.json',
                 'repoe/passive_skill_trees/AtlasEmpty.json',
                 'repoe/passive_skill_trees/BrequelTree.json',
                 'repoe/passive_skill_trees/Default.json',
                 'repoe/passive_skill_trees/DefaultAltAscendancies.json',
                 'repoe/passive_skill_trees/Royale.json']

# stat-id-like heuristic (intentionally broad)
STAT_RE = re.compile(r"^[a-z%][a-z0-9_%+%-]*[a-z0-9_%+%-]$")
MARKERS = ['Unique', 'Implicit', 'Corrupted', 'Influence', 'Maven', 'EaterOfWorlds',
           'SearingExarch', 'Divergent', 'Anomalous', 'Phantasmal', 'Royale', 'Local',
           'Base', 'Crucible', 'Scourge', 'Necropolis', 'Foulborn', 'Graft', 'Tincture',
           'Veiled', 'Synthesis', 'Delve', 'Eldritch', 'WatchersEye', 'Enchantment',
           'Shaping', 'Shaper', 'Elder', 'Abyss', 'Cluster', 'Essence', 'Fossil']


def connect():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def rows_of(con, rel):
    return [json.loads(r['raw_json']) for r in
            con.execute("SELECT raw_json FROM raw_records WHERE source_file=? ORDER BY record_key", (rel,))]


def keys_of(con, rel):
    return [r['record_key'] for r in
            con.execute("SELECT record_key FROM raw_records WHERE source_file=? ORDER BY record_key", (rel,))]


def is_scalar(v):
    return isinstance(v, (int, float, str, bool)) or v is None


def dict_at(rec, path):
    v = rec
    for part in path.split('.'):
        if isinstance(v, dict) and part in v:
            v = v[part]
        else:
            return None
    return v


def field_counter(recs, path):
    c = Counter()
    for r in recs:
        v = dict_at(r, path)
        if isinstance(v, (str, int, float)) and not isinstance(v, bool):
            c[v] += 1
    return dict(c)


def shape_signature(rec):
    if isinstance(rec, dict):
        if len(rec) > 50:
            return f'keyed-map<{len(rec)} keys>'
        return 'dict{' + ','.join(sorted(rec)) + '}'
    if isinstance(rec, list):
        return 'list'
    return type(rec).__name__


def inner_signature(v):
    """Depth-2 structural signature (for ModCache-style heterogeneous values)."""
    def sig(x, d=0):
        if d > 2:
            return type(x).__name__
        if isinstance(x, dict):
            return 'dict{' + ','.join(sorted(x))[:80] + '}'
        if isinstance(x, list):
            inner = sorted({sig(i, d + 1) for i in x[:20]})
            return 'list[' + ','.join(inner) + ']'
        return type(x).__name__
    return sig(v)


def naming_pattern(keys, id_vals=None, n=10):
    toks = Counter()
    digit_suffix = 0
    markers = Counter()
    for k in keys:
        parts = [p for p in re.split(r'(?=[A-Z])', k) if p]
        for p in parts:
            toks[p.lower()] += 1
        if re.search(r'\d+$', k):
            digit_suffix += 1
        for m in MARKERS:
            if m in k:
                markers[m] += 1
    snake = Counter()
    for v in (id_vals or []):
        snake.update(x for x in v.split('_') if x)
    return {
        'camel_tokens_top': toks.most_common(n),
        'digit_suffix_keys': digit_suffix,
        'markers_top': markers.most_common(n),
        'snake_tokens_top': snake.most_common(n),
    }


# stat_id-like signal walker
def stat_signals(records, rkeys=None):
    """Return {value: set(signals)} for every stat_id-like value (unrestricted)."""
    out = defaultdict(set)
    if rkeys:
        for k in rkeys:
            if STAT_RE.match(k):
                out[k].add('record_key')
    for rec in records:
        stack = [(rec, '')]
        while stack:
            v, path = stack.pop()
            if isinstance(v, dict):
                vals = list(v.values())
                numeric_map = bool(vals) and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in vals)
                for k, val in v.items():
                    if isinstance(k, str) and STAT_RE.match(k):
                        out[k].add('stat_regex')
                        if numeric_map:
                            out[k].add('stat_map_key')
                    if k == 'id' and isinstance(val, str) and STAT_RE.match(val):
                        out[val].add('field_id')
                    stack.append((val, f'{path}.{k}' if path else k))
            elif isinstance(v, list):
                for i, x in enumerate(v):
                    stack.append((x, f'{path}[{i}]'))
            elif isinstance(v, str) and STAT_RE.match(v):
                out[v].add('stat_regex')
    return {k: sorted(v) for k, v in out.items()}


def combo_counts(sigmap):
    c = Counter()
    for _v, sigs in sigmap.items():
        c['+'.join(sigs)] += 1
    return dict(c)


def pick_examples(recs, keys_by_idx, selects, fallback_variant=1):
    """Return (record_key, value) examples: preferred selects, then first of
    extra structural variants."""
    out = []
    by_key = dict(zip(keys_by_idx, recs))
    for k in selects:
        if k in by_key:
            out.append((k, by_key[k]))
    if len(out) < 3:
        seen = {shape_signature(v) for _k, v in out}
        for k, v in zip(keys_by_idx, recs):
            sig = shape_signature(v)
            if sig not in seen:
                out.append((k, v))
                seen.add(sig)
            if len(out) >= 3 + max(0, fallback_variant - 1) or len(out) >= 5:
                break
    return out[:5]


def json_dump(o):
    return json.dumps(o, indent=1, ensure_ascii=False, default=str)


def crossref_extract(recs, spec, record_keys=None):
    """spec: list of (label, field, sub, target_guess). `field` is a
    top-level field (or 'record_key'); if the field holds a list of dicts,
    `sub` names the per-element id-ish key; if a dict, its keys are recorded."""
    res = []
    for label, field, sub, target in spec:
        vals = set()
        for r in recs:
            if field == 'record_key':
                continue
            v = r.get(field) if isinstance(r, dict) else None
            if isinstance(v, (str, int, float)) and not isinstance(v, bool):
                vals.add(str(v))
            elif isinstance(v, list):
                for x in v:
                    if sub and isinstance(x, dict) and isinstance(x.get(sub), (str, int, float)):
                        vals.add(str(x[sub]))
                    elif isinstance(x, (str, int, float)) and not isinstance(x, bool):
                        vals.add(str(x))
            elif isinstance(v, dict):
                vals.update(str(k) for k in v)
        if field == 'tradeMod':  # QueryMods: context[modkey] -> slot -> tradeMod
            for r in recs:
                for slot in (r.values() if isinstance(r, dict) else []):
                    tm = slot.get('tradeMod') if isinstance(slot, dict) else None
                    if isinstance(tm, dict) and isinstance(tm.get('id'), str):
                        vals.add(tm['id'])
        if field == 'record_key' and record_keys:
            vals.update(str(k) for k in record_keys)
        if vals:
            res.append({'field': label, 'target_guess': target,
                        'distinct_count': len(vals),
                        'sample': sorted(vals)[:5]})
    return res


# ---------------------------------------------------------------------------
# per-source config
# ---------------------------------------------------------------------------

CONFIG = {
    'repoe/mods.json': {
        'class': 'priority',
        'discriminators': [('generation_type', 'generation_type', []), ('domain', 'domain', []),
                           ('is_essence_only', 'is_essence_only', ['true'])],
        'id_vals_paths': ['type'],
        'crossrefs': [
            ('stats[].id', 'stats', 'id', 'repoe/stats.json'),
            ('spawn_weights[].tag', 'spawn_weights', 'tag', 'tag vocabulary (tags.json / tag_details.json)'),
            ('implicit_tags', 'implicit_tags', None, 'tag vocabulary'),
            ('adds_tags', 'adds_tags', None, 'tag vocabulary'),
            ('groups', 'groups', None, 'internal mod-group vocabulary'),
            ('grants_effects[].granted_effect_id', 'grants_effects', 'granted_effect_id', 'buff/skill ids (buffs.json)'),
        ],
        'examples': ['Strength1', 'LocalIncreasedEnergyShieldUniqueHelmetInt7',
                     'FireResistUniqueHelmetInt7', 'CrucibleTreeNotableSmallPassive'],
        'classes': ['by generation_type', 'by domain'],
    },
    'repoe/stats.json': {
        'class': 'priority',
        'discriminators': [('is_local', 'is_local', ['true']), ('is_aliased', 'is_aliased', ['true']),
                           ('alias.when_in_main_hand', 'alias.when_in_main_hand', ['non-null'])],
        'id_vals_paths': [],
        'crossrefs': [],
        'examples': ['accuracy_rating', 'base_fire_damage_resistance_%', 'strong_casting'],
        'classes': ['flat registry: one stat id per record'],
    },
    'repoe/uniques.json': {
        'class': 'priority',
        'discriminators': [('item_class', 'item_class', []), ('is_alternate_art', 'is_alternate_art', ['true']),
                           ('renamed_version', 'renamed_version', ['non-null'])],
        'id_vals_paths': ['id'],
        'crossrefs': [
            ('item_class', 'item_class', None, 'item_classes.json'),
            ('visual_identity.id', 'visual_identity', 'id', 'mods.json record keys (naming convention)'),
            ('visual_identity.dds_file', 'visual_identity', 'dds_file', 'Art assets'),
        ],
        'examples': ['168', '0'],
        'classes': ['by item_class'],
    },
    'repoe/gems.json': {
        'class': 'priority',
        'discriminators': [('is_support', 'is_support', []), ('color', 'color', []),
                           ('discriminator', 'discriminator', []),
                           ('active_skill.id', 'active_skill.id', []),
                           ('base_item.release_state', 'base_item.release_state', [])],
        'id_vals_paths': ['active_skill.id', 'base_item.id'],
        'crossrefs': [
            ('base_item.id', 'base_item', 'id', 'base_items.json (Metadata path)'),
            ('active_skill.id', 'active_skill', 'id', 'skill id vocabulary'),
            ('active_skill.stat_conversions keys', 'active_skill', 'stat_conversions', 'stat ids (alias map)'),
        ],
        'examples': ['Fireball'],
        'classes': ['active skill vs support (is_support)', 'by gem color'],
    },
    'pob/ModItemExclusive.json': {
        'class': 'supporting',
        'discriminators': [('affix', 'affix', ['non-empty']), ('group', 'group', []), ('level', 'level', [])],
        'id_vals_paths': ['group'],
        'crossrefs': [
            ('tradeHashes keys', 'tradeHashes', None, 'TradeSiteStats explicit.stat_<hash>'),
            ('group', 'group', None, 'PoB mod-group vocabulary'),
            ('statOrder', 'statOrder', None, 'numeric index (PoB stat ordering)'),
        ],
        'examples': ['LocalIncreasedEnergyShieldUniqueHelmetInt7',
                     'SpellDamageModifiersApplyToAttackDamageUniqueHelmetInt7'],
        'classes': ['by group', 'unique/exclusive mods'],
    },
    'pob/QueryMods.json': {
        'class': 'supporting',
        'discriminators': [('top-level context', 'record_key', ['distinct'])],
        'id_vals_paths': [],
        'crossrefs': [
            ('tradeMod.id (nested)', 'tradeMod', 'id', 'TradeSiteStats trade stat ids'),
        ],
        'examples': [],
        'classes': ['per top-level context (Corrupted/Eater/Enchant/Exarch/Explicit/Implicit/PassiveNode/Scourge/WatchersEye)'],
    },
    'pob/TradeSiteStats.json': {
        'class': 'supporting',
        'discriminators': [('id', 'id', []), ('label', 'label', [])],
        'id_vals_paths': ['id', 'label'],
        'crossrefs': [
            ('entries[].id', 'entries', 'id', 'trade stat ids (explicit/pseudo.stat_<hash>) used by QueryMods / ModItemExclusive'),
        ],
        'examples': [],
        'classes': ['by group id (pseudo/explicit/implicit/enchant/...)'],
    },
    'pob/ModCache.json': {
        'class': 'supporting',
        'discriminators': [('value inner shape', 'inner', ['inner_signature'])],
        'id_vals_paths': [],
        'crossrefs': [
            ('record_key', 'record_key', None, 'mod display text (mods.json text / ModItemExclusive)'),
        ],
        'examples': ['Attacks have 150% Arcane Might', ''],
        'classes': ['[null,text] normalized entries vs [[condition-objects]] parsed mods'],
    },
}


def structural_excerpt(v, cap=4000):
    """Reduce an oversized record to a representative excerpt (marked)."""
    s = json.dumps(v, ensure_ascii=False)
    if len(s) <= cap:
        return v, False
    if isinstance(v, dict):
        sub = {}
        for k, val in list(v.items())[:3]:
            sub[k], _ = structural_excerpt(val, max(200, cap // 3))
        return sub, True
    if isinstance(v, list):
        return v[:5], True
    return v, True


def emit_examples(recs, keys, selects):
    out = []
    for k, v in pick_examples(recs, keys, selects):
        val, truncated = structural_excerpt(v)
        e = {'record_key': k, 'value': val}
        if truncated:
            e['truncated'] = True
        out.append(e)
    return out


def profile_source(con, rel, cfg, keys, recs, stat_sig):
    disc = {}
    for item in cfg['discriminators']:
        if len(item) == 3:
            label, path, flag = item
        else:
            label, path = item
            flag = []
        if label == 'top-level context':
            disc[label] = {'distinct': sorted(set(keys))}
        elif flag and flag[0] == 'true':
            c = sum(1 for r in recs if dict_at(r, path) is True)
            disc[label] = {'true_count': c}
        elif flag and flag[0] == 'non-null':
            disc[label] = {'non_null_count': sum(1 for r in recs if dict_at(r, path) is not None)}
        elif label == 'value inner shape':
            disc[label] = dict(Counter(inner_signature(r) for r in recs))
        elif path == 'contexts':
            pass
        else:
            disc[label] = field_counter(recs, path)
    id_vals = set()
    for p in cfg.get('id_vals_paths', []):
        for r in recs:
            v = dict_at(r, p)
            if isinstance(v, str):
                id_vals.add(v)
    shapes = Counter(shape_signature(r) for r in recs)
    xref = crossref_extract(recs, cfg.get('crossrefs', []), keys)
    sigmap = {k: v for k, v in stat_sig.items()}
    return {
        'record_count': len(recs),
        'discriminators': disc,
        'naming_patterns': naming_pattern(keys, sorted(id_vals)),
        'stat_id_like': {
            'distinct_count': len(sigmap),
            'matched_via_combos': combo_counts(sigmap),
            'values': sigmap,
        },
        'cross_references': xref,
        'shapes': dict(shapes),
        'examples': emit_examples(recs, keys, cfg['examples']),
        'candidate_record_classes': cfg['classes'],
    }


MECH_MARKERS = ('generation_type', 'domain', 'stats', 'modTags', 'passives', 'statOrder',
                'tradeHashes', 'spawn_weights', 'generation_weights', 'grants_effects',
                'implicit_tags', 'constant_stats', 'per_level_stats', 'stat_text',
                'stat_conversions', 'active_skill', 'base_item', 'granted_mod',
                'allowed_mods', 'blocked_mods')
MECH_SUB = ('mod', 'stat', 'skill', 'passiv', 'implicit', 'explicit', 'enchant',
            'granted', 'grants', 'spawn')


def has_mechanic_marker(o, depth=0):
    if depth > 3:
        return False
    if isinstance(o, dict):
        for k, v in o.items():
            if any(m in k for m in MECH_SUB):
                return True
            if has_mechanic_marker(v, depth + 1):
                return True
    elif isinstance(o, list):
        return any(has_mechanic_marker(x, depth + 1) for x in o[:20])
    return False


# Curated allowlist: files whose PURPOSE (per Phase 1 report) is mod/stat/skill/
# passive data but whose record structure may not expose mechanical markers
# (e.g. text-block lists, bare registries). OR'd with the structural probe.
NAME_ALLOW = {
    'repoe/mods_by_base.json', 'repoe/mod_types.json', 'repoe/stat_translations.json',
    'repoe/stat_value_handlers.json', 'repoe/stats_by_file.json',
    'repoe/crafting_bench_options.json', 'repoe/essences.json', 'repoe/fossils.json',
    'repoe/cluster_jewels.json', 'repoe/cluster_jewel_notables.json',
    'repoe/default_monster_stats.json', 'repoe/active_skill_types.json',
    'pob/ModScalability.json', 'pob/BossSkills.json', 'pob/Rares.json',
    'pob/Gems.json', 'pob/Essence.json', 'pob/ClusterJewels.json',
    'pob/SkillStatMap.json', 'pob/Minions.json', 'pob/Spectres.json',
    'pob/Pantheons.json', 'pob/TattooPassives.json',
}


def classify_unlisted(con, rel):
    """Light probe of a non-priority/non-supporting file: does it look like it
    holds mod/stat/skill/passive mechanic data? Recursive marker scan + "strong"
    stat-id-like signals (long/multi-segment ids, %/+/-, or values at id /
    stat-map positions), OR the curated name allowlist. Over-flagging borderline
    files is acceptable — the decision is made by the user, not here."""
    recs = [json.loads(r['raw_json']) for r in
            con.execute("SELECT raw_json FROM raw_records WHERE source_file=? LIMIT 200", (rel,))]
    if not recs:
        return False, 'empty (no records)'
    marker = any(has_mechanic_marker(r) for r in recs)
    sig = stat_signals(recs)
    strong = sorted(v for v, sv in sig.items()
                    if sv.count('_') >= 2 or any(ch in v for ch in '%+-')
                    or any(x in sv for x in ('field_id', 'stat_map_key', 'record_key')))
    if marker or strong or rel in NAME_ALLOW:
        why = []
        if rel in NAME_ALLOW:
            why.append('name-allowlisted')
        if marker:
            why.append('marker')
        if strong:
            why.append('statlike: ' + ','.join(strong[:4]))
        return True, '; '.join(why)
    return False, 'no mechanical markers / stat-like ids'


UNLISTED_GUESSES = {
    'mods_by_base.json': 'inverted mod->base index (weights per base)',
    'mod_types.json': 'mod type registry (implicit/explicit eligibility)',
    'stat_translations.json': 'stat id -> display text templates',
    'stat_value_handlers.json': 'stat value display handlers',
    'stats_by_file.json': 'stat id -> referencing source files',
    'buffs.json': 'buffs/debuffs with stat ids',
    'gems_minimal.json': 'reduced gem export',
    'crafting_bench_options.json': 'crafting recipes producing mods',
    'essences.json': 'essences granting mods',
    'fossils.json': 'fossil mod-group weights',
    'cluster_jewel_notables.json': 'cluster notable passives',
    'cluster_jewels.json': 'cluster jewel bases + notables',
    'default_monster_stats.json': 'monster base stats by level',
    'active_skill_types.json': 'active-skill type tags',
}


def one_line_guess(rel):
    base = rel.split('/')[-1]
    if base in UNLISTED_GUESSES:
        return UNLISTED_GUESSES[base]
    if rel.startswith('pob/Mod'):
        return 'PoB mod pool (unprofiled Mod* family)'
    if rel.startswith('repoe/Metadata/Items/'):
        return 'raw item archetype metadata (tags/implicits)'
    if rel.startswith('repoe/base_items/'):
        return 'base-item definitions (implicits/tags)'
    if rel.startswith('repoe/stat_translations/'):
        return 'stat display text per context'
    if rel.startswith('pob/StatDescriptions/'):
        return 'stat display text descriptions'
    return 'possible mod/stat/skill/passive data'


def main():
    con = connect()
    manifest = json.load(open(SANTA / 'data' / 'manifest.json'))
    rels = sorted(r for r in manifest if r != META_KEY)

    profile = {}
    ordered = PRIORITY + PASSIVE_FILES + SUPPORTING
    covered = set(ordered)
    for rel in ordered:
        if rel not in manifest:
            continue
        keys = keys_of(con, rel)
        recs = rows_of(con, rel)
        cfg = CONFIG.get(rel)
        if cfg is None and rel.startswith('repoe/passive_skill_trees/'):
            cfg = {
                'class': 'priority',
                'discriminators': [('is_keystone', 'is_keystone', ['true']),
                                   ('is_notable', 'is_notable', ['true']),
                                   ('is_jewel_socket', 'is_jewel_socket', ['true']),
                                   ('is_ascendancy_starting_node', 'is_ascendancy_starting_node', ['true'])],
                'id_vals_paths': ['id'],
                'crossrefs': [('stats keys', 'stats', None, 'repoe/stats.json'),
                              ('icon', 'icon', None, 'Art assets')],
                'examples': ['50288', '44941'],
                'classes': ['passive nodes (keystone/notable/jewel/ascendancy)'],
            }
        sigs = stat_signals(recs, keys)
        profile[rel] = profile_source(con, rel, cfg, keys, recs, sigs)
        if rel.startswith('repoe/passive_skill_trees/') and recs:
            pas = recs[0].get('passives') or {}
            profile[rel]['tree_flags'] = {
                'passives': len(pas),
                'keystones': sum(1 for p in pas.values() if p.get('is_keystone')),
                'notables': sum(1 for p in pas.values() if p.get('is_notable')),
                'jewel_sockets': sum(1 for p in pas.values() if p.get('is_jewel_socket')),
            }
            sel = [h for h in ('50288', '44941') if h in pas]
            sel += [h for h, p in pas.items() if p.get('is_notable')][:1]
            profile[rel]['examples'] = [{'record_key': h, 'value': pas[h]} for h in sel]

    # ---- unlisted sources check (local manifest only) ----
    unlisted = []
    for rel in rels:
        if rel in covered:
            continue
        is_mech, why = classify_unlisted(con, rel)
        if is_mech:
            unlisted.append({'file': rel, 'guess': one_line_guess(rel),
                             'probe': why, 'why_it_may_matter':
                             'may hold mod/stat/skill/passive data outside the priority/supporting sets'})

    out = {
        '_meta': {
            'generated_from': 'cache/raw_records.db',
            'priority_sources': PRIORITY + PASSIVE_FILES,
            'supporting_sources': SUPPORTING,
            'unlisted_check_scope': f'{len(rels)} in-scope manifest files (local mirror; '
                                    'full upstream tree beyond the mirror is not cached locally)',
        },
        'sources': profile,
        'unlisted_sources_found': unlisted,
    }
    DOCS.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(DOCS / 'phase4a_profile.json', 'w'), indent=1, ensure_ascii=False)

    # ---- summary md ----
    L = ['# Phase 4A — Raw Snapshot Profile (summary)',
         '',
         '| source | records | candidate record classes |',
         '|---|---|---|']
    for rel in ordered:
        if rel not in profile:
            continue
        p = profile[rel]
        L.append(f"| `{rel}` | {p['record_count']} | {', '.join(p['candidate_record_classes'])} |")
    L.append('')
    L.append('## stat_id-like values (counts by matched_via combination)')
    L.append('| source | distinct | by combination |')
    L.append('|---|---|---|')
    for rel in ordered:
        if rel not in profile:
            continue
        p = profile[rel]['stat_id_like']
        combo = '; '.join(f"{k}={v}" for k, v in sorted(p['matched_via_combos'].items()))
        L.append(f"| `{rel}` | {p['distinct_count']} | {combo} |")
    L.append('')
    L.append(f"## Unlisted sources flagged (of {len(rels)} in-scope files)")
    L.append('')
    for u in unlisted:
        L.append(f"- `{u['file']}` — {u['guess']} [{u['probe']}]")
    if not unlisted:
        L.append('- none')
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / 'phase4a_summary.md').write_text('\n'.join(L) + '\n')

    # ---- console result ----
    total = sum(p['record_count'] for p in profile.values())
    print(f"profiled {len(profile)} sources / {total} records; unlisted flagged: {len(unlisted)}")
    for rel in ordered:
        if rel in profile:
            s = profile[rel]['stat_id_like']
            print(f"  {rel}: {profile[rel]['record_count']} recs, statlike={s['distinct_count']} "
                  f"({s['matched_via_combos']})")
    print("wrote docs/phase4a_profile.json, docs/phase4a_summary.md")
    return 0


if __name__ == '__main__':
    sys.exit(main())
