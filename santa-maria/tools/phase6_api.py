#!/usr/bin/env python3
"""Phase 6 — minimal Graph API over the frozen factual graph.

Two calls only (see docs/phase6_api_design.md):

    get_start_seed(filters)       # discovery sample, NOT ranked
    get_neighbour(depth, filters) # BFS frontier from a start node

Reads cache/nodes.db and cache/edges.db. Exposes ONLY confirmed-eligible edges
(confidence_status resolved_not_validated/confirmed/confirmed_source_backed).
Candidate-only resolution lives in node payloads, never in edges, and is never
surfaced here. No ranking, no scoring, no semantic reasoning.

Filter schema is CLOSED: unknown filter names, invalid enum values and out-of-range
integers raise ValueError. An LLM can know the complete legal API surface from this
file + the design doc.

Usage:
  python3 phase6_api.py            # run the discovery-example self-check
  python3 -m tests.test_phase6     # assert-based tests
"""
import json, random, sqlite3
from pathlib import Path

SANTA = Path(__file__).resolve().parents[1]
NODES_DB = SANTA / 'cache' / 'nodes.db'
EDGES_DB = SANTA / 'cache' / 'edges.db'

NODE_TYPES = ['Stat', 'Modifier', 'ModifierGroup', 'UniqueItem', 'Passive',
              'Gem', 'Tag', 'ItemClass']
EDGE_TYPES = ['modifier_grants_stat', 'passive_grants_stat', 'gem_grants_stat',
              'unique_modifier_association', 'gem_has_tag', 'modifier_has_tag',
              'modifier_in_group', 'unique_in_class', 'stat_scales_with',
              'sem_relation_binds', 'attribute_grants_stat',
              'stat_mechanic_variant', 'stat_mechanic_operand']

START_SEED_FILTERS = {'type', 'id_contains', 'name_contains', 'count', 'seed'}
NEIGHBOUR_FILTERS = {'start', 'direction', 'edge_types', 'max_nodes_per_level',
                     'include_provenance', 'carrier_grouping'}
CARRIER_GROUP_CLASSES = {'modifier_grants_stat', 'passive_grants_stat', 'gem_grants_stat',
                         'unique_modifier_association', 'modifier_has_tag', 'gem_has_tag',
                         'modifier_in_group', 'unique_in_class'}

DEFAULT_COUNT = 5
MAX_COUNT = 20
MAX_DEPTH = 6
DEFAULT_MAX_NODES = 50
MAX_NODES_PER_LEVEL = 200


def _node_name(node_id, payload):
    t = node_id.split(':', 1)[0]
    if t == 'stat':
        return payload.get('stat_id')
    if t == 'mod':
        return payload.get('name')
    if t == 'modgroup':
        return payload.get('group')
    if t == 'unique':
        return payload.get('id') or payload.get('name')
    if t == 'passive':
        return payload.get('name')
    if t == 'gem':
        return payload.get('display_name') or (payload.get('active_skill') or {}).get('display_name')
    if t == 'tag':
        return payload.get('tag')
    if t == 'item_class':
        return payload.get('item_class')
    return None


def _compact_provenance(prov):
    """Compact LLM-friendly provenance: source_file + field (+ method for uma)."""
    if not prov:
        return {}
    f = prov[0]
    out = {'source_file': f.get('source_file')}
    if f.get('field'):
        out['field'] = f['field']
    if f.get('method') is not None:
        out['method'] = f['method']
    return out


class GraphDB:
    """Lazy loader of nodes + edges with a closed, validated API."""

    def __init__(self, nodes_db=None, edges_db=None):
        self.nodes_db = Path(nodes_db or NODES_DB)
        self.edges_db = Path(edges_db or EDGES_DB)
        self._nodes = None          # node_id -> (type, payload)
        self._edges = None          # dict of edges per type for adjacency

    def _load_nodes(self):
        if self._nodes is not None:
            return self._nodes
        con = sqlite3.connect(self.nodes_db)
        con.row_factory = sqlite3.Row
        nodes = {}
        for r in con.execute("SELECT node_id, type, payload FROM nodes ORDER BY node_id"):
            nodes[r['node_id']] = (r['type'], json.loads(r['payload']))
        con.close()
        self._nodes = nodes
        return nodes

    def _load_edges(self):
        if self._edges is not None:
            return self._edges
        con = sqlite3.connect(self.edges_db)
        con.row_factory = sqlite3.Row
        # out[type][src] -> list[(tgt, prov)] ; in[type][tgt] -> list[(src, prov)]
        out = {t: {} for t in EDGE_TYPES}
        inn = {t: {} for t in EDGE_TYPES}
        for r in con.execute(
                "SELECT source_node_id, target_node_id, relationship_type, "
                "confidence_status, provenance FROM edges ORDER BY relationship_type, "
                "source_node_id, target_node_id"):
            if r['relationship_type'] not in out:
                continue
            prov = json.loads(r['provenance']) if r['provenance'] else []
            out[r['relationship_type']].setdefault(r['source_node_id'], []).append(
                (r['target_node_id'], prov))
            inn[r['relationship_type']].setdefault(r['target_node_id'], []).append(
                (r['source_node_id'], prov))
        con.close()
        self._edges = (out, inn)
        return out, inn

    # ---- get_start_seed ----

    def get_start_seed(self, filters):
        if not isinstance(filters, dict):
            raise ValueError('filters must be an object (dict)')
        unknown = set(filters) - START_SEED_FILTERS
        if unknown:
            raise ValueError(f"unknown get_start_seed filter(s): {sorted(unknown)}")
        if not (filters.get('type') or filters.get('id_contains') or
                filters.get('name_contains')):
            raise ValueError('get_start_seed requires at least one of type / id_contains / name_contains')
        ftype = filters.get('type')
        if ftype is not None and ftype not in NODE_TYPES:
            raise ValueError(f"invalid type {ftype!r}; must be one of {NODE_TYPES}")
        idc = filters.get('id_contains')
        if idc is not None and not isinstance(idc, str):
            raise ValueError('id_contains must be a string')
        nmc = filters.get('name_contains')
        if nmc is not None and not isinstance(nmc, str):
            raise ValueError('name_contains must be a string')
        count = filters.get('count', DEFAULT_COUNT)
        if not isinstance(count, int) or isinstance(count, bool) or not (1 <= count <= MAX_COUNT):
            raise ValueError(f'count must be an integer in [1..{MAX_COUNT}]')
        seed = filters.get('seed', 0)
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise ValueError('seed must be an integer')

        nodes = self._load_nodes()
        ids = []
        for nid, (typ, payload) in nodes.items():
            if ftype is not None and typ != ftype:
                continue
            if idc is not None and idc not in nid:
                continue
            if nmc is not None:
                name = _node_name(nid, payload)
                if not name or nmc.lower() not in name.lower():
                    continue
            ids.append(nid)
        ids.sort()
        k = min(count, len(ids))
        sample = random.Random(seed).sample(ids, k) if k else []
        return {'seeds': [{'node_id': nid, 'type': nodes[nid][0],
                           'name': _node_name(nid, nodes[nid][1])} for nid in sample]}

    # ---- get_neighbour ----

    def get_neighbour(self, depth, filters):
        if not isinstance(depth, int) or isinstance(depth, bool) or not (1 <= depth <= MAX_DEPTH):
            raise ValueError(f'depth must be an integer in [1..{MAX_DEPTH}]')
        if not isinstance(filters, dict):
            raise ValueError('filters must be an object (dict)')
        unknown = set(filters) - NEIGHBOUR_FILTERS
        if unknown:
            raise ValueError(f"unknown get_neighbour filter(s): {sorted(unknown)}")
        start = filters.get('start')
        if start is None:
            raise ValueError('get_neighbour requires start')
        direction = filters.get('direction', 'both')
        if direction not in ('out', 'in', 'both'):
            raise ValueError("direction must be one of 'out' | 'in' | 'both'")
        et = filters.get('edge_types')
        if et is None:
            edge_types = list(EDGE_TYPES)
        else:
            if not isinstance(et, list) or not et:
                raise ValueError('edge_types must be a non-empty array')
            for t in et:
                if t not in EDGE_TYPES:
                    raise ValueError(f"invalid edge_type {t!r}; must be one of {EDGE_TYPES}")
            edge_types = list(et)
        cap = filters.get('max_nodes_per_level', DEFAULT_MAX_NODES)
        if not isinstance(cap, int) or isinstance(cap, bool) or not (1 <= cap <= MAX_NODES_PER_LEVEL):
            raise ValueError(f'max_nodes_per_level must be an integer in [1..{MAX_NODES_PER_LEVEL}]')
        incl_prov = filters.get('include_provenance', False)
        if not isinstance(incl_prov, bool):
            raise ValueError('include_provenance must be a boolean')
        carrier_grouping = filters.get('carrier_grouping', False)
        if not isinstance(carrier_grouping, bool):
            raise ValueError('carrier_grouping must be a boolean')

        nodes = self._load_nodes()
        if start not in nodes:
            raise ValueError(f"start node not found: {start!r}")
        out, inn = self._load_edges()

        visited = {start}
        frontier = [start]
        levels = []
        truncated = False
        for d in range(1, depth + 1):
            cand = {}   # neighbor -> edge dict (from,to,type,direction,prov)
            gagg = {}   # (carrier_type) -> set(member node ids); terminal virtual groups
            for node in sorted(frontier):
                is_stat = nodes[node][0] == 'Stat'
                for t in edge_types:
                    grouping = carrier_grouping and is_stat and t in CARRIER_GROUP_CLASSES
                    if direction in ('out', 'both'):
                        for (tgt, prov) in out[t].get(node, []):
                            if grouping:
                                gagg.setdefault(nodes[tgt][0], set()).add(tgt)
                                continue
                            if tgt in visited:
                                continue
                            ed = {'from': node, 'to': tgt, 'type': t, 'direction': 'out',
                                  'prov': prov}
                            cur = cand.get(tgt)
                            if cur is None or (t, node) < (cur['type'], cur['from']):
                                cand[tgt] = ed
                    if direction in ('in', 'both'):
                        for (src, prov) in inn[t].get(node, []):
                            if grouping:
                                gagg.setdefault(nodes[src][0], set()).add(src)
                                continue
                            if src in visited:
                                continue
                            ed = {'from': node, 'to': src, 'type': t, 'direction': 'in',
                                  'prov': prov}
                            cur = cand.get(src)
                            if cur is None or (t, node) < (cur['type'], cur['from']):
                                cand[src] = ed
            ordered = [cand[n] for n in sorted(cand)]
            if len(ordered) > cap:
                ordered = ordered[:cap]
                truncated = True
            edges_out = [{'from': e['from'], 'to': e['to'], 'type': e['type'],
                          'direction': e['direction'],
                          **({'provenance': _compact_provenance(e['prov'])} if incl_prov else {})}
                         for e in ordered]
            groups_out = [{'carrier_type': k, 'count': len(v), 'members': sorted(v)}
                          for k, v in sorted(gagg.items())]
            level = {'depth': d, 'edges': edges_out}
            if carrier_grouping:
                level['carrier_groups'] = groups_out
            levels.append(level)
            if not ordered:
                break
            for e in ordered:
                visited.add(e['to'])
            frontier = [e['to'] for e in ordered]
        return {'start': start, 'depth_requested': depth, 'truncated': truncated,
                'levels': levels}


_DEFAULT_GRAPH = None


def get_graph(*args, **kwargs):
    global _DEFAULT_GRAPH
    if _DEFAULT_GRAPH is None:
        _DEFAULT_GRAPH = GraphDB(*args, **kwargs)
    return _DEFAULT_GRAPH


def get_start_seed(filters):
    return get_graph().get_start_seed(filters)


def get_neighbour(depth, filters):
    return get_graph().get_neighbour(depth, filters)


# ---------------------------------------------------------------------------
# discovery-example self-check
# ---------------------------------------------------------------------------

def demo():
    g = get_graph()
    print('== get_start_seed ==')
    print(json.dumps(g.get_start_seed({'type': 'Stat', 'id_contains': 'strength', 'count': 3, 'seed': 0}), indent=1))
    print(json.dumps(g.get_start_seed({'name_contains': 'Whispers', 'count': 2}), indent=1))

    print('\n== 1. Strength -> Fire scaling -> modifiers ==')
    n = g.get_neighbour(2, {'start': 'stat:strength', 'edge_types': ['stat_scales_with', 'modifier_grants_stat'],
                            'include_provenance': True, 'max_nodes_per_level': 200})
    print(json.dumps(n, indent=1))

    print('\n== 2. Unique -> Modifier -> shared Stat -> other Modifier ==')
    print(json.dumps(g.get_neighbour(3, {'start': 'unique:183', 'max_nodes_per_level': 200}), indent=1))

    print('\n== 3. Whispers -> (intelligence) ==')
    print(json.dumps(g.get_neighbour(2, {'start': 'unique:1461', 'max_nodes_per_level': 200}), indent=1))
    print(json.dumps(g.get_neighbour(1, {'start': 'stat:intelligence',
                                         'edge_types': ['stat_scales_with'],
                                         'max_nodes_per_level': 200}), indent=1))

    print('\n== 4. Unholy Trinity -> tags ==')
    print(json.dumps(g.get_neighbour(1, {'start': 'gem:SupportUnholyTrinity',
                                         'edge_types': ['gem_has_tag']}), indent=1))


if __name__ == '__main__':
    demo()
