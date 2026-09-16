#!/usr/bin/env python3
"""Phase 8 — Research CLI. Thin JSON wrapper over the research API plus
passthroughs to the existing phase6/phase7 operations.

Subcommands:
  resolve    <query> [--type T]
  carriers   <node_id> [--edge-types a,b,c]
  seed       [--type T] [--id-contains S] [--name-contains S] [--count N] [--seed N]
  neighbour  <start> --depth N [--direction d] [--edge-types a,b,c]
             [--max-nodes-per-level N] [--no-carrier-grouping] [--include-provenance]
  validate   '<build-state json>'   ('-' reads the state from stdin)

Output: one JSON document on stdout. resolve/carriers use the shared research
envelope (see phase8_research.py); seed/neighbour/validate return the
underlying phase6/phase7 result unchanged. Exit code 1 = input error
(envelope.error set or a rejected filter); 0 otherwise — empty results and
ambiguous lookups are valid answers, not errors.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import phase6_api as api
import phase8_research as R
import phase7_build_validity as bv


def _emit(doc):
    print(json.dumps(doc, indent=1))
    return 1 if isinstance(doc, dict) and doc.get('error') else 0


def _csv(value):
    return value.split(',') if value else None


def main(argv=None):
    ap = argparse.ArgumentParser(prog='research.py')
    sub = ap.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('resolve', help='complete node lookup (no sampling)')
    p.add_argument('query')
    p.add_argument('--type', dest='node_type', default=None)

    p = sub.add_parser('carriers', help='what grants/carries this node')
    p.add_argument('node_id')
    p.add_argument('--edge-types', default=None)

    p = sub.add_parser('seed', help='phase6 get_start_seed (sampled discovery)')
    for flag in ('type', 'id-contains', 'name-contains'):
        p.add_argument('--' + flag)
    p.add_argument('--count', type=int)
    p.add_argument('--seed', type=int, default=0)

    p = sub.add_parser('neighbour', help='phase6 get_neighbour (BFS traversal)')
    p.add_argument('start')
    p.add_argument('--depth', type=int, required=True)
    p.add_argument('--direction', default='both')
    p.add_argument('--edge-types')
    p.add_argument('--max-nodes-per-level', type=int)
    p.add_argument('--no-carrier-grouping', action='store_true')
    p.add_argument('--include-provenance', action='store_true')

    p = sub.add_parser('validate', help='phase7 validate_build')
    p.add_argument('state', help="build-state JSON, or '-' for stdin")

    a = ap.parse_args(argv)

    if a.cmd == 'resolve':
        return _emit(R.resolve(a.query, type=a.node_type))

    if a.cmd == 'carriers':
        return _emit(R.carriers(a.node_id, edge_types=_csv(a.edge_types)))

    if a.cmd == 'seed':
        filters = {'seed': a.seed}
        for dest, key in (('type', 'type'), ('id_contains', 'id_contains'),
                          ('name_contains', 'name_contains')):
            v = getattr(a, dest.replace('-', '_'))
            if v is not None:
                filters[key] = v
        if a.count is not None:
            filters['count'] = a.count
        try:
            return _emit(api.get_start_seed(filters))
        except ValueError as e:
            return _emit(R._err('unknown_filter', str(e),
                                filter_echo=filters))

    if a.cmd == 'neighbour':
        filters = {'start': a.start, 'direction': a.direction,
                   'carrier_grouping': not a.no_carrier_grouping,
                   'include_provenance': a.include_provenance}
        if a.edge_types:
            filters['edge_types'] = _csv(a.edge_types)
        if a.max_nodes_per_level is not None:
            filters['max_nodes_per_level'] = a.max_nodes_per_level
        try:
            return _emit(api.get_neighbour(a.depth, filters))
        except ValueError as e:
            return _emit(R._err('unknown_filter', str(e),
                                filter_echo=filters))

    if a.cmd == 'validate':
        raw = sys.stdin.read() if a.state == '-' else a.state
        try:
            return _emit(bv.validate_build(json.loads(raw)))
        except (ValueError, json.JSONDecodeError) as e:
            return _emit(R._err('unknown_filter',
                                f'invalid build-state JSON: {e}'))

    ap.error(f'unknown command {a.cmd!r}')


if __name__ == '__main__':
    sys.exit(main())
