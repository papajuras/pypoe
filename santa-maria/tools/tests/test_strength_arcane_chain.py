#!/usr/bin/env python3
"""End-to-end golden test: Strength → Iron Will → Arcane Might chain.

Run: python3 tools/tests/test_strength_arcane_chain.py
Walks the full source-backed reasoning chain through the Phase 6 Graph API
(read-only, real cache/ artifacts):

    stat:strength
        --attribute_grants_stat--> stat:melee_physical_damage_+%
        <--sem_relation_binds (M2b from)-- stat:strong_casting (Iron Will)
        --sem_relation_binds (M2b to)--> stat:spell_damage_+%
        --stat_mechanic_operand--> Arcane Might family (6 Stats)
        --stat_mechanic_variant--> canonical family member
        --stat_mechanic_operand (product)--> stat:attack_damage_+%

Every hop is source-backed: Round A artifact (attribute), 4M+5S.2 (semantic
binds), Round C artifact (mechanic operand/variant). No Iron Will special
case: the walk uses only generic edge types.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import phase6_api

MELEE = 'stat:melee_physical_damage_+%'
STRONG_CASTING = 'stat:strong_casting'
SPELL = 'stat:spell_damage_+%'
ATTACK = 'stat:attack_damage_+%'
FAMILY_CANONICAL = 'stat:additive_spell_damage_modifiers_apply_to_attack_damage'
FAMILY_SIZE = 6  # canonical + 150% + at_%_value + wand + retaliation + gem-scoped


def walk(start, edge_types, depth, direction=None):
    f = {'start': start, 'edge_types': edge_types,
         'max_nodes_per_level': 200, 'direction': direction or 'both'}
    r = phase6_api.get_neighbour(depth, f)
    seen = {}
    for lv in r['levels']:
        for e in lv['edges']:
            seen.setdefault((e['type'], e['to']), []).append(lv['depth'])  # 'to' is always the neighbor
    return r, seen


def test_full_chain():
    # hop 1: Strength grants its inherent Melee Physical Damage bonus
    r, seen = walk('stat:strength', ['attribute_grants_stat'], 1)
    assert ('attribute_grants_stat', MELEE) in seen, seen
    # hop 2: Iron Will's stat binds the bonus (from-side)
    r, seen = walk(MELEE, ['sem_relation_binds'], 1)
    assert ('sem_relation_binds', STRONG_CASTING) in seen, seen
    # hop 3: Iron Will transfers the bonus to all Spell Damage (to-side)
    r, seen = walk(STRONG_CASTING, ['sem_relation_binds'], 1)
    assert ('sem_relation_binds', SPELL) in seen, seen
    # hop 4: Spell Damage is the operand of the Arcane Might mechanic family
    r, seen = walk(SPELL, ['stat_mechanic_operand'], 1)
    fam = {t for (t, _), d in seen.items() for _ in d if t == 'stat_mechanic_operand'}
    fam_nodes = {e['to'] for lv in r['levels'] for e in lv['edges']
                 if e['type'] == 'stat_mechanic_operand'}
    assert len(fam_nodes) == FAMILY_SIZE, (len(fam_nodes), fam_nodes)
    assert FAMILY_CANONICAL in fam_nodes
    # hop 5: the family is one mechanic (variants reach the canonical)
    r, seen = walk(FAMILY_CANONICAL, ['stat_mechanic_variant'], 1)
    variants = {e['to'] for lv in r['levels'] for e in lv['edges']}
    assert len(variants) == FAMILY_SIZE - 1, variants
    # hop 6: the mechanic's product is Attack Damage — the canonical member has a
    # direct product edge; every variant has its own product edge (verified in
    # test_stat_mechanics), so the product is reachable from the whole family
    r, seen = walk(FAMILY_CANONICAL, ['stat_mechanic_operand'], 1, direction='out')
    assert ('stat_mechanic_operand', ATTACK) in seen, seen
    assert ('stat_mechanic_operand', SPELL) in seen, seen
    print('ok: full chain traversable — strength →melee_physical ←strong_casting→ '
          'spell_damage ↔operand→ family(6) ↔product→ attack_damage')


if __name__ == '__main__':
    test_full_chain()
    print('ALL PASS')