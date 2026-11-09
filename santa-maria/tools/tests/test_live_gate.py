#!/usr/bin/env python3
"""Live-only invariant tests: what lands in the KB is live.

Run: cd santa-maria && uv run python -m tools.tests.test_live_gate

Pins the build-time association gate (extract_nodes): method-6 (Vestigial
alt-quality) associations are retired; m1/m4 associations must be text-true
against the unique's CURRENT PoB block; blockless uniques carry none. The
public API does no filtering — absence here means the KB never had it.
"""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import extract_nodes as en
import phase8_research as R

ROOT = Path(__file__).resolve().parents[2]

MV_PER50 = 'mod:GainArmourEqualToManaReservedUnique__1'
MV_PER100 = 'mod:DivergentGainArmourEqualToManaReservedUnique__1'
TARYN_STALE = 'mod:SpellDamageUniqueStaff2'          # (50-60)% — Pre-3.11 line
GOLDRIM_STALE = 'mod:AllResistancesUniqueAmulet2'    # +20% — pre-buff text
GOLDRIM_CURRENT = 'mod:AllResistancesUniqueHelmetDex3'   # +(30-40)%


def _uma_carriers(mod_id):
    doc = R.carriers(mod_id, edge_types=['unique_modifier_association'])
    assert doc['error'] is None, doc
    return [r['carrier'] for r in doc['results']]


def test_gate_units():
    cur = [en.live_tokens('1% increased Armour per 50 Reserved Mana')]
    assert en.live_text_ok('1% increased Armour per 50 Reserved Mana', cur)
    # legacy item-version: numbers must be distinct (Taryn/Goldrim class)
    assert not en.live_text_ok('1% increased Armour per 100 Reserved Mana', cur)
    assert not en.live_text_ok('+20% to all Elemental Resistances',
                               [en.live_tokens('+(30-40)% to all Elemental Resistances')])
    # number boundary: '20' never matches '120'
    assert not en.live_text_ok('+20% to all Elemental Resistances',
                               [en.live_tokens('+(120)% to all Elemental Resistances')])
    # formatting tolerance (the former m5-FP class)
    assert en.live_text_ok('Regenerate 8.00 Mana per second',
                           [en.live_tokens('Regenerate 8 Mana per second')])
    assert en.live_text_ok('(50-60)% increased Spell Damage',
                           [en.live_tokens('(60-50)% increased Spell Damage')])
    assert en.live_text_ok('(-35-35)% increased Duration',
                           [en.live_tokens('(-35-35)% reduced Duration')])
    assert en.live_text_ok('Gain (1-3) Endurance Charges on use',
                           [en.live_tokens('Gain (1-3) Endurance Charge on use')])
    assert en.live_text_ok('Socketed Spells are Supported by level 20 [CrabTotem|Crab Totem]',
                           [en.live_tokens('Socketed Spells are Supported by level 20 Crab Totem')])
    # unverifiable text is never live
    assert not en.live_text_ok(None, cur) and not en.live_text_ok('', cur)
    print('ok: gate normalization units')


def test_method6_retired():
    # Vestigial alt-quality implicits are out of the KB (separate modelling later)
    assert _uma_carriers(MV_PER100) == []
    print('ok: method-6/Vestigial associations retired (MV per-100 absent)')


def test_live_associations_present():
    assert 'unique:713' in _uma_carriers(MV_PER50)          # Memory Vault per-50
    goldrim_ids = {r['id'] for r in R.resolve('Goldrim', type='UniqueItem')['results']}
    assert goldrim_ids & set(_uma_carriers(GOLDRIM_CURRENT)), goldrim_ids
    print('ok: live associations present (MV per-50, Goldrim current)')


def test_stale_associations_absent():
    assert _uma_carriers(TARYN_STALE) == []      # Pre-3.11 variant line
    assert _uma_carriers(GOLDRIM_STALE) == []    # pre-buff text
    print('ok: stale associations absent (Taryn legacy line, Goldrim pre-buff)')


def test_blockless_uniques_carry_no_associations():
    con = sqlite3.connect(f'file:{ROOT / "cache" / "nodes.db"}?mode=ro', uri=True)
    raw = sqlite3.connect(f'file:{ROOT / "cache" / "raw_records.db"}?mode=ro', uri=True)
    blocks = en.load_pob_blocks(raw)
    blockless_with_targets = 0
    checked = 0
    for nid, payload in con.execute(
            "SELECT node_id, payload FROM nodes WHERE type='UniqueItem'"):
        p = json.loads(payload)
        if p['name'] in blocks:
            continue
        checked += 1
        assoc = [t for t in p.get('resolved_targets') or []
                 if t.get('target_type') == 'Modifier'
                 and t.get('method') in (1, 4, 5)
                 and t.get('status') == 'resolved']
        if assoc:
            blockless_with_targets += 1
    con.close()
    raw.close()
    assert checked > 50, checked        # blockless population exists
    assert blockless_with_targets == 0, blockless_with_targets
    print(f'ok: {checked} blockless uniques carry zero association targets')


def test_m5_pairs_all_text_true():
    """Acceptance gate: 0 of the m5-resolved pairs may fail the liveness gate
    (m5 resolves FROM current block lines, so the gate must agree)."""
    con = sqlite3.connect(f'file:{ROOT / "cache" / "nodes.db"}?mode=ro', uri=True)
    raw = sqlite3.connect(f'file:{ROOT / "cache" / "raw_records.db"}?mode=ro', uri=True)
    blocks = en.load_pob_blocks(raw)
    mod_text = {}
    for nid, payload in con.execute(
            "SELECT node_id, payload FROM nodes WHERE type='Modifier'"):
        p = json.loads(payload)
        if 'text' in p:
            mod_text[nid] = p['text']
    checked = flagged = 0
    for _nid, payload in con.execute(
            "SELECT node_id, payload FROM nodes WHERE type='UniqueItem'"):
        p = json.loads(payload)
        block = blocks.get(p['name'])
        if not block:
            continue
        _b, lines5 = en.parse_unique_block(block)
        lt = [en.live_tokens(l) for l in lines5]
        for t in p.get('resolved_targets') or []:
            if t.get('method') == 5 and t.get('status') == 'resolved':
                checked += 1
                if not en.live_text_ok(mod_text.get(f"mod:{t['target_key']}"), lt):
                    flagged += 1
    con.close()
    raw.close()
    assert checked > 4000, checked
    assert flagged == 0, flagged
    print(f'ok: {checked} m5-resolved pairs, all text-true vs current block')


if __name__ == '__main__':
    fns = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for fn in fns:
        fn()
        print(f'{fn.__name__}: OK')
    print(f'{len(fns)} tests passed')
