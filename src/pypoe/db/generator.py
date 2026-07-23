"""Base-type flip generator for body armours, helmets, gloves, boots.

Usage:
    uv run python -m db.generator              # write to DB
    uv run python -m db.generator --dry-run     # preview only
"""

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pypoe.flipper.store import DB, Flip, Store  # noqa: E402

EPOCH = 0
QUALITIES = [27, 28, 29, 30]

GROUPS = [
    {
        "name": "body armour",
        "bases": [
            ("Royal Plate", 84, 86),
            ("Syndicate's Garb", 84, 86),
            ("Twilight Regalia", 84, 86),
            ("Conquest Lamellar", 84, 86),
            ("Sacred Chainmail", 84, 86),
            ("Necrotic Armour", 84, 86),
            ("Astral Plate", 84, 86),
            ("Assassin's Garb", 84, 86),
        ],
        "category": None,
        "notes": "",
    },
    {
        "name": "helmet",
        "bases": [
            ("Giantslayer Helmet", 80, 85),
            ("Majestic Pelt", 80, 85),
            ("Lich's Circlet", 80, 85),
            ("Haunted Bascinet", 80, 85),
            ("Penitent Mask", 80, 85),
            ("Divine Crown", 80, 85),
            ("Bone Helmet", 80, 85),
            ("Torturer's Mask", 80, 85),
            ("Blizzard Crown", 80, 85),
        ],
        "category": "armour.helmet",
        "notes": "check Nook's Crown card price",
    },
    {
        "name": "gloves",
        "bases": [
            ("Velour Gloves", 80, 85),
            ("Gripped Gloves", 80, 85),
            ("Trapsetter Gloves", 80, 85),
            ("Warlock Gloves", 80, 85),
            ("Nexus Gloves", 80, 85),
            ("Fingerless Silk Gloves", 80, 85),
            ("Wyvernscale Gauntlets", 80, 85),
            ("Paladin Gloves", 80, 85),
            ("Apothecary's Gloves", 80, 85),
            ("Phantom Mitts", 80, 85),
        ],
        "category": "armour.gloves",
        "notes": "",
    },
    {
        "name": "boots",
        "bases": [
            ("Velour Boots", 80, 85),
            ("Stormrider Boots", 80, 85),
            ("Warlock Boots", 80, 85),
            ("Dreamquest Slippers", 80, 85),
            ("Wyvernscale Boots", 80, 85),
            ("Two-Toned Boots", 80, 85),
            ("Paladin Boots", 80, 85),
            ("Phantom Boots", 80, 85),
            ("Fugitive Boots", 80, 85),
        ],
        "category": "armour.boots",
        "notes": "",
    },
]


def _src_query(base: str, quality: int, ilvl: int) -> str:
    return json.dumps({
        "query": {
            "status": {"option": "securable"},
            "type": base,
            "stats": [{"type": "and", "filters": []}],
            "filters": {
                "misc_filters": {
                    "filters": {
                        "corrupted": {"option": "false"},
                        "mirrored": {"option": "false"},
                        "fractured_item": {"option": "false"},
                        "synthesised_item": {"option": "false"},
                        "quality": {"min": quality},
                        "ilvl": {"min": ilvl},
                    },
                },
            },
        },
        "sort": {"price": "asc"},
    }, separators=(",", ":"))


def _tgt_query(base: str, quality: int, ilvl: int) -> str:
    return json.dumps({
        "query": {
            "status": {"option": "securable"},
            "type": base,
            "stats": [{"type": "and", "filters": []}],
            "filters": {
                "misc_filters": {
                    "filters": {
                        "corrupted": {"option": "false"},
                        "mirrored": {"option": "false"},
                        "fractured_item": {"option": "false"},
                        "synthesised_item": {"option": "false"},
                        "quality": {"min": quality},
                        "ilvl": {"min": ilvl},
                    },
                },
                "trade_filters": {
                    "filters": {
                        "price": {"option": "divine"},
                    },
                },
            },
        },
        "sort": {"price": "asc"},
    }, separators=(",", ":"))


def _high_ilvl_query(category: str) -> str:
    return json.dumps({
        "query": {
            "status": {"option": "securable"},
            "stats": [{"type": "and", "filters": []}],
            "filters": {
                "type_filters": {
                    "filters": {
                        "category": {"option": category},
                        "rarity": {"option": "nonunique"},
                    },
                },
                "misc_filters": {
                    "filters": {
                        "ilvl": {"min": 95},
                        "fractured_item": {"option": "false"},
                        "synthesised_item": {"option": "false"},
                        "mirrored": {"option": "false"},
                        "corrupted": {"option": "false"},
                    },
                },
            },
        },
        "sort": {"price": "asc"},
    }, separators=(",", ":"))


def _flip_name(base: str, quality: int) -> str:
    return f"{base.lower()} {quality}"


MANUAL_FLIPS: list[Flip] = [
    Flip(
        name="kingmaker",
        source_type="query",
        source_queries=['{"query":{"status":{"option":"securable"},"name":"Soul Taker","type":"Siege Axe","stats":[{"type":"and","filters":[]}],"filters":{"misc_filters":{"filters":{"corrupted":{"option":"false"}}}}},"sort":{"price":"asc"}}'],
        target_type="query",
        target_queries=['{"query":{"status":{"option":"securable"},"name":"Kingmaker","type":"Despot Axe","stats":[{"type":"and","filters":[]}],"filters":{"misc_filters":{"filters":{"corrupted":{"option":"false"}}}}},"sort":{"price":"asc"}}'],
        multiplier=1.0, cost=0,
    ),
    Flip(
        name="apothecary",
        source_type="ninja",
        source_ninja_item="the-apothecary",
        source_ninja_type="DivinationCard",
        target_type="query",
        target_queries=['{"query":{"status":{"option":"securable"},"name":"Mageblood","type":"Heavy Belt","stats":[{"type":"and","filters":[]}],"filters":{"misc_filters":{"filters":{"corrupted":{"option":"false"}}}}},"sort":{"price":"asc"}}'],
        multiplier=0.2, cost=0,
    ),
    Flip(
        name="seven years bad luck",
        source_type="ninja",
        source_ninja_item="seven-years-bad-luck",
        source_ninja_type="DivinationCard",
        target_type="ninja",
        target_ninja_item="mirror-shard",
        target_ninja_type="Currency",
        multiplier=0.0769, cost=0,
    ),
]


def generate() -> list[Flip]:
    flips: list[Flip] = []
    for group in GROUPS:
        for base, src_ilvl, tgt_ilvl in group["bases"]:
            for q in QUALITIES:
                name = _flip_name(base, q)
                src_qs = [_src_query(base, q, src_ilvl)]
                if group["category"]:
                    src_qs.append(_high_ilvl_query(group["category"]))
                flips.append(Flip(
                    name=name,
                    source_type="query",
                    source_queries=src_qs,
                    target_type="query",
                    target_queries=[_tgt_query(base, q, tgt_ilvl)],
                    multiplier=0.5,
                    cost=0,
                    enabled=True,
                    notes=group["notes"],
                ))
    flips.extend(MANUAL_FLIPS)
    return flips


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    flips = generate()

    if args.dry_run:
        print(f"Generated {len(flips)} flips:\n")
        current_base = None
        for f in flips:
            base = f.name.rsplit(" ", 2)[0]
            if base != current_base:
                tag = ""
                for g in GROUPS:
                    if any(base == b[0].lower() for b in g["bases"]):
                        tag = f" [{g['name']}]"
                        break
                print(f"\n  [{base}]{tag}")
                current_base = base
            note = f"  notes={f.notes}" if f.notes else ""
            print(f"    {f.name}  (cost={f.cost}, mult={f.multiplier}){note}")
        print(f"\nDry run — not written to DB.")
        return

    store = Store()
    names = {f.name for f in flips}
    existing = [f for f in store.list() if f.name in names]
    if existing:
        for f in existing:
            store.delete(f.id)
        print(f"Removed {len(existing)} existing flips with matching names.")

    ids: list[str] = []
    for f in flips:
        store.put(f)
        ids.append(f.id)

    if ids:
        conn = sqlite3.connect(str(DB))
        ph = ",".join("?" for _ in ids)
        conn.execute(
            f"UPDATE flips SET created_at = ?, updated_at = ? WHERE id IN ({ph})",
            [EPOCH, EPOCH, *ids],
        )
        conn.commit()
        conn.close()

    print(f"Wrote {len(flips)} flips to DB.")


if __name__ == "__main__":
    main()
