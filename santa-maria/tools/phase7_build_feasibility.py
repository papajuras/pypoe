#!/usr/bin/env python3
"""Build feasibility layer — equipment slots + gem supportability.

Read-only, deterministic, derived entirely from existing KB payloads/edges
(see docs/experiments/phase7_feasibility_research/README.md). Never touches the
graph, phase6_api, BFS, carrier grouping, or the stat classifier.

Out of scope (per research): socket/link capacity, weapon swaps, jewel/flask
capacity, crafting, passive-allocation constraints.

Slots model (from item classes):
  weapon slot capacity 2 — 1H weapons count 1, Bow/melee-2H count 2
  off-hand capacity 1    — Shield/Quiver; blocked by melee 2H
  Shield requires a 1H main weapon; Quiver requires a Bow
  Ring capacity 2; Helmet/Body Armour/Gloves/Boots/Belt/Amulet capacity 1
  any other class -> explicit 'unsupported' (never silently assumed)

Gem supportability outcomes are exactly 'valid' | 'invalid' | 'unknown';
missing/incomplete data yields 'unknown', never 'invalid'. excluded_types /
allowed_types may contain PoB expression operator tokens (NOT/AND/OR): operator
tokens are never treated as types; an intersecting exclusion under operators is
'unknown' (ambiguous), a disjoint exclusion is confidently 'valid'.

Usage:
  python3 phase7_build_feasibility.py                     # self-check demo
  python3 -m tests.test_build_feasibility          # assert-based tests
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase6_api

SANTA = Path(__file__).resolve().parents[1]

SINGLE_SLOTS = {'Helmet': 'head', 'Body Armour': 'body', 'Gloves': 'gloves',
                'Boots': 'boots', 'Belt': 'belt', 'Amulet': 'amulet'}
ONE_HANDED = {'One Hand Sword', 'One Hand Axe', 'One Hand Mace',
              'Thrusting One Hand Sword', 'Sceptre', 'Wand', 'Dagger',
              'Rune Dagger', 'Claw'}
BOWS = {'Bow'}
TWO_HANDED_MELEE = {'Two Hand Sword', 'Two Hand Axe', 'Two Hand Mace',
                    'Staff', 'Warstaff', 'FishingRod'}
OFFHAND = {'Shield', 'Quiver'}

EXPRESSION_OPS = {'NOT', 'AND', 'OR', 'if', 'MAX', 'MIN'}

VALID, INVALID, UNKNOWN = 'valid', 'invalid', 'unknown'

# Parent weapon classes: concrete class (and 1H/2H occupancy) is resolved per
# unique via the deterministic chain documented in
# docs/experiments/phase7_weapon_resolution/README.md:
#   unique name -> data/pob/Uniques/<parent>.json line 2 (base name, {variant:…}
#   stripped) -> repoe/base_items.json 'name' lookup -> concrete item_class
#   -> handedness (class prefix, confirmed by inherits_from OneHandWeapons/ vs
#   TwoHandWeapons/). Unresolved -> explicit unknown/unsupported, never guessed.
WEAPON_PARENT_CLASSES = {'Sword', 'Axe', 'Mace'}

_weapon_res_cache = None


def _slot_model(cls):
    """class -> (slots, weapon units) or (None, None) if no slot model."""
    if cls in SINGLE_SLOTS:
        return [SINGLE_SLOTS[cls]], 1
    if cls == 'Ring':
        return ['ring'], 1
    if cls in ONE_HANDED:
        return ['weapon'], 1
    if cls in BOWS:
        return ['weapon'], 2
    if cls in TWO_HANDED_MELEE:
        return ['weapon', 'offhand_blocked'], 2
    if cls in OFFHAND:
        return ['offhand'], 1
    return None, None


def _weapon_resolution_data():
    """Lazily cached (pob_blocks, base_index); files are read once, read-only."""
    global _weapon_res_cache
    if _weapon_res_cache is None:
        import json, re
        pob = {}
        for f in sorted((SANTA / 'data' / 'pob' / 'Uniques').glob('*.json')):
            try:
                blocks = json.loads(f.read_text())
            except (ValueError, OSError):
                continue
            pairs = []
            for b in blocks:
                lines = b.split('\n')
                if len(lines) >= 2 and lines[0].strip():
                    pairs.append((lines[0].strip(),
                                  re.sub(r'^\{[^}]*\}', '', lines[1]).strip()))
            pob[f.stem] = pairs
        bi = json.loads((SANTA / 'data' / 'repoe' / 'base_items.json').read_text())
        bases = {}
        for k in sorted(bi):
            rec = bi[k]
            nm = rec.get('name')
            if nm and nm not in bases:
                bases[nm] = (rec.get('item_class'), rec.get('inherits_from'))
        _weapon_res_cache = (pob, bases)
    return _weapon_res_cache


def _handedness(concrete_cls, inherits_from=None):
    """1H/2H from the concrete class prefix, confirmed by inherits_from."""
    h = None
    if concrete_cls.startswith(('One Hand', 'Thrusting One Hand')) or concrete_cls in (
            'Dagger', 'Rune Dagger', 'Claw', 'Wand', 'Sceptre'):
        h = '1H'
    elif concrete_cls.startswith('Two Hand') or concrete_cls in (
            'Bow', 'Staff', 'Warstaff', 'FishingRod'):
        h = '2H'
    if h is None or inherits_from is None:
        return h
    if 'OneHandWeapons/' in inherits_from:
        ih = '1H'
    elif 'TwoHandWeapons/' in inherits_from:
        ih = '2H'
    else:
        return h
    return h if ih == h else None   # contradiction -> unresolved, never guess


def resolve_weapon_class(node_or_name, graph=None):
    """Resolve a unique weapon to its concrete class/handedness.

    Returns {'item_class', 'handedness'|None, 'resolved': bool, 'reason', ...}.
    Concrete-class items pass through unchanged (resolved=False, no handedness
    needed); only parent weapon classes go through the resolution chain.
    """
    g = graph or phase6_api.get_graph()
    nodes = g._load_nodes()
    out, inn = g._load_edges()
    uid = _resolve_unique(node_or_name, nodes)
    payload = nodes[uid][1]
    cls = payload.get('item_class')
    for t, _ in out['unique_in_class'].get(uid, []):
        cls = t.replace('item_class:', '', 1)
    if cls not in WEAPON_PARENT_CLASSES:
        return {'item_class': cls, 'handedness': None, 'resolved': False,
                'reason': 'not a parent weapon class'}
    pob, bases = _weapon_resolution_data()
    name = payload.get('name')
    for uname, base_name in pob.get(cls.lower(), []):
        if uname != name or base_name not in bases:
            continue
        concrete, inherits_from = bases[base_name]
        h = _handedness(concrete, inherits_from)
        if h is None:
            continue
        return {'item_class': concrete, 'handedness': h, 'resolved': True,
                'base_item': base_name}
    return {'item_class': cls, 'handedness': None, 'resolved': False,
            'reason': f'no deterministic base-item resolution for {name!r} '
                      f'({cls})'}


def _resolve(node_id_or_name, nodes, type_prefix, name_fields):
    key = node_id_or_name
    if not key.startswith(f'{type_prefix}:'):
        key = f'{type_prefix}:{node_id_or_name}'
    if key in nodes:
        return key
    want = node_id_or_name.lower()
    for nid, (typ, payload) in nodes.items():
        if typ != type_prefix.capitalize():
            continue
        for f in name_fields:
            v = payload.get(f)
            if isinstance(v, str) and v.lower() == want:
                return nid
    raise ValueError(f'{type_prefix} node not found: {node_id_or_name!r}')


def _resolve_unique(node_or_name, nodes):
    key = node_or_name
    if not key.startswith('unique:'):
        key = f'unique:{node_or_name}'
    if key in nodes:
        return key
    want = node_or_name.lower()
    for nid, (typ, payload) in nodes.items():
        if typ == 'UniqueItem' and (payload.get('name') or '').lower() == want:
            return nid
    raise ValueError(f'unique node not found: {node_or_name!r}')


def slot_check(required_items, graph=None):
    """Resolve items -> item_class -> slots; detect occupancy conflicts."""
    g = graph or phase6_api.get_graph()
    nodes = g._load_nodes()
    out, inn = g._load_edges()
    cls_of = {u: t for u, l in out['unique_in_class'].items() for (t, _) in l}

    counts = {}            # slot -> [(uid, weight)]
    assignments, unsupported, conflicts = [], [], []
    resolved = []
    for entry in required_items:
        uid = _resolve_unique(entry, nodes)
        resolved.append(uid)
        ic = cls_of.get(uid) or (
            f"item_class:{nodes[uid][1].get('item_class')}"
            if nodes[uid][1].get('item_class') else None)
        name = nodes[uid][1].get('name') or uid
        cls = ic.replace('item_class:', '', 1) if ic else None
        slots, weight = _slot_model(cls)
        resolved_class = None
        if slots is None and cls in WEAPON_PARENT_CLASSES:
            r = resolve_weapon_class(uid, g)
            if r['resolved']:
                cls, resolved_class = r['item_class'], r['item_class']
                slots, weight = _slot_model(cls)
        for s in slots or []:
            if s != 'offhand_blocked':
                counts.setdefault(s, []).append((uid, weight))
        a = {'item': uid, 'name': name, 'item_class': cls, 'slots': slots or []}
        if resolved_class:
            a['resolved_item_class'] = resolved_class
        if not slots:
            a['status'] = 'unsupported'
            reason = 'no slot model for this item class'
            if cls in WEAPON_PARENT_CLASSES:
                reason = 'parent weapon class without deterministic base resolution'
            unsupported.append({'item': uid, 'name': name, 'item_class': cls,
                                'reason': reason})
        else:
            a['status'] = 'checked'
        assignments.append(a)

    CAPACITY = {'weapon': 2, 'offhand': 1, 'ring': 2, 'head': 1, 'body': 1,
                'gloves': 1, 'boots': 1, 'belt': 1, 'amulet': 1}
    for slot, entries in sorted(counts.items()):
        units = sum(w for _, w in entries)
        if units > CAPACITY[slot]:
            conflicts.append({'slot': slot, 'items': sorted(u for u, _ in entries),
                              'reason': f'capacity {CAPACITY[slot]} exceeded '
                                        f'({units} slot units)'})
    # off-hand semantic rules
    weapons = [u for u, _ in counts.get('weapon', [])]
    weapon_classes = [next(a['item_class'] for a in assignments if a['item'] == u)
                      for u in weapons]
    has_1h = any(c in ONE_HANDED for c in weapon_classes)
    has_bow = any(c in BOWS for c in weapon_classes)
    has_2h_melee = any(c in TWO_HANDED_MELEE for c in weapon_classes)
    offhand_uids = [u for u, _ in counts.get('offhand', [])]
    offhand_classes = [next(a['item_class'] for a in assignments if a['item'] == u)
                       for u in offhand_uids]
    if has_2h_melee and offhand_uids:
        conflicts.append({'slot': 'offhand', 'items': sorted(offhand_uids),
                          'reason': 'two-handed melee weapon occupies the off-hand'})
    for uid, cls in zip(offhand_uids, offhand_classes):
        if cls == 'Shield' and not has_1h:
            conflicts.append({'slot': 'offhand', 'items': [uid],
                              'reason': 'shield requires a one-handed main weapon'})
        if cls == 'Quiver' and not has_bow:
            conflicts.append({'slot': 'offhand', 'items': [uid],
                              'reason': 'quiver requires a bow'})
    return {'valid': not conflicts, 'conflicts': conflicts,
            'unsupported': unsupported, 'assignments': assignments,
            'undetermined': bool(unsupported)}


# ---- gem supportability ----

def _gem_types(payload):
    return (payload.get('active_skill') or {}).get('types') or []


def can_support(support_gem, skill_gem, graph=None, skill_types=None):
    """Three-outcome pairwise check: 'valid' | 'invalid' | 'unknown'."""
    g = graph or phase6_api.get_graph()
    nodes = g._load_nodes()
    sid = _resolve(support_gem, nodes, 'gem', ('display_name', 'record_key'))
    kid = _resolve(skill_gem, nodes, 'gem', ('display_name', 'record_key'))
    sp, kp = nodes[sid][1], nodes[kid][1]
    sg = sp.get('support_gem') or {}
    ev = {'support': sid, 'skill': kid, 'allowed_types': sg.get('allowed_types'),
          'excluded_types': sg.get('excluded_types'),
          'skill_types': skill_types if skill_types is not None else _gem_types(kp),
          'added_types': sg.get('added_types')}
    if not sp.get('is_support'):
        return {'result': INVALID, 'reason': f'{sid} is not a support gem', 'evidence': ev}
    if kp.get('is_support'):
        return {'result': INVALID,
                'reason': f'{kid} is a support gem; supports cannot be supported',
                'evidence': ev}
    if sp.get('support_gem') is None:
        return {'result': UNKNOWN, 'reason': f'{sid} has no support_gem payload', 'evidence': ev}
    if (sg.get('allowed_types') is None and not sg.get('excluded_types')
            and sg.get('support_name') is None and sg.get('support_text') is None):
        return {'result': UNKNOWN,
                'reason': f'{sid} has no support contract data (pseudo-support)',
                'evidence': ev}
    types = list(ev['skill_types'])
    if not types:
        return {'result': UNKNOWN, 'reason': f'{kid} has no active_skill.types', 'evidence': ev}

    allowed = sg.get('allowed_types')
    if allowed is not None:
        plain = [t for t in allowed if t not in EXPRESSION_OPS]
        if not (set(plain) & set(types)):
            if len(plain) < len(allowed):
                return {'result': UNKNOWN,
                        'reason': 'allowed_types expression not confidently evaluable '
                                  'and no plain type matches the skill types',
                        'evidence': ev}
            return {'result': INVALID,
                    'reason': 'no allowed_types entry matches the skill types',
                    'evidence': ev}

    excluded = sg.get('excluded_types') or []
    if excluded:
        plain = [t for t in excluded if t not in EXPRESSION_OPS]
        hit = set(plain) & set(types)
        if hit:
            if len(plain) < len(excluded):
                return {'result': UNKNOWN,
                        'reason': f'excluded expression contains operator tokens; '
                                  f'ambiguous intersection {sorted(hit)}',
                        'evidence': ev}
            return {'result': INVALID,
                    'reason': f'skill types intersect excluded_types: {sorted(hit)}',
                    'evidence': ev}
    return {'result': VALID, 'reason': 'allowed/excluded checks passed', 'evidence': ev}


def validate_support_chain(skill_gem, support_gems, graph=None):
    """Ordered check: each support sees the type set accumulated so far."""
    g = graph or phase6_api.get_graph()
    nodes = g._load_nodes()
    kid = _resolve(skill_gem, nodes, 'gem', ('display_name', 'record_key'))
    current = _gem_types(nodes[kid][1])
    steps, result = [], VALID
    if not current:
        result = UNKNOWN
    for entry in support_gems:
        r = can_support(entry, kid, g, skill_types=list(current))
        sid = r['evidence']['support']
        before = list(current)
        applied = []
        if r['result'] == VALID and current:
            added = [t for t in (r['evidence']['added_types'] or [])
                     if t not in EXPRESSION_OPS]
            applied = [t for t in added if t not in current]
            current = current + applied
        steps.append({'support': sid, 'result': r['result'], 'reason': r['reason'],
                      'types_before': before, 'types_after': list(current),
                      'added_types_applied': applied})
        if r['result'] == INVALID:
            result = INVALID
        elif r['result'] == UNKNOWN and result == VALID:
            result = UNKNOWN
    return {'skill': kid, 'result': result, 'steps': steps,
            'final_types': list(current)}


def weapon_check(skill_gem, weapon=None, graph=None):
    """Evaluate active_skill.weapon_restrictions against a weapon class/item.

    weapon: item_class name ('Bow'), unique id/name, or None.
    Missing restrictions -> valid ('no weapon restrictions'), never invalid.
    """
    g = graph or phase6_api.get_graph()
    nodes = g._load_nodes()
    kid = _resolve(skill_gem, nodes, 'gem', ('display_name', 'record_key'))
    restrictions = (nodes[kid][1].get('active_skill') or {}).get('weapon_restrictions')
    if not restrictions:
        return {'skill': kid, 'result': VALID, 'reason': 'no weapon restrictions'}
    if weapon is None:
        return {'skill': kid, 'result': UNKNOWN,
                'reason': f'restrictions {restrictions} but no weapon given'}
    cls, uid = weapon, None
    if not weapon.startswith('item_class:'):
        if weapon in nodes and nodes[weapon][0] == 'UniqueItem':
            uid, cls = weapon, nodes[weapon][1].get('item_class')
        elif f'unique:{weapon}' in nodes:
            uid = f'unique:{weapon}'
            cls = nodes[uid][1].get('item_class')
    cls = (cls or '').replace('item_class:', '', 1)
    if cls in WEAPON_PARENT_CLASSES:
        if uid is None:
            return {'skill': kid, 'weapon_class': cls, 'restrictions': restrictions,
                    'result': UNKNOWN,
                    'reason': 'parent weapon class name without a concrete item '
                              'to resolve'}
        r = resolve_weapon_class(uid, g)
        if not r['resolved']:
            return {'skill': kid, 'weapon_class': cls, 'restrictions': restrictions,
                    'result': UNKNOWN,
                    'reason': f'parent weapon class unresolved ({r["reason"]})'}
        cls = r['item_class']
    ok = cls in restrictions
    return {'skill': kid, 'weapon_class': cls, 'restrictions': restrictions,
            'result': VALID if ok else INVALID,
            'reason': (f'{cls} is an allowed weapon class' if ok
                       else f'{cls} not in weapon_restrictions')}


def demo():
    g = phase6_api.GraphDB()
    print('== slots ==')
    for items in [["Voll's Protector", 'The Brass Dome'],
                  ["Demigod's Eye", "Doedre's Damning"],
                  ['Redbeak', "Demigod's Beacon"],
                  ['Silverbranch', "Demigod's Beacon"],
                  ['Glorious Vanity']]:
        r = slot_check(items, g)
        print(items, '-> valid:', r['valid'], '| conflicts:', r['conflicts'],
              '| unsupported:', [(u['name'], u['item_class']) for u in r['unsupported']])
    print('\n== can_support ==')
    for b, a in [('gem:SupportMultistrike', 'gem:HolyHammers'),
                 ('gem:SupportChargedTraps', 'gem:HolyHammers'),
                 ('gem:SupportPointBlank', 'gem:HolyHammers'),
                 ('gem:SupportChargedTraps', 'gem:LightningTrap'),
                 ('gem:SupportElementalFocus', 'gem:HolyHammers')]:
        print(f'{b} -> {a}:', can_support(b, a, g)['result'])
    print('\n== ordered chain ==')
    r = validate_support_chain('gem:HolyHammers',
                               ['gem:GeneralsCrySupport', 'gem:SupportMultistrike'], g)
    print('HH + GeneralsCry + Multistrike:', r['result'],
          [(s['support'], s['result']) for s in r['steps']])
    print('weapon:', weapon_check('gem:HolyHammers', 'Sceptre', g)['result'],
          '|', weapon_check('gem:HolyHammers', 'Bow', g)['result'])


if __name__ == '__main__':
    demo()
