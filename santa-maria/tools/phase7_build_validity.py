#!/usr/bin/env python3
"""Build-validity API — thin integration layer over phase7_build_feasibility.

Two operations for incremental discovery validation and final validation:

  validate_addition(state, candidate)   # can candidate join the current state?
  validate_build(state)                 # validate the accumulated build state

Both run the SAME feasibility checks (slot_check / validate_support_chain /
weapon_check) over the actual accumulated build state — never the candidate in
isolation. A candidate that is individually valid can still be rejected because
of the composition (e.g. Hand of Wisdom and Action 1H claw + Jiquani's
Potential 2H staff).

Statuses reuse the feasibility vocabulary:
  'valid'    no conflict among the constraints this validator checks
             (NOT a full PoE build-validity claim — see 'valid_wrt')
  'invalid'  at least one deterministic hard conflict (reasons included)
  'unknown'  at least one check could not be performed (no slot model,
             unresolved parent weapon class, ambiguous weapon context).
             Absence of a check is never reported as valid.

Build state is explicit — no hidden context (BuildState, below). Validators
never mutate; BuildState.add()/add_gem_group() return new instances
(check-then-commit).

Gem groups: the weapon context is taken from the state ONLY when uniquely
determined (exactly one weapon-class item equipped). Otherwise weapon_check is
skipped and the group is 'unknown' with an explicit reason — never guessed.

Discovery integration (stateless CLI, q.py conventions):
  python3 tools/phase7_build_validity.py add CANDIDATE [STATE_ITEM ...]
      [--gem SKILL [SUPPORT ...]]
  python3 tools/phase7_build_validity.py build ITEM [ITEM ...]
      [--gem SKILL [SUPPORT ...]]

Final validation: at the end of build generation run `build` with the complete
state even when every addition passed incremental validation (state may be
assembled through more than one path; some constraints only make sense for the
complete composition).

Usage:
  python3 phase7_build_validity.py        # self-check demo
  python3 -m tests.test_build_validity    # assert-based tests
"""
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase6_api
import phase7_build_feasibility as feas

VALID, INVALID, UNKNOWN = feas.VALID, feas.INVALID, feas.UNKNOWN

# ---- item availability (PoB 'Source:' header is the authoritative signal) ---
# PoB marks content that cannot drop/be obtained any more as
# 'Source: No longer obtainable'. RePoE uniques.json carries no availability
# field. PoB-block absence is a coverage gap, NOT evidence of unavailability,
# so such items are simply not availability-checked (surfaced in LIMITATIONS).
# The PoB availability map lives in phase6_api (_pob_availability) — the API
# layer needs the same signal for seed entries.
_UNAVAILABLE_SOURCE = 'No longer obtainable'
_pob_availability = phase6_api._pob_availability


def json_load(p):
    import json
    with open(p, encoding='utf-8') as fh:
        return json.load(fh)


def _item_availability_checks(items, g):
    """Per-item availability block for the current unique list."""
    nodes = g._load_nodes()
    out = []
    for entry in items:
        uid = feas._resolve_unique(entry, nodes)
        name = nodes[uid][1].get('name') or uid
        verdict = _pob_availability().get(name)
        out.append({'item': uid, 'name': name,
                    'availability': verdict if verdict is not None
                    else 'not_in_pob'})
    unavailable = [r for r in out if r['availability'] == 'unavailable']
    conflicts = [r for r in out if r['availability'] == 'conflict']
    status = INVALID if unavailable else UNKNOWN if conflicts else VALID
    reasons = ([f"{r['name']}: Source: No longer obtainable — disabled/"
                f"unavailable content, cannot be a build component"
                for r in unavailable]
               + [f"{r['name']}: conflicting PoB availability sources — "
                  f"not checked" for r in conflicts])
    return {'status': status,
            'reason': '; '.join(reasons) if reasons else 'available',
            'items': out,
            'unavailable': [r['item'] for r in unavailable]}

VALID_WRT = ('valid with respect to the constraints implemented and checked by '
             'this validator (slot occupancy, weapon configuration, gem '
             'supportability, ascendancy composition); NOT a full PoE '
             'build-validity claim')

LIMITATIONS = [
    'unique duplication not modeled: two copies of the same unique are not '
    'detected unless slot capacity collides',
    'influenced-item compatibility not modeled',
    'items with no slot model (jewels, flasks, ...) surface as unsupported -> '
    'unknown, never assumed valid',
    'socket/link capacity, reservation feasibility, passive-tree legality, '
    'DPS: out of scope of the feasibility layer, never checked here',
    'ascendancy composition: Passive nodes classified via node payload '
    '(ascendancy field + kind_flags); consistent ascendancy=None is a legal '
    'classless passive (regular-tree keystones); only cross-tree-'
    'conflicting classification surfaces as unknown, never guessed. KB fact: '
    'no Ascendancy node is a keystone (is_keystone only on regular-tree '
    'nodes), so the <=4 cap counts is_notable ascendancy nodes; small '
    'ascendancy nodes are uncounted. "exactly one Ascendancy" is enforced on '
    'final validation only when passives are committed; item-only states '
    'skip the check (legacy behaviour)',
    'item availability: PoB Source header ("No longer obtainable") marks '
    'disabled/unavailable uniques; absence of a PoB block is a coverage gap '
    '(~83/1382 unique names) and is NOT availability-checked — PoB absence '
    'is not evidence of unavailability',
]

ASCENDANCY_NOTABLE_CAP = 4


@dataclass
class BuildState:
    """Smallest explicit build state: equipped items + optional gem groups
    and passives.

    items: unique ids ('unique:597') or unique names. gem_groups:
    {'skill': id-or-name, 'supports': [id-or-name, ...]}. passives: passive
    ids ('passive:AscendancyNecromancer9') or passive names.
    Immutable-by-convention: add()/add_gem_group()/add_passive() return new
    instances.
    """
    items: list = field(default_factory=list)
    gem_groups: list = field(default_factory=list)
    passives: list = field(default_factory=list)

    def add(self, candidate):
        return BuildState(list(self.items) + [candidate],
                          list(self.gem_groups), list(self.passives))

    def add_gem_group(self, skill, supports=()):
        gg = self.gem_groups + [{'skill': skill, 'supports': list(supports)}]
        return BuildState(list(self.items), gg, list(self.passives))

    def add_passive(self, candidate):
        return BuildState(list(self.items), list(self.gem_groups),
                          list(self.passives) + [candidate])


def _as_state(state):
    if isinstance(state, BuildState):
        return state
    if isinstance(state, dict):
        return BuildState(list(state.get('items', [])),
                          [dict(g) for g in state.get('gem_groups', [])],
                          list(state.get('passives', [])))
    return BuildState(list(state))          # bare list of items


def _unique_weapon(slot_result, names):
    """The state's weapon for gem weapon_check, only when uniquely determined."""
    weapons = [a for a in slot_result['assignments']
               if 'weapon' in (a['slots'] or [])]
    if len(weapons) == 1:
        return weapons[0]['item'], None
    ws = ', '.join(names.get(a['item'], a['item']) for a in weapons)
    reason = (f'weapon context not uniquely determined: {len(weapons)} '
              f'weapon-class items equipped' + (f' ({ws})' if ws else '')
              + '; weapon_check skipped')
    return None, reason


def _resolve_passive(candidate, nodes):
    """Resolve a passive id-or-name to 'passive:<id>' (fail-fast ValueError)."""
    key = candidate if candidate.startswith('passive:') \
        else f'passive:{candidate}'
    if key in nodes:
        return key
    want = candidate.lower()
    hits = [nid for nid, (typ, payload) in nodes.items()
            if typ == 'Passive' and (payload.get('name') or '').lower() == want]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise ValueError(f'passive node not found: {candidate!r}')
    raise ValueError(f'passive name ambiguous ({len(hits)} nodes): {candidate!r}')


def _classify_passive(payload):
    """(ascendancy, is_notable, class_status) from a Passive node payload.

    class_status 'known' when classification is resolved — including
    legitimately classless nodes (ascendancy=None consistent across all
    tree variants, e.g. regular-tree keystones). Only cross-variant
    DISAGREEMENT on ascendancy or kind_flags yields 'unknown'.
    """
    shared = payload.get('shared') or {}
    kf = payload.get('kind_flags')
    notable = None if kf is None else bool(kf.get('is_notable'))
    asc = shared.get('ascendancy')
    variants = payload.get('variants') or []
    if variants:
        vascs = {v.get('record', {}).get('ascendancy') for v in variants}
        if len(vascs) > 1:
            return None, notable, 'unknown'
        asc = next(iter(vascs))
    if asc is None:
        # consistent None: legal for plain ids (Vaal Pact = classless
        # regular-tree node), but an Ascendancy* id with empty class is a
        # KB data gap -> unknown, never guessed
        if payload.get('id', '').find('Ascendancy') >= 0:
            return None, notable, 'unknown'
    if notable is None:
        return asc, notable, 'unknown'
    return asc, notable, 'known'


def _passive_checks(passives, g, final):
    """Ascendancy composition checks over the accumulated passive list.

    Reports resolved classification, class mixing, notable cap and (final)
    exactly-one. Unresolvable names raise ValueError (fail-fast, consistent
    with items); unclassifiable payloads contribute 'unknown'.
    """
    nodes = g._load_nodes()
    resolved, unknown_reasons = [], []
    for entry in passives:
        pid = _resolve_passive(entry, nodes)
        typ, payload = nodes[pid]
        asc, notable, status = _classify_passive(payload)
        name = payload.get('name') or pid
        resolved.append({'passive': pid, 'name': name, 'ascendancy': asc,
                         'class_status': status, 'is_notable': notable})
        if status == 'unknown':
            unknown_reasons.append(
                f"{name}: ascendancy/flags unclassifiable in KB (never guessed)")
    classes = sorted({r['ascendancy'] for r in resolved
                      if r['class_status'] == 'known' and r['ascendancy']})
    class_mix = {'result': VALID, 'reason': None, 'classes': classes}
    if len(classes) > 1:
        class_mix.update(result=INVALID,
                         reason='mixed Ascendancies: ' + ', '.join(classes))
    n_notables = sum(1 for r in resolved
                     if r['class_status'] == 'known' and r['is_notable'])
    cap = {'result': VALID, 'reason': None, 'count': n_notables,
           'cap': ASCENDANCY_NOTABLE_CAP}
    if n_notables > ASCENDANCY_NOTABLE_CAP:
        cap.update(result=INVALID, reason=(
            f'{n_notables} ascendancy notables exceeds cap of '
            f'{ASCENDANCY_NOTABLE_CAP}'))
    single = {'result': VALID, 'reason': None, 'required': True}
    if final and not classes:
        single.update(result=INVALID,
                      reason='no Ascendancy in final build state')

    results = [class_mix, cap, single] if final else [class_mix, cap]
    status = INVALID if any(c['result'] == INVALID for c in results) \
        else UNKNOWN if unknown_reasons else VALID
    reasons = ([c['reason'] for c in results if c['result'] == INVALID]
               + [f'{r} — not checked' for r in unknown_reasons])
    return {'status': status,
            'reason': '; '.join(reasons) if reasons else 'valid',
            'resolved': resolved,
            'class_mix': class_mix,
            'notable_cap': cap,
            'single_ascendancy': single}


def _check_gem_group(gg, weapon, weapon_reason, g):
    chain = feas.validate_support_chain(gg['skill'], gg.get('supports', []), g)
    if weapon is not None:
        wc = feas.weapon_check(gg['skill'], weapon, g)
    else:
        wc = {'skill': chain['skill'], 'result': UNKNOWN, 'reason': weapon_reason}
    chain_reason = next((f"{s['support']}: {s['reason']}"
                         for s in chain['steps'] if s['result'] != VALID), None)
    group = {'skill': chain['skill'],
             'support_chain': {'result': chain['result'],
                               'reason': chain_reason},
             'weapon_restriction': {'result': wc['result'],
                                    'reason': wc['reason']}}
    results = (chain['result'], wc['result'])
    group['status'] = (INVALID if INVALID in results
                       else UNKNOWN if UNKNOWN in results else VALID)
    return group


def _gem_reason(group):
    for k in ('support_chain', 'weapon_restriction'):
        if group[k]['result'] != VALID:
            return f"{k} {group[k]['result']}: {group[k]['reason']}"
    return 'valid'


def validate_build(state, graph=None, final=True):
    """Validate the complete accumulated build state; reports ALL conflicts.

    final=True enforces 'exactly one Ascendancy' (final-build requirement).
    Incremental checks (validate_addition) pass final=False: an in-progress
    state may not contain an ascendancy yet; mixing and the notable cap still
    apply.
    """
    g = graph or phase6_api.get_graph()
    state = _as_state(state)
    sr = feas.slot_check(state.items, g)
    names = {a['item']: a['name'] for a in sr['assignments']}
    conflicts = [dict(c, items_named=[names.get(u, u) for u in c['items']])
                 for c in sr['conflicts']]
    conflict_reasons = [f"{c['slot']}: {c['reason']} — items: "
                        f"{', '.join(c['items_named'])}" for c in conflicts]

    pc = _passive_checks(state.passives, g, final) if state.passives else None
    passive_invalid = pc is not None and pc['status'] == INVALID
    passive_unknown = pc is not None and pc['status'] == UNKNOWN
    pc_reason = pc['reason'] if pc is not None else None

    ac = _item_availability_checks(state.items, g) if state.items else None
    avail_invalid = ac is not None and ac['status'] == INVALID
    avail_unknown = ac is not None and ac['status'] == UNKNOWN
    ac_reason = ac['reason'] if ac is not None else None

    gem_checks = []
    if state.gem_groups:
        weapon, weapon_reason = _unique_weapon(sr, names)
        gem_checks = [_check_gem_group(gg, weapon, weapon_reason, g)
                      for gg in state.gem_groups]
    gem_invalid = [c for c in gem_checks if c['status'] == INVALID]
    gem_unknown = [c for c in gem_checks if c['status'] == UNKNOWN]

    if conflicts or gem_invalid or passive_invalid or avail_invalid:
        status = INVALID
        reasons = conflict_reasons + [f"gem group {c['skill']}: {_gem_reason(c)}"
                                      for c in gem_invalid]
        if avail_invalid:
            reasons.append(f"availability: {ac_reason}")
        if passive_invalid:
            reasons.append(f"passives: {pc_reason}")
    elif sr['unsupported'] or gem_unknown or passive_unknown or avail_unknown:
        status = UNKNOWN
        reasons = ([f"{u['name']} ({u['item_class']}): {u['reason']} — not checked"
                    for u in sr['unsupported']]
                   + [f"gem group {c['skill']}: {_gem_reason(c)}"
                      for c in gem_unknown])
        if avail_unknown:
            reasons.append(f"availability: {ac_reason}")
        if passive_unknown:
            reasons.append(f"passives: {pc_reason}")
    else:
        status, reasons = VALID, []

    return {'status': status,
            'reason': '; '.join(reasons) if reasons else VALID_WRT,
            'conflicts': conflicts,
            'unsupported': sr['unsupported'],
            'gem_checks': gem_checks,
            'passive_checks': pc,
            'availability_checks': ac,
            'checked': (['slot_occupancy', 'weapon_configuration']
                        + (['gem_support'] if state.gem_groups else [])
                        + (['ascendancy_composition'] if pc else [])
                        + (['item_availability'] if ac else [])),
            'valid_wrt': VALID_WRT,
            'limitations': LIMITATIONS}


def validate_addition(state, candidate, graph=None):
    """Can candidate be added to the current build state?

    Runs validate_build over state+candidate (same rules, same envelope) and
    attributes conflicts involving the candidate. Never mutates state.
    Passives go through add_passive and final=False (exactly-one-Ascendancy is
    a final-build constraint; mixing/cap still apply incrementally).
    """
    g = graph or phase6_api.get_graph()
    state = _as_state(state)
    nodes = g._load_nodes()
    cand_pid = None
    try:
        cand_pid = _resolve_passive(candidate, nodes)
        is_passive = True
    except ValueError:
        is_passive = False
    if is_passive:
        merged = state.add_passive(candidate)
    else:
        merged = state.add(candidate)
    out = validate_build(merged, g, final=False)
    out['candidate'] = candidate
    if is_passive and out['passive_checks']:
        pc = out['passive_checks']
        pid = cand_pid
        cand = next((r for r in pc['resolved'] if r['passive'] == pid), None)
        if cand and pc['status'] == INVALID:
            if len(pc['class_mix']['classes']) > 1 and cand['class_status'] == 'known':
                others = [c for c in pc['class_mix']['classes']
                          if c != cand['ascendancy']]
                out['reason'] = (f"candidate {cand['name']} would introduce a "
                                 f"second Ascendancy ({cand['ascendancy']}); "
                                 f"state already has {', '.join(others)}")
            elif pc['notable_cap']['result'] == INVALID and cand['is_notable']:
                out['reason'] = (f"candidate {cand['name']} would exceed the "
                                 f"ascendancy-notable cap "
                                 f"({pc['notable_cap']['count']}/"
                                 f"{ASCENDANCY_NOTABLE_CAP})")
            else:
                out['reason'] = f"passives: {pc['reason']}"
        out['status'] = pc['status'] if pc['status'] == INVALID \
            else out['status']
        return out
    # availability attribution: candidate itself unavailable?
    if out['availability_checks'] and \
            out['availability_checks']['status'] == INVALID:
        nodes = g._load_nodes()
        try:
            cand_uid = feas._resolve_unique(candidate, nodes)
        except ValueError:
            cand_uid = None
        if cand_uid is not None and cand_uid in \
                out['availability_checks']['unavailable']:
            cand_name = next(r['name'] for r in
                             out['availability_checks']['items']
                             if r['item'] == cand_uid)
            out['reason'] = (f"candidate {cand_name} is no longer obtainable "
                             f"(disabled/unavailable content) and cannot join "
                             f"the build")
            return out
    if out['conflicts']:
        cand_uid = feas._resolve_unique(candidate, g._load_nodes())
        involved = [c for c in out['conflicts'] if cand_uid in c['items']]
        if involved:
            parts = []
            for c in involved:
                cand_name = c['items_named'][c['items'].index(cand_uid)]
                others = ', '.join(n for u, n in zip(c['items'], c['items_named'])
                                   if u != cand_uid)
                parts.append(f"{c['slot']}: {c['reason']} — {cand_name}"
                             f" conflicts with {others}")
            out['reason'] = ('candidate conflicts with the current build '
                             'state: ' + '; '.join(parts))
        else:
            out['reason'] = ('build state already invalid, independent of the '
                             'candidate: ' + '; '.join(
                                 f"{c['slot']}: {c['reason']}"
                                 for c in out['conflicts']))
    return out


def demo():
    g = phase6_api.get_graph()
    print('== incremental ==')
    s = BuildState(['Hand of Wisdom and Action'])
    print('add HoWA:', validate_build(s, g)['status'])
    r = validate_addition(s, "Jiquani's Potential", g)
    print('add Jiquani:', r['status'], '|', r['reason'])
    r = validate_addition(s, "Doedre's Damning", g)
    print('add ring:', r['status'])
    print('\n== final ==')
    r = validate_build(s.add("Doedre's Damning").add("Demigod's Eye"), g)
    print('full build:', r['status'], '| checked:', r['checked'])


if __name__ == '__main__':
    if len(sys.argv) > 1:
        import argparse, json
        ap = argparse.ArgumentParser(
            description='build validity: validate_addition / validate_build')
        sub = ap.add_subparsers(required=True)
        for name, help_, items_required in (
                ('add', 'CANDIDATE [STATE_ITEM ...]: validate_addition', False),
                ('build', 'ITEM [ITEM ...]: validate_build (items optional '
                          'when only passives are committed)', True)):
            p = sub.add_parser(name, help=help_)
            if name == 'add':
                p.add_argument('candidate')
            p.add_argument('items', nargs='*',
                           help='build-state items (unique ids or names)')
            p.add_argument('--gem', action='append', nargs='+', default=[],
                           metavar=('SKILL', 'SUPPORT'),
                           help='gem group SKILL [SUPPORT ...]; repeatable')
            p.add_argument('--passive', action='append', default=[],
                           metavar='NAME',
                           help='build-state passive (id or name); repeatable')
        args = ap.parse_args()
        gem_groups = [{'skill': gg[0], 'supports': gg[1:]} for gg in args.gem]
        state = BuildState(args.items, gem_groups, args.passive)
        if hasattr(args, 'candidate'):
            res = validate_addition(state, args.candidate)
        else:
            res = validate_build(state)
        print(json.dumps(res, indent=1))
    else:
        demo()
