"""Base-type flip generator for body armours, helmets, gloves, boots.

Usage:
    uv run python -m db.generator              # write to DB
    uv run python -m db.generator --dry-run     # preview only
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "gatherer"))

from gatherer.store import Flip  # noqa: E402
from pypoe.config import read_gatherer_url  # noqa: E402
from pypoe.db.bases import GROUPS, QUALITIES  # noqa: E402
from pypoe.flipper.gatherer_client import GathererClient  # noqa: E402

EPOCH = 0


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


def _high_ilvl_query(category: str, base: str, ilvl: int) -> str:
    return json.dumps({
        "query": {
            "status": {"option": "securable"},
            "type": base,
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
                        "ilvl": {"min": ilvl},
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
                    src_qs.append(_high_ilvl_query(group["category"], base, group["donor_ilvl"]))
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

    items = [flip_dict(f) for f in flips]
    client = GathererClient(read_gatherer_url())
    result = client.seed(items)
    print(f"Seeded {result.get('count', len(flips))} flips via gatherer (removed {result.get('removed', 0)}).")


def flip_dict(f: Flip) -> dict:
    return {
        "name": f.name,
        "source_type": f.source_type,
        "source_queries": f.source_queries,
        "source_ninja_item": f.source_ninja_item,
        "source_ninja_type": f.source_ninja_type,
        "target_type": f.target_type,
        "target_queries": f.target_queries,
        "target_ninja_item": f.target_ninja_item,
        "target_ninja_type": f.target_ninja_type,
        "multiplier": f.multiplier,
        "cost": f.cost,
        "enabled": f.enabled,
        "notes": f.notes,
        "created_at": EPOCH,
        "updated_at": EPOCH,
    }


if __name__ == "__main__":
    main()
