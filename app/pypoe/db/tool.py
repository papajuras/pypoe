#!/usr/bin/env uv run
"""CLI to inspect and manipulate flips via the remote gatherer.

Usage:
  uv run python -m pypoe.db.tool list                          # all flips
  uv run python -m pypoe.db.tool list --search necrotic        # filter by name/query/ninja
  uv run python -m pypoe.db.tool dump [--search twilight]      # dump flips as JSON lines
"""

import json
import sys

from pypoe.config import read_gatherer_url
from pypoe.flipper.gatherer_client import GathererClient


def flips() -> list[dict]:
    data = GathererClient(read_gatherer_url()).list_flips()
    return data.get("flips", [])


def list_flips(search: str | None = None):
    for f in flips():
        blob = json.dumps(f)
        if search and search.lower() not in blob.lower():
            continue
        name = f.get("name", "[Unnamed]")
        uuid_str = f.get("uuid", "")
        src_type = f.get("source_type", "query")
        tgt_type = f.get("target_type", "query")
        src = f.get("source_queries") or []
        tgt = f.get("target_queries") or []
        src_ninja = f.get("source_ninja_item", "")
        tgt_ninja = f.get("target_ninja_item", "")
        print(f"{f.get('id', '')[:12]}  {name}  [{uuid_str[:8]}...]")
        print(f"   source: {'[ninja] ' + src_ninja if src_type == 'ninja' else str(len(src)) + ' q'}")
        print(f"   target: {'[ninja] ' + tgt_ninja if tgt_type == 'ninja' else str(len(tgt)) + ' q'}")
        print(f"   mult={f.get('multiplier', 1)}  cost={f.get('cost', 0)}d")
        p = f.get("price")
        if p:
            print(f"   prices: src={p.get('source_avg', 0):.2f}  tgt={p.get('target_avg', 0):.2f}  @{p.get('fetched_at')}")
        print()


def dump_flips(search: str | None = None):
    for f in flips():
        if search and search.lower() not in json.dumps(f).lower():
            continue
        print(json.dumps(f))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    search = None
    for i, arg in enumerate(sys.argv):
        if arg == "--search" and i + 1 < len(sys.argv):
            search = sys.argv[i + 1]

    if cmd == "list":
        list_flips(search)
    elif cmd == "dump":
        dump_flips(search)
    else:
        print(f"Unknown: {cmd}")
        sys.exit(1)
