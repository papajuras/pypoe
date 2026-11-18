#!/usr/bin/env python3
"""Phase 5I — influenced mods as first-class KB members (v1: six confluence
influences; whispers08 plan, user-confirmed).

Projects the influence/spawn-class facts that the Phase 4 node extraction
carries as opaque spawn_weights tags into LLM-readable form:

  influence:<suffix>       nodes  payload: display_name (pinned source table),
                                  item_classes (from item_classes.json
                                  influence_tags), provenance
  modifier_has_influence   edges  mod -> influence (a spawn_weights tag
                                  '<itemclass_tag>_<suffix>' with weight > 0
                                  where the tag is a known item-class
                                  influence tag)
  influence_spawns_on      edges  influence -> ItemClass (from the SAME
                                  item_classes.json influence_tags list)

Sources (data-derived, no invented facts):
  nodes.db Modifier payloads          spawn_weights[].tag (already extracted)
  nodes.db ItemClass payloads         influence_tags (enriched by extract_nodes)
  tools/sources/influence_names.json  pinned suffix -> display_name table

Fail-closed: a spawn tag whose suffix is not in the pinned table is counted
and skipped (never inferred); weight<=0 rows never bind. Pruned
(highest-tier-only) mods were already removed at extraction, so only retained
mods are projected. Eldritch/Delve/Essence/... pseudo-influences are out of
v1 scope by the pinned table and never inferred here.

Idempotent: deletes its own node namespace (influence:*) and its own edge
types before writing. No timestamps — bit-reproducible.

Usage:
  python3 phase5i_influence.py             # project + verify
  python3 phase5i_influence.py --report    # + per-influence listing
  python3 phase5i_influence.py --verify-only
"""
import argparse
import json
import sqlite3
from pathlib import Path

TOOL = Path(__file__).resolve().parent
SANTA = TOOL.parent
CACHE = SANTA / 'cache'
NAMES = TOOL / 'sources' / 'influence_names.json'

META_PREFIX = 'influence_'
NODE_NS = 'influence:'
EDGE_MOD = 'modifier_has_influence'
EDGE_CLASS = 'influence_spawns_on'
PROV_CLASS = 'pinned_reviewed_source_table'


def load_inputs():
    table = json.loads(NAMES.read_text())
    influences = table['influences']
    assert isinstance(influences, dict) and influences, NAMES
    for s, rec in influences.items():
        assert isinstance(s, str) and isinstance(rec.get('display_name'), str), s
    assert table.get('provenance_class') == PROV_CLASS, NAMES
    return influences


def project(report=False):
    influences = load_inputs()

    nodes_con = sqlite3.connect(CACHE / 'nodes.db')
    classes = {}
    for nid, payload in nodes_con.execute(
            "select node_id, payload from nodes where type='ItemClass'"):
        tags = json.loads(payload).get('influence_tags')
        if isinstance(tags, list):
            classes[nid] = {t for t in tags if isinstance(t, str)}
    con_in = nodes_con

    mod_rows = nodes_con.execute(
        "select node_id, payload from nodes where type='Modifier'").fetchall()
    nodes_con.close()

    # tag -> set(item_class ids); suffix -> set(item_class ids)
    tag2classes, suffix2classes = {}, {}
    for cid, tags in classes.items():
        for t in sorted(tags):
            tag2classes.setdefault(t, set()).add(cid)
            suffix = t.rsplit('_', 1)[1]
            if suffix in influences:
                suffix2classes.setdefault(suffix, set()).add(cid)

    inf_nodes, mod_edges, class_edges = [], [], []
    skipped = {}   # reason -> count
    for suffix in sorted(influences):
        payload = {
            'tag_suffix': suffix,
            'name': influences[suffix]['display_name'],
            'item_classes': sorted(suffix2classes.get(suffix, ())),
            'provenance': {
                'influence_names': 'tools/sources/influence_names.json',
                'item_classes': 'repoe/item_classes.json influence_tags',
                'mods_spawn_weights': 'repoe/mods.json spawn_weights[].tag',
                'provenance_class': PROV_CLASS,
            },
        }
        inf_nodes.append((NODE_NS + suffix, 'Influence',
                          json.dumps(payload, ensure_ascii=False, sort_keys=True)))
        for cid in sorted(suffix2classes.get(suffix, ())):
            class_edges.append((NODE_NS + suffix, cid, EDGE_CLASS, 'confirmed',
                                None, '2', json.dumps(
                                    [{'source_file': 'repoe/item_classes.json',
                                      'field': 'influence_tags',
                                      'provenance_class': PROV_CLASS}],
                                    ensure_ascii=False, sort_keys=True)))

    # modifier side: exact tag membership against the item_class vocabulary
    suffix_of_tag = {t: t.rsplit('_', 1)[1] for t in tag2classes
                     if t.rsplit('_', 1)[1] in influences}
    mod_nodes_con = sqlite3.connect(CACHE / 'nodes.db')
    mod_rows = mod_nodes_con.execute(
        "select node_id, payload from nodes where type='Modifier'").fetchall()
    mod_nodes_con.close()
    for nid, payload_str in mod_rows:
        payload = json.loads(payload_str)
        seen = {}
        for s in payload.get('spawn_weights') or []:
            tag = s.get('tag') if isinstance(s, dict) else None
            if not isinstance(tag, str) or '_' not in tag:
                continue
            weight = s.get('weight')
            if not isinstance(weight, (int, float)) or weight <= 0:
                continue
            if tag not in tag2classes:
                sfx = tag.rsplit('_', 1)[1]
                if sfx in influences:
                    skipped[f'unknown_tag:{tag}'] = \
                        skipped.get(f'unknown_tag:{tag}', 0) + 1
                continue      # not an item-class influence tag (default etc.)
            sfx = suffix_of_tag[tag]
            seen.setdefault(sfx, set()).add(tag)
        for sfx, tags in sorted(seen.items()):
            prov = [{'source_file': 'repoe/mods.json',
                     'field': 'spawn_weights[].tag',
                     'record_key': payload.get('record_key'),
                     'tags': sorted(tags),
                     'provenance_class': PROV_CLASS}]
            mod_edges.append((nid, NODE_NS + sfx, EDGE_MOD, 'confirmed', None,
                              '2', json.dumps(prov, ensure_ascii=False,
                                              sort_keys=True)))
    _write(inf_nodes, mod_edges, class_edges)
    print(f'influence projection: {len(inf_nodes)} influence nodes, '
          f'{len(mod_edges)} {EDGE_MOD} edges, {len(class_edges)} '
          f'{EDGE_CLASS} edges, skipped: '
          f'{json.dumps(skipped, sort_keys=True) if skipped else "{}"}')
    if report:
        for nid, typ, payload in sorted(inf_nodes):
            p = json.loads(payload)
            print(f"  {nid} — {p['name']} — classes: {p['item_classes']}")
    return len(inf_nodes), len(mod_edges), len(class_edges)


def _write(inf_nodes, mod_edges, class_edges):
    con = sqlite3.connect(CACHE / 'nodes.db')
    con.execute("delete from nodes where node_id like ?", (NODE_NS + '%',))
    con.executemany("insert into nodes(node_id, type, payload) values (?,?,?)",
                    inf_nodes)
    con.commit()
    con.close()

    con = sqlite3.connect(CACHE / 'edges.db')
    con.execute("delete from edges where relationship_type in (?, ?)",
                (EDGE_MOD, EDGE_CLASS))
    con.executemany("insert into edges(source_node_id, target_node_id, "
                    "relationship_type, confidence_status, secondary_status, "
                    "tier, provenance) values (?,?,?,?,?,?,?)",
                    mod_edges + class_edges)
    for key, val in (('version', '1'), ('nodes', str(len(inf_nodes))),
                     ('modifier_edges', str(len(mod_edges))),
                     ('class_edges', str(len(class_edges)))):
        con.execute("insert or replace into meta(key, value) values (?,?)",
                    (META_PREFIX + key, val))
    con.commit()
    con.close()


def verify():
    nodes_con = sqlite3.connect(CACHE / 'nodes.db')
    inf = {r[0] for r in nodes_con.execute(
        "select node_id from nodes where node_id like 'influence:%'")}
    nodes_con.close()
    con = sqlite3.connect(CACHE / 'edges.db')
    mod_edges = {(r[0], r[1]) for r in con.execute(
        "select source_node_id, target_node_id from edges "
        "where relationship_type=?", (EDGE_MOD,))}
    class_edges = {(r[0], r[1]) for r in con.execute(
        "select source_node_id, target_node_id from edges "
        "where relationship_type=?", (EDGE_CLASS,))}
    con.close()
    assert inf == {NODE_NS + s for s in load_inputs()}, inf
    for src, tgt in mod_edges:
        assert src.startswith('mod:'), src
        assert tgt in inf, tgt
    for src, tgt in class_edges:
        assert src in inf, src
        assert tgt.startswith('item_class:'), tgt
    return len(inf), len(mod_edges), len(class_edges)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--report', action='store_true')
    ap.add_argument('--verify-only', action='store_true')
    args = ap.parse_args()
    if args.verify_only:
        n, m, c = verify()
        print(f'influence verify OK: {n} nodes, {m} mod edges, {c} class edges')
        return
    project(report=args.report)
    verify()


if __name__ == '__main__':
    main()