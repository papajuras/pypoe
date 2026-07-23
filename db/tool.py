#!/usr/bin/env uv run
"""CLI to inspect and manipulate db/flips.db.

Usage:
  uv run python db/tool.py list                               # all flips
  uv run python db/tool.py list --search necrotic             # filter by name/query/ninja
  uv run python db/tool.py dump [--search twilight]           # dump flips as JSON lines
  uv run python db/tool.py dump --id <flip_id> > out.jsonl    # single flip
"""

import json
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).parent / "flips.db"


def conn():
    return sqlite3.connect(str(DB))


def list_flips(search: str | None = None):
    c = conn()
    rows = c.execute("SELECT id, data, created_at, updated_at FROM flips ORDER BY updated_at DESC").fetchall()
    for row in rows:
        data = json.loads(row[1])
        if search and search.lower() not in json.dumps(data).lower():
            continue
        name = data.get("name", "[Unnamed]")
        src_type = data.get("source_type", "query")
        tgt_type = data.get("target_type", "query")
        src = (data.get("source_queries") or data.get("source_urls", []))
        tgt = (data.get("target_queries") or data.get("target_urls", []))
        src_ninja = data.get("source_ninja_item", "")
        tgt_ninja = data.get("target_ninja_item", "")
        print(f"{row[0][:12]}  {name}")
        print(f"   source: {'[ninja] ' + src_ninja if src_type == 'ninja' else str(len(src)) + ' q'}")
        print(f"   target: {'[ninja] ' + tgt_ninja if tgt_type == 'ninja' else str(len(tgt)) + ' q'}")
        mult = data.get("multiplier", 1)
        cost = data.get("cost", 0)
        print(f"   mult={mult}  cost={cost}d")
        p = c.execute("SELECT source_avg, target_avg, fetched_at FROM prices WHERE flip_id = ?", (row[0],)).fetchone()
        if p:
            print(f"   prices: src={p[0]:.2f}  tgt={p[1]:.2f}  @{p[2]}")
        print()


def dump_flips(search: str | None = None, flip_id: str | None = None):
    c = conn()
    if flip_id:
        rows = c.execute("SELECT id, data FROM flips WHERE id = ?", (flip_id,)).fetchall()
    else:
        rows = c.execute("SELECT id, data FROM flips ORDER BY updated_at DESC").fetchall()
    for row in rows:
        data = json.loads(row[1])
        if search and search.lower() not in json.dumps(data).lower():
            continue
        print(json.dumps({"id": row[0], **data}))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    search = None
    flip_id = None

    for i, arg in enumerate(sys.argv[2:]):
        if arg == "--search" and i + 3 < len(sys.argv):
            search = sys.argv[i + 3]
        if arg == "--id" and i + 3 < len(sys.argv):
            flip_id = sys.argv[i + 3]

    for i, arg in enumerate(sys.argv):
        if arg == "--search" and i + 1 < len(sys.argv):
            search = sys.argv[i + 1]
        if arg == "--id" and i + 1 < len(sys.argv):
            flip_id = sys.argv[i + 1]

    if cmd == "list":
        list_flips(search)
    elif cmd == "dump":
        dump_flips(search, flip_id)
    else:
        print(f"Unknown: {cmd}")
        sys.exit(1)
