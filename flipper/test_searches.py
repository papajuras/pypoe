#!/usr/bin/env uv run
# ruff: noqa: T201
# One-shot: execute two trade searches, show item count + first few prices.

import json
import logging
import time

from flipper.store import _extract_query as eq

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")

SRC_CURL = """curl 'https://www.pathofexile.com/api/trade/search/Mirage' --data-raw '{"query":{"status":{"option":"securable"},"type":"Necrotic Armour","stats":[{"type":"and","filters":[]}],"filters":{"misc_filters":{"filters":{"split":{"option":"false"},"corrupted":{"option":"false"},"mirrored":{"option":"false"},"fractured_item":{"option":"false"},"synthesised_item":{"option":"false"},"quality":{"min":29},"ilvl":{"min":86}}}}},"sort":{"price":"asc"}}'"""

TGT_CURL = """curl 'https://www.pathofexile.com/api/trade/search/Mirage' --data-raw '{"query":{"status":{"option":"securable"},"type":"Necrotic Armour","stats":[{"type":"and","filters":[]}],"filters":{"misc_filters":{"filters":{"split":{"option":"false"},"corrupted":{"option":"false"},"mirrored":{"option":"false"},"fractured_item":{"option":"false"},"synthesised_item":{"option":"false"},"quality":{"min":29},"ilvl":{"min":84}}}}},"sort":{"price":"asc"}}'"""

queries = {"source": eq(SRC_CURL), "target": eq(TGT_CURL)}

# ── use POESESSID from curls ───────────────────────────────────

from flipper.client import TradeClient

client = TradeClient("OAuth pypoe/0.1.0 (test)", league="Mirage")
client.session.cookies.set("POESESSID", "6446f7185ca5fb12aadc8a06ab625ac7", domain="www.pathofexile.com")

for side, raw in queries.items():
    q = json.loads(raw)
    cfg = json.dumps(q, indent=2)
    print(f"\n{'='*60}")
    print(f"  {side.upper()} — {cfg[:120]}...")
    print(f"{'='*60}")

    resp = client.search(q)
    total = resp.get("total", "?")
    ids: list[str] = resp.get("result", [])[:10]
    print(f"  total={total}, showing first {len(ids)} items")

    if ids:
        items_data = client.fetch(ids)
        items = items_data.get("result", [])
        for item in items:
            itm = item.get("item", {})
            listing = item.get("listing", {})
            price = listing.get("price", {})
            print(
                f"    {itm.get('name', '?') or '(no name)'}  "
                f"{itm.get('typeLine', '?')}  "
                f"ilvl={itm.get('ilvl', '?')}  "
                f"q={itm.get('properties', [{}])[0].get('value', '?') if itm.get('properties') else '?'}  "
                f"→ {price.get('amount', '?')} {price.get('currency', '?')}"
            )

print("\nDone.")
