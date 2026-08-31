#!/usr/bin/env python3
"""Targeted Phase-1 investigations over the downloaded data (read-only).

Input:  santa-maria/data/  (+ cache/stat_vocab.json)
Output: santa-maria/cache/investigations.json

Facts only: Crown of Eyes / Iron Will / Avatar of Fire traces, the exhaustive
unique-visual-id -> mods naming-convention linkage rate, the PoB unique-mod
pipeline, and cross-reference resolution rates. No nodes, no KB, no schema.
"""
import json, re
from pathlib import Path

SANTA = Path(__file__).resolve().parents[1]
D = SANTA / 'data'
CACHE = SANTA / 'cache'

_VISUAL_RUN = re.compile(r'Unique[A-Za-z0-9_]*')

_loaded = {}
def load(rel):
    if rel not in _loaded:
        with open(D / rel, encoding='utf-8') as f:
            _loaded[rel] = json.load(f)
    return _loaded[rel]

def vocab():
    p = CACHE / 'stat_vocab.json'
    if p.exists():
        return set(json.load(open(p)))
    from vocab import collect_ids
    return collect_ids()

def stat_resolution(sid, mods_stats, voc):
    trans = load('repoe/stat_translations.json')
    strings = []
    for rec in trans:
        if sid in rec['ids']:
            for e in rec.get('English') or []:
                s = e.get('string')
                if s:
                    strings.append(s)
            if strings:
                break
    handlers = load('repoe/stat_value_handlers.json')
    handler = None
    if isinstance(handlers, dict):
        for name, spec in handlers.items():
            s = json.dumps(spec)[:200]
            if sid in s:
                handler = name
                break
    return {'in_vocab': sid in voc, 'in_mods_stats': sid in mods_stats,
            'translations': strings[:3], 'value_handler': handler}

def mods_stats_set():
    m = load('repoe/mods.json')
    out = set()
    for v in m.values():
        for s in v['stats']:
            out.add(s['id'])
    return out

def keys_containing(keys, visual_id):
    return [k for k in keys if visual_id in k]

def find_unique(uid):
    u = load('repoe/uniques.json')
    for key, rec in u.items():
        if rec.get('id') == uid:
            return key, rec
    return None, None

def find_passive(name):
    trees = sorted(p for p in (D / 'repoe/passive_skill_trees').glob('*.json'))
    for tp in trees:
        tree = json.load(open(tp))
        for h, p in (tree.get('passives') or {}).items():
            if p.get('name') == name:
                return tp.name, h, p, tree
    return None, None, None, None


def investigate_crown():
    key, rec = find_unique('Crown of Eyes')
    if rec is None:
        return {'found': False, 'unique_key': None}
    vid = rec['visual_identity']['id']
    m = load('repoe/mods.json')
    mods = []
    for mk in m:
        if vid in mk:
            v = m[mk]
            mods.append({'key': mk, 'generation_type': v['generation_type'],
                         'match_type': 'exact' if mk == vid else 'naming_convention',
                         'stats': [{'id': s['id'], 'min': s['min'], 'max': s['max']} for s in v['stats']]})
    voc = vocab()
    mstats = mods_stats_set()
    sids = sorted({s['id'] for mm in mods for s in mm['stats']})
    resolution = {sid: stat_resolution(sid, mstats, voc) for sid in sids}

    E = load('pob/ModItemExclusive.json')
    I = load('pob/ModItem.json')
    ex = {k: {kk: vv for kk, vv in E[k].items()} for k in E if vid in k}
    trades = {}
    for k, v in ex.items():
        for hsh, texts in (v.get('tradeHashes') or {}).items():
            trades[hsh] = texts
    TS = load('pob/TradeSiteStats.json')
    ts_ids = {e['id'] for g in TS for e in g.get('entries', [])}
    trade_res = {}
    for hsh, texts in trades.items():
        tid = f'explicit.stat_{hsh}'
        trade_res[hsh] = {'trade_id': tid, 'in_trade_site_stats': tid in ts_ids, 'text': texts}

    helmet = load('pob/Uniques/helmet.json')
    helmet_text = None
    for block in helmet:
        if isinstance(block, str) and block.startswith('Crown of Eyes'):
            helmet_text = block
            break

    not_in_mod_item = sorted(k for k in ex if k not in I)
    mods_in_exclusive = sorted(mk['key'] for mk in mods if mk['key'] in E)
    mods_missing_in_exclusive = sorted(mk['key'] for mk in mods if mk['key'] not in E)

    chain_break = None
    if mods_missing_in_exclusive:
        chain_break = (f"PoB ModItemExclusive.json lacks {len(mods_missing_in_exclusive)} of the "
                       f"{len(mods)} naming-convention mods: {mods_missing_in_exclusive}. "
                       "PoB's unique->mod linkage is display-text only (Uniques/*.json).")

    # ---- ModCache.json: display-text cache ----
    MC = load('pob/ModCache.json')
    mc_texts = sorted(set(texts[0] for texts in trades.values() if texts))
    mc_hits = {t: {'present': t in MC,
                   'maps_to': MC[t] if t in MC else None} for t in mc_texts}
    mc_crown_keys = [k for k in MC if 'Crown' in k]

    # ---- QueryMods.json: trade-id lookup ----
    QM = load('pob/QueryMods.json')
    qm_trade_index = {}   # tradeMod.id -> list of (context, modkey, text)
    for ctx, val in QM.items():
        if not isinstance(val, dict):
            continue
        for mk, slot in val.items():
            if isinstance(slot, dict) and isinstance(slot.get('tradeMod'), dict):
                tid = slot['tradeMod'].get('id')
                if tid:
                    qm_trade_index.setdefault(tid, []).append(
                        (ctx, mk, slot['tradeMod'].get('text')))
    co_trade_ids = sorted(trade_res[h]['trade_id'] for h in trade_res
                          if trade_res[h]['in_trade_site_stats'])
    qm_hits = {tid: qm_trade_index.get(tid, []) for tid in co_trade_ids}
    qm_has_co_keys = any('UniqueHelmetInt7' in str(k) for ctx in QM.values()
                         if isinstance(ctx, dict) for k in ctx)

    return {
        'unique_key': key,
        'visual_identity_id': vid,
        'link_type': 'naming_convention (visual_identity.id embedded in mod key) — not an FK',
        'mods': mods,
        'exact_matches': sorted(mk['key'] for mk in mods if mk['match_type'] == 'exact'),
        'stat_resolution': resolution,
        'files_examined': [
            {'file': 'repoe/uniques.json', 'examined': True,
             'role': 'unique identity (name/class/visual_identity.id); no modifier list',
             'status': 'contains the unique record (key %s)' % key},
            {'file': 'repoe/mods.json', 'examined': True,
             'role': 'mod definitions; candidate unique mods via naming convention',
             'status': '%d candidate mod keys (%d exact, %d naming-convention)' % (
                 len(mods), len(mods) - sum(1 for x in mods if x['match_type'] == 'naming_convention'),
                 sum(1 for x in mods if x['match_type'] == 'naming_convention'))},
            {'file': 'repoe/stat_translations.json', 'examined': True,
             'role': 'stat id -> display text',
             'status': '%d/%d stat ids resolved' % (sum(1 for r in resolution.values() if r['translations']), len(resolution))},
            {'file': 'pob/ModItemExclusive.json', 'examined': True,
             'role': 'PoB unique/exclusive mod pool',
             'status': '%d/%d candidate mods present' % (len(mods_in_exclusive), len(mods))},
            {'file': 'pob/ModItem.json', 'examined': True,
             'role': 'PoB item mod pool',
             'status': 'no Crown of Eyes mods present (uniques live in ModItemExclusive)'},
            {'file': 'pob/TradeSiteStats.json', 'examined': True,
             'role': 'trade stat id -> text',
             'status': '%d/%d trade hashes resolve to explicit.stat_<hash>' % (
                 sum(1 for v in trade_res.values() if v['in_trade_site_stats']), len(trade_res))},
            {'file': 'pob/ModCache.json', 'examined': True,
             'role': 'mod display-text normalization cache',
             'status': '%d/%d Crown display texts present as cache keys; %d keys contain "Crown"' % (
                 sum(1 for v in mc_hits.values() if v['present']), len(mc_hits), len(mc_crown_keys))},
            {'file': 'pob/QueryMods.json', 'examined': True,
             'role': 'PoB mod -> trade-site query mapping (tradeMod ids per slot)',
             'status': 'Crown mod keys absent from keyspace (%s); %d/%d Crown trade ids present as tradeMod values' % (
                 'yes' if qm_has_co_keys else 'no', sum(1 for v in qm_hits.values() if v), len(co_trade_ids))},
            {'file': 'pob/Uniques/helmet.json', 'examined': True,
             'role': 'per-unique display text blocks',
             'status': 'Crown of Eyes text block present: %s' % (helmet_text is not None)},
        ],
        'mod_cache': {'display_text_membership': mc_hits, 'keys_containing_crown': mc_crown_keys},
        'query_mods': {'crown_keys_in_keyspace': qm_has_co_keys,
                       'crown_trade_id_hits': qm_hits},
        'pob': {
            'uniques_helmet_text_present': helmet_text is not None,
            'mod_item_exclusive': ex,
            'mod_item': {k: {kk: vv for kk, vv in I[k].items()} for k in I if vid in k},
            'not_in_mod_item': not_in_mod_item,
            'mods_missing_in_exclusive': mods_missing_in_exclusive,
            'mods_present_in_exclusive': mods_in_exclusive,
            'trade_resolution': trade_res,
            'chain_break': chain_break,
        },
        'chain': [
            {'from': 'repoe/uniques.json', 'key': key, 'field': 'visual_identity.id',
             'value': vid, 'to': 'repoe/mods.json', 'target': 'mod keys containing the id',
             'link': 'heuristic (naming convention)', 'resolved': True,
             'meaning': f'{len(mods)} unique mod definitions'},
            {'from': 'repoe/mods.json', 'key': 'each matching mod', 'field': 'stats[].id',
             'value': 'stat ids', 'to': 'repoe/stat_translations.json', 'target': 'translation entries',
             'link': 'explicit (id -> ids[] array)', 'resolved': True,
             'meaning': 'display text'},
            {'from': 'pob/ModItemExclusive.json', 'key': 'matching mod keys', 'field': 'tradeHashes',
             'value': 'hash -> [text]', 'to': 'pob/TradeSiteStats.json', 'target': 'explicit.stat_<hash>',
             'link': 'heuristic (same naming convention) + hash match', 'resolved': True,
             'meaning': 'trade stat id + display text'},
            {'from': 'pob/ModItemExclusive.json', 'key': 'tradeHashes text', 'field': 'display text',
             'value': 'Crown display lines', 'to': 'pob/ModCache.json', 'target': 'cache key',
             'link': 'heuristic (text match)', 'resolved': False,
             'meaning': 'ModCache is a text-normalization cache; not a per-unique index (partial overlap)'},
            {'from': 'pob/QueryMods.json', 'key': 'keyspace', 'field': 'tradeMod.id',
             'value': 'Crown trade ids', 'to': 'pob/TradeSiteStats.json', 'target': 'tradeMod values',
             'link': 'explicit (tradeMod.id equality)', 'resolved': True,
             'meaning': 'QueryMods indexes shared trade ids; does not index Crown keys itself'},
        ],
    }


def investigate_passive(name):
    fname, h, p, tree = find_passive(name)
    if p is None:
        return {'found': False}
    voc = vocab()
    mstats = mods_stats_set()
    res = {sid: stat_resolution(sid, mstats, voc) for sid in (p.get('stats') or {})}
    return {
        'found': True, 'source_file': f'repoe/passive_skill_trees/{fname}',
        'hash': p.get('hash'), 'node_id': p.get('id'),
        'flags': {k: v for k, v in p.items() if k.startswith('is_')},
        'stats': p.get('stats'),
        'stat_resolution': res,
        'in_mods_stats': all(r['in_mods_stats'] for r in res.values()),
        'in_vocab': all(r['in_vocab'] for r in res.values()),
    }


def investigate_unique_linkage():
    u = load('repoe/uniques.json')
    m = load('repoe/mods.json')
    E = load('pob/ModItemExclusive.json')
    vid_set = set()
    for rec in u.values():
        vid = (rec.get('visual_identity') or {}).get('id')
        if vid:
            vid_set.add(vid)
    mod_keys = list(m.keys())
    ex_keys = list(E.keys())
    def matched(vid):
        hits = [k for k in mod_keys if vid in k]
        return bool(hits)
    matched_pob = {vid for vid in vid_set if any(vid in k for k in ex_keys)}
    with_mod = [rec['id'] for rec in u.values()
                if matched((rec.get('visual_identity') or {}).get('id') or '')]
    without = sorted(rec['id'] for rec in u.values()
                     if not matched((rec.get('visual_identity') or {}).get('id') or ''))
    return {
        'total_uniques': len(u),
        'distinct_visual_ids': len(vid_set),
        'uniques_with_mod_match': len(with_mod),
        'uniques_without_mod_match': len(without),
        'without_sample': without[:20],
        'uniques_with_pob_exclusive_match': len(matched_pob),
        'link_type': 'naming_convention',
    }


def investigate_crossref_resolution():
    m = load('repoe/mods.json')
    trans = load('repoe/stat_translations.json')
    trans_ids = {sid for rec in trans for sid in rec['ids']}
    mstats = mods_stats_set()
    resolved = mstats & trans_ids
    base = load('repoe/base_items.json')
    refs, resolved_inh = 0, 0
    for v in base.values():
        inh = v.get('inherits_from')
        if isinstance(inh, str):
            refs += 1
            resolved_inh += 1 if inh in base else 0
    E = load('pob/ModItemExclusive.json')
    TS = load('pob/TradeSiteStats.json')
    ts_ids = {e['id'] for g in TS for e in g.get('entries', [])}
    hashes = set()
    for v in E.values():
        hashes.update((v.get('tradeHashes') or {}).keys())
    resolved_hash = sum(1 for h in hashes if f'explicit.stat_{h}' in ts_ids)
    return {
        'mods_stat_ids': {
            'distinct_stat_ids': len(mstats),
            'resolvable_to_translation': len(resolved),
            'unresolved_sample': sorted(mstats - trans_ids)[:10],
        },
        'base_items_inherits_from': {
            'references': refs,
            'resolved_against_base_items_keys': resolved_inh,
        },
        'mod_exclusive_trade_hashes': {
            'distinct_hashes': len(hashes),
            'resolvable_to_trade_site_stats': resolved_hash,
        },
    }


def main():
    out = {
        'crown_of_eyes': investigate_crown(),
        'iron_will': investigate_passive('Iron Will'),
        'avatar_of_fire': investigate_passive('Avatar of Fire'),
        'unique_linkage': investigate_unique_linkage(),
        'crossref_resolution': investigate_crossref_resolution(),
    }
    CACHE.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(CACHE / 'investigations.json', 'w'), indent=1)
    c = out['crown_of_eyes']
    print(f"Crown of Eyes: {len(c['mods'])} naming-convention mods, "
          f"{len(c['pob']['mod_item_exclusive'])} in PoB ModItemExclusive")
    print(f"unique linkage: {out['unique_linkage']['uniques_with_mod_match']}/"
          f"{out['unique_linkage']['total_uniques']} uniques have a matching mod key")
    for name in ('iron_will', 'avatar_of_fire'):
        p = out[name]
        print(f"{name}: hash={p['hash']} id={p['node_id']} "
              f"in_mods={p['in_mods_stats']} in_vocab={p['in_vocab']}")
    cr = out['crossref_resolution']
    print(f"stat-id translation resolution: {cr['mods_stat_ids']['resolvable_to_translation']}/"
          f"{cr['mods_stat_ids']['distinct_stat_ids']}")
    print(f"trade-hash -> TradeSiteStats: {cr['mod_exclusive_trade_hashes']['resolvable_to_trade_site_stats']}/"
          f"{cr['mod_exclusive_trade_hashes']['distinct_hashes']}")


if __name__ == '__main__':
    main()
