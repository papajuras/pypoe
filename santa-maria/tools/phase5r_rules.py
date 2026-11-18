#!/usr/bin/env python3
"""Phase 5R — intrinsic engine rules as first-class KB facts.

Two fact classes, kept semantically distinct:

1. NUMERIC attribute -> resource conversions are already canonical in the KB
   as attribute_grants_stat edges (phase5 ext_attribute_grants_stat, golden
   tests test_attribute_grants.py). NOT re-modeled as edges here. Each of the
   six conversions ALSO gets a rule: node so its exception mechanisms
   (suppressed_by flags) have a first-class target — the rule node and the
   edge are both derived from the SAME audited artifact, and verify()
   cross-checks their operand consistency (no drift by construction).

2. DEFAULT ENGINE RULES — qualitative mechanics implemented in the game
   engine / PoB calc code. Each rule: node is extracted FROM SOURCE (PoB
   main-branch Lua at the manifest-pinned commit, verified by regex anchor),
   NEVER inferred from the existence of a RePoE exception stat. Exceptions
   are separate facts bound by directed edges (rule -> other):

     rule_applies_to   rule -> stat/tag   generic applicability target
     rule_negated_by   rule -> stat       exception PREVENTS the default
     rule_modified_by  rule -> stat       exception CHANGES a parameter

   An exception edge is emitted only when the PoB flag consulted inside the
   rule's code region has a name-corresponding KB stat (mapping documented in
   docs/game_rules_inventory.md; each pair resolve-verified against nodes.db).

NOT extracted (fail-fast, documented in docs/game_rules_inventory.md):
- "DoT cannot crit" / "DoT is not a hit": no mechanical anchor in PoB calc
  code; ailment dot-multipliers explicitly carry crit-conditional handling
  (CalcOffence.lua CritBleed/CritPoison/CritIgnite DotMulti). Emitting an
  absolute rule would be pretraining knowledge, not source.
- Low Life 35% / Low Mana 30% thresholds: engine-internal; RePoE carries only
  the override stats; PoB's data.misc.LowPoolThreshold = 0.5 is a modeling
  fallback, not the game rule.

Idempotent: deletes its own rows (rule:* nodes, rule_* edges) and rewrites
meta keys rules_* before inserting. No timestamps — bit-reproducible.

Usage:
  python3 phase5r_rules.py            # project + verify
  python3 phase5r_rules.py --report   # + per-rule edge listing
  python3 phase5r_rules.py --verify-only
"""
import argparse
import json
import re
import sqlite3
from pathlib import Path

TOOL = Path(__file__).resolve().parent
SANTA = TOOL.parent
CACHE = SANTA / 'cache'
DATA = SANTA / 'data'
ARTIFACT = TOOL / 'sources' / 'pob_attribute_mechanics.json'

META_PREFIX = 'rules_'
APPLIES = 'rule_applies_to'
NEGATED = 'rule_negated_by'
MODIFIED = 'rule_modified_by'
RULE_EDGE_TYPES = (APPLIES, NEGATED, MODIFIED)

# Attribute operand nodes used by the canonical attribute_grants_stat edges
# (stat:<attribute>; phase5 ext_attribute_grants_stat, golden-tested).
ATTR_STAT = {'strength': 'stat:strength', 'dexterity': 'stat:dexterity',
             'intelligence': 'stat:intelligence'}

# Attribute QUANTITY nodes the conversion rules also apply to. KB-proven
# attribute quantities: stat:base_<attr> is granted by tree passives named
# after the attribute, stat:additional_<attr> by "+X to <attribute>" item mods
# (RePoE translation). The engine totals these into the stat:<attr> operand;
# that aggregation is not represented, so the rule binds each verified
# quantity node directly (fail-closed if absent).
QUANTITY_NODES = {
    'strength': ['stat:base_strength', 'stat:additional_strength'],
    'dexterity': ['stat:base_dexterity', 'stat:additional_dexterity'],
    'intelligence': ['stat:base_intelligence', 'stat:additional_intelligence'],
}

# PoB suppression-flag name -> GGG stat id. Each pair verified to exist as a
# Stat node at build time (resolve-checked against nodes.db); flags with no
# corresponding KB stat are reported unbound (NoIntBonusToES, DexAccBonusOverride).
FLAG_TO_STAT = {
    'NoStrengthAttributeBonuses': 'gain_no_inherent_bonus_from_strength',
    'NoStrBonusToLife': 'gain_no_maximum_life_from_strength',
    'NoDexterityAttributeBonuses': 'gain_no_inherent_bonus_from_dexterity',
    'NoDexBonusToEvasion': 'gain_no_inherent_evasion_rating_+%_from_dexterity',
    'NoIntelligenceAttributeBonuses': 'gain_no_inherent_bonus_from_intelligence',
    'NoIntBonusToMana': 'gain_no_maximum_mana_from_intelligence',
}

# PoB ES-bypass exception flag -> GGG stat id (ChaosNotBypassEnergyShield,
# CalcDefence.lua inside the '-- Energy Shield bypass' block).
CHAOS_FLAG = 'ChaosNotBypassEnergyShield'
CHAOS_STAT = 'chaos_damage_does_not_bypass_energy_shield'

PROV_ARTIFACT = 'tools/sources/pob_attribute_mechanics.json'


def _manifest_poblua_commit():
    meta = json.loads((DATA / 'manifest.json').read_text()).get('_meta') or {}
    src = (meta.get('sources') or {}).get('poblua') or {}
    commit = src.get('commit')
    assert commit, 'manifest _meta.sources.poblua.commit missing — run phase1_download.py'
    return commit


def _read(rel):
    return (DATA / rel).read_text()


def _line_of(text, pos):
    return text[:pos].count('\n') + 1


def artifact_rules(pob_commit, stats):
    """Rule nodes + edges for the six audited attribute conversions."""
    art = json.loads(ARTIFACT.read_text())
    rules, unbound = [], []
    for m in art['mechanics']:
        attr_stat = ATTR_STAT[m['attribute']]
        res_stat = 'stat:' + m['target_stat']
        assert attr_stat in stats, f'missing attribute stat {attr_stat}'
        assert res_stat in stats, f'missing resource stat {res_stat}'
        qty = [n for n in QUANTITY_NODES[m['attribute']] if n in stats]
        missing_qty = [n for n in QUANTITY_NODES[m['attribute']] if n not in stats]
        for n in missing_qty:
            unbound.append((m['id'], n, 'quantity node absent from KB'))
        neg = []
        for flag in m.get('suppressed_by', []):
            sid = FLAG_TO_STAT.get(flag)
            if sid is None:
                unbound.append((m['id'], flag, 'no name-corresponding KB stat'))
                continue
            nid = 'stat:' + sid
            if nid in stats:
                neg.append(nid)
            else:
                unbound.append((m['id'], flag, f'{nid} absent from KB'))
        rules.append({
            'id': m['id'],
            'name': m['ratio'][0].upper() + m['ratio'][1:],
            'payload': {
                'kind': 'intrinsic_rule',
                'formula': m['formula'],
                'operands': {'attribute': attr_stat,
                             'attribute_quantity_nodes': qty,
                             'resource': res_stat},
                'source': [{'file': PROV_ARTIFACT,
                            'field': f"mechanics[]:{m['id']}",
                            'commit': art['provenance']['pob_commit']}],
                'artifact_commit': art['provenance']['pob_commit'],
            },
            'applies_to': [attr_stat, *qty, res_stat],
            'negated_by': neg,
            'modified_by': [],
        })
    return rules, unbound


def lua_rules(pob_commit, stats):
    """Rule nodes + edges for engine rules anchored in PoB Lua (regex-verified)."""
    rules, unbound = [], []

    # -- rule: chaos_damage_bypasses_energy_shield ---------------------------
    cd = _read('pob-src/src/Modules/CalcDefence.lua')
    block = cd.find('-- Energy Shield bypass')
    flag = re.search(
        r'if not modDB:Flag\(nil, "ChaosNotBypassEnergyShield"\) then', cd)
    add = re.search(r'EnergyShieldBypass"\] = output\[damageType\.\.'
                    r'"EnergyShieldBypass"\] \+ 100', cd)
    assert block >= 0, 'ES-bypass block anchor not found'
    assert flag, 'ChaosNotBypassEnergyShield flag check not found'
    assert add, 'chaos +100 bypass line not found'
    chaos_stat = 'stat:' + CHAOS_STAT
    assert chaos_stat in stats, f'{chaos_stat} absent from KB'
    rules.append({
        'id': 'chaos_damage_bypasses_energy_shield',
        'name': 'Chaos Damage taken bypasses Energy Shield',
        'payload': {
            'kind': 'intrinsic_rule',
            'value': {'energy_shield_bypass_percent': 100},
            'operands': {'damage_type_tag': 'tag:chaos',
                         'pool': 'stat:maximum_energy_shield'},
            'source': [
                {'file': 'pob-src/src/Modules/CalcDefence.lua',
                 'lines': f'{_line_of(cd, block)}-'
                          f'{_line_of(cd, block) + 22}',
                 'anchor': '-- Energy Shield bypass'},
                {'file': 'pob-src/src/Modules/CalcDefence.lua',
                 'lines': f'{_line_of(cd, flag.start())}-'
                          f'{_line_of(cd, add.start())}',
                 'anchor': 'if not modDB:Flag(nil, "ChaosNotBypassEnergyShield")'},
            ],
            'pob_commit': pob_commit,
        },
        'applies_to': ['tag:chaos', 'stat:maximum_energy_shield'],
        'negated_by': [chaos_stat],
        'modified_by': [],
    })

    # -- rule: energy_shield_recharge_delay ----------------------------------
    dl = _read('pob-src/src/Modules/Data.lua')
    val = re.search(r'EnergyShieldRechargeDelay = (\d+),', dl)
    delay = re.search(r'output\.EnergyShieldRechargeDelay = '
                      r'data\.misc\.EnergyShieldRechargeDelay / '
                      r'\(1 \+ modDB:Sum\("INC", nil, '
                      r'"EnergyShieldRechargeFaster"\) / 100\)', cd)
    assert val, 'EnergyShieldRechargeDelay constant not found'
    assert delay, 'recharge-delay formula line not found'
    rules.append({
        'id': 'energy_shield_recharge_delay',
        'name': 'Energy Shield Recharge starts after a delay',
        'payload': {
            'kind': 'intrinsic_rule',
            'value': {'delay_seconds': int(val.group(1))},
            'formula': 'delay = base / (1 + faster_start_of_ES_recharge / 100)',
            'operands': {'pool': 'stat:maximum_energy_shield'},
            'source': [
                {'file': 'pob-src/src/Modules/Data.lua',
                 'lines': str(_line_of(dl, val.start())),
                 'anchor': 'EnergyShieldRechargeDelay = ' + val.group(1)},
                {'file': 'pob-src/src/Modules/CalcDefence.lua',
                 'lines': str(_line_of(cd, delay.start())),
                 'anchor': 'output.EnergyShieldRechargeDelay = '
                           'data.misc.EnergyShieldRechargeDelay / (1 + ...)'},
            ],
            'pob_commit': pob_commit,
        },
        'applies_to': ['stat:maximum_energy_shield'],
        'negated_by': [],
        'modified_by': [],
    })
    return rules, unbound


def project(report=False):
    pob_commit = _manifest_poblua_commit()
    con = sqlite3.connect(CACHE / 'nodes.db')
    stats = {r[0] for r in con.execute("select node_id from nodes where type='Stat'")}
    tags = {r[0] for r in con.execute("select node_id from nodes where type='Tag'")}

    rules, unbound = artifact_rules(pob_commit, stats)
    lua, lua_unbound = lua_rules(pob_commit, stats)
    rules += lua
    unbound += lua_unbound

    con.execute("delete from nodes where node_id like 'rule:%'")
    for r in rules:
        payload = {'name': r['name'], **r['payload']}
        con.execute("insert into nodes(node_id, type, payload) values (?,?,?)",
                    (f"rule:{r['id']}", 'Rule',
                     json.dumps(payload, ensure_ascii=False, sort_keys=True)))
    con.commit()
    con.close()

    con = sqlite3.connect(CACHE / 'edges.db')
    for et in RULE_EDGE_TYPES:
        con.execute("delete from edges where relationship_type=?", (et,))
    edges, skipped = [], []
    for r in rules:
        rid = f"rule:{r['id']}"
        src0 = r['payload']['source'][0]
        field = src0.get('field') or f"lines {src0.get('lines')}"
        for tgt in r['applies_to']:
            pool = tags if tgt.startswith('tag:') else stats
            if tgt not in pool:
                skipped.append((rid, APPLIES, tgt, 'missing target node'))
                continue
            edges.append((rid, tgt, APPLIES, 'confirmed_source_backed', None,
                          'outside_this_vocabulary',
                          json.dumps([{'source_file': src0['file'],
                                       'field': field,
                                       'binding': 'rule_extraction',
                                       'rule_id': r['id']}],
                                     ensure_ascii=False, sort_keys=True)))
        for kind, key in ((NEGATED, 'negated_by'), (MODIFIED, 'modified_by')):
            for tgt in r[key]:
                if tgt not in stats:
                    skipped.append((rid, kind, tgt, 'missing stat node'))
                    continue
                edges.append((rid, tgt, kind, 'confirmed_source_backed', None,
                              'outside_this_vocabulary',
                              json.dumps([{'source_file': src0['file'],
                                           'field': field,
                                           'binding': 'exception_flag_name_match',
                                           'rule_id': r['id']}],
                                         ensure_ascii=False, sort_keys=True)))
    con.executemany("insert into edges(source_node_id, target_node_id, "
                    "relationship_type, confidence_status, secondary_status, "
                    "tier, provenance) values (?,?,?,?,?,?,?)", edges)
    by_type = {et: sum(1 for e in edges if e[2] == et) for et in RULE_EDGE_TYPES}
    con.execute("insert or replace into meta(key, value) values (?,?)",
                (META_PREFIX + 'version', '1'))
    con.execute("insert or replace into meta(key, value) values (?,?)",
                (META_PREFIX + 'nodes', str(len(rules))))
    for et, n in by_type.items():
        con.execute("insert or replace into meta(key, value) values (?,?)",
                    (META_PREFIX + et, str(n)))
    con.commit()
    con.close()

    print(f'rules projection: {len(rules)} rule nodes, {len(edges)} edges '
          f'({by_type[APPLIES]} applies_to, {by_type[NEGATED]} negated_by, '
          f'{by_type[MODIFIED]} modified_by)')
    if unbound:
        print(f'  unbound exceptions ({len(unbound)}):')
        for rid, flag, why in unbound:
            print(f'    {rid}: {flag} — {why}')
    if skipped:
        print(f'  skipped edges: {skipped}')
    if report:
        for r in rules:
            print(f"  rule:{r['id']} — {r['name']}")
            print(f"    applies_to: {', '.join(r['applies_to'])}")
            if r['negated_by']:
                print(f"    negated_by: {', '.join(r['negated_by'])}")
    return len(rules), edges


def verify():
    art = json.loads(ARTIFACT.read_text())
    pob_commit = _manifest_poblua_commit()

    ncon = sqlite3.connect(CACHE / 'nodes.db')
    rules = {r[0]: json.loads(r[1]) for r in ncon.execute(
        "select node_id, payload from nodes where type='Rule'")}
    expect = {f"rule:{m['id']}" for m in art['mechanics']} | {
        'rule:chaos_damage_bypasses_energy_shield',
        'rule:energy_shield_recharge_delay',
    }
    assert set(rules) == expect, f'rule-node drift: +{sorted(set(rules) - expect)} ' \
                                 f'-{sorted(expect - set(rules))}'
    for rid, p in rules.items():
        assert p.get('name') and p.get('kind') == 'intrinsic_rule', rid
        assert p.get('source') and p['source'][0].get('file'), rid
        assert p.get('artifact_commit') or p.get('pob_commit') == pob_commit, rid

    econ = sqlite3.connect(CACHE / 'edges.db')
    edges = econ.execute(
        "select source_node_id, target_node_id, relationship_type from edges "
        f"where relationship_type like 'rule_%'").fetchall()
    nodes = set(rules) | {r[0] for r in ncon.execute('select node_id from nodes')}
    for src, tgt, _et in edges:
        assert src in rules and tgt in nodes, (src, tgt)
    got_applies = {(e[0], e[1]) for e in edges if e[2] == APPLIES}
    expect_applies = set()
    for m in art['mechanics']:
        expect_applies.add((f"rule:{m['id']}", ATTR_STAT[m['attribute']]))
        for n in QUANTITY_NODES[m['attribute']]:
            expect_applies.add((f"rule:{m['id']}", n))
        expect_applies.add((f"rule:{m['id']}", 'stat:' + m['target_stat']))
    expect_applies.add(('rule:chaos_damage_bypasses_energy_shield', 'tag:chaos'))
    expect_applies.add(('rule:chaos_damage_bypasses_energy_shield',
                        'stat:maximum_energy_shield'))
    expect_applies.add(('rule:energy_shield_recharge_delay',
                        'stat:maximum_energy_shield'))
    assert got_applies == expect_applies, \
        f'applies_to drift: +{sorted(got_applies - expect_applies)[:3]} ' \
        f'-{sorted(expect_applies - got_applies)[:3]}'
    # cross-check: every artifact conversion also exists as an
    # attribute_grants_stat edge with the same endpoints (no drift between
    # the rule view and the canonical traversal edges)
    ags = {(e[0], e[1]) for e in econ.execute(
        "select source_node_id, target_node_id from edges "
        "where relationship_type='attribute_grants_stat'")}
    for m in art['mechanics']:
        pair = (ATTR_STAT[m['attribute']], 'stat:' + m['target_stat'])
        assert pair in ags, f'attribute_grants_stat edge missing for {pair}'
        assert (f"rule:{m['id']}", pair[0]) in got_applies
    n_neg = sum(1 for e in edges if e[2] == NEGATED)
    print(f'verify ok: {len(rules)} rule nodes, {len(edges)} rule edges '
          f'({len(got_applies)} applies_to, {n_neg} negated_by), '
          f'artifact/edge operand consistency checked, endpoints all exist')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--report', action='store_true')
    ap.add_argument('--verify-only', action='store_true')
    a = ap.parse_args()
    if not a.verify_only:
        project(report=a.report)
    verify()
