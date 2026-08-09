"""Div-card flip scanner — local, poe.ninja + poedb only.

set_cost = card price (ninja exchange overview) x stack (poedb)
reward price = cheapest non-variant stash-item-overview line matching the
reward name (ninja). margin = reward - set_cost.

Excluded: corrupted rewards, generic rewards, variant rewards, unmatched names.
"""

from __future__ import annotations

import argparse

import ninja.divcards as divcards
from ninja import NinjaClient
from ninja.ninja import ITEM_TYPES

LEAGUE = "Allflame"
SET_COST_FLOOR = 50.0   # chaos — skip cards too cheap to matter
MIN_LISTINGS = 3        # reward must have this many ninja listings


def load_reward_prices(client: NinjaClient) -> dict[str, float]:
    """Reward item name -> cheapest chaos price (non-variant, non-corrupted lines)."""
    prices: dict[str, float] = {}
    for t in ITEM_TYPES:
        data = client.item_overview(t, LEAGUE)
        for line in data.get("lines", []):
            if line.get("corrupted"):
                continue
            if line.get("variant"):  # skip multi-roll uniques
                continue
            if line.get("listingCount", 0) < MIN_LISTINGS:
                continue
            name = line.get("name")
            val = line.get("chaosValue")
            if not name or val is None:
                continue
            if name not in prices or val < prices[name]:
                prices[name] = val
    return prices


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="re-fetch poedb mapping")
    args = parser.parse_args()

    client = NinjaClient()

    cards = divcards.fetch(refresh=args.refresh)
    card_prices = {
        l["id"]: l["primaryValue"]
        for l in client.overview("DivinationCard", LEAGUE).get("lines", [])
        if l.get("primaryValue")
    }
    reward_prices = load_reward_prices(client)
    print(f"cards: {len(cards)}  priced: {len(card_prices)}  unique rewards priced: {len(reward_prices)}\n")

    rows = []
    for name, meta in cards.items():
        price = card_prices.get(name.lower().replace(" ", "-").replace("'", ""))
        if not price or not meta["stack"]:
            continue
        if meta["corrupted"]:
            continue
        reward = meta["reward"]
        if not reward:
            continue
        rp = reward_prices.get(reward)
        if rp is None:
            continue
        set_cost = price * meta["stack"]
        if set_cost < SET_COST_FLOOR:
            continue
        margin = rp - set_cost
        rows.append((name, reward, set_cost, rp, margin, price, meta["stack"]))

    rows.sort(key=lambda r: r[4], reverse=True)
    print(f"{'card':28s} {'reward':24s} {'setCost':>9s} {'rewardPx':>9s} {'margin':>9s} {'margin%':>7s}")
    for name, reward, set_cost, rp, margin, price, stack in rows[:30]:
        pct = margin / set_cost * 100 if set_cost else 0
        print(f"{name:28s} {reward:24s} {set_cost:9.1f} {rp:9.1f} {margin:+9.1f} {pct:+6.0f}%")


if __name__ == "__main__":
    main()
