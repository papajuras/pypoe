"""Ninja collector sync + build-emergence detection (local side).

Pulls collected cycles from the gatherer (via its /api/ninja/* API) into
app/pypoe/data/ninja_live/<cycle>/ and diffs consecutive manifests:

- gem enters / leaves top_skills
- any gem jumping >RANK_JUMP ranks (min MIN_COUNT builds to cut noise)
- ascendancy share shifts inside a tracked skill's board

Usage: PYTHONPATH=app python -m pypoe.ninja_sync [--base-url http://pi.local:23467]
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / "data" / "ninja_live"
RANK_JUMP = 10
MIN_COUNT = 200
ASC_SHIFT_PP = 15  # percentage points


def _manifest_path(cycle_dir: Path) -> Path:
    return cycle_dir / "manifest.json"


def _manifest_ok(mf: Path) -> bool:
    """True when the local manifest is a real (non-empty) dict."""
    try:
        return bool(json.loads(mf.read_text()))
    except Exception:
        return False


def pull(client, data_dir: Path = DATA_DIR) -> list[str]:
    """Fetch all cycles we don't have locally. Returns new cycle ids."""
    new = []
    for entry in client.ninja_cycles():
        cycle = entry["cycle"]
        if not entry.get("manifest"):
            continue  # ponytail: gatherer still collecting this cycle
        cdir = data_dir / cycle
        mf = _manifest_path(cdir)
        if mf.exists() and _manifest_ok(mf):
            continue  # have it — files were all fetched before manifest landed
        cdir.mkdir(parents=True, exist_ok=True)
        files = client.ninja_files(cycle)["files"]
        for f in files:
            dest = cdir / f["path"]
            if dest.exists():
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(client.ninja_file(cycle, f["path"]))
        # prefer the server manifest over whatever partial files say
        mf.write_text(json.dumps(entry["manifest"], ensure_ascii=False))
        new.append(cycle)
    return sorted(new)


def _ranks(gem_counts: dict) -> dict:
    order = sorted(gem_counts.items(), key=lambda t: -t[1])
    return {g: i for i, (g, _) in enumerate(order)}


def detect(prev: dict, cur: dict) -> list[dict]:
    """Diff two manifests -> emergence events."""
    events: list[dict] = []
    pt, ct = set(prev.get("top_skills") or []), set(cur.get("top_skills") or [])
    for g in sorted(ct - pt):
        events.append({"type": "gem_entered_top", "gem": g})
    for g in sorted(pt - ct):
        events.append({"type": "gem_left_top", "gem": g})

    pr, cr = _ranks(prev.get("gem_counts") or {}), _ranks(cur.get("gem_counts") or {})
    pc, cc = prev.get("gem_counts") or {}, cur.get("gem_counts") or {}
    for gem, rank in cr.items():
        if gem in pr and pr[gem] - rank >= RANK_JUMP and cc.get(gem, 0) >= MIN_COUNT:
            events.append({"type": "gem_rank_jump", "gem": gem,
                           "from_rank": pr[gem], "to_rank": rank,
                           "count": cc[gem]})

    for skill, cur_board in (cur.get("boards") or {}).items():
        prev_board = (prev.get("boards") or {}).get(skill)
        if not prev_board:
            continue
        pa, ca = prev_board.get("asc") or {}, cur_board.get("asc") or {}
        total_p = sum(pa.values()) or 1
        total_c = sum(ca.values()) or 1
        for asc in set(pa) | set(ca):
            before = 100.0 * pa.get(asc, 0) / total_p
            after = 100.0 * ca.get(asc, 0) / total_c
            if abs(after - before) >= ASC_SHIFT_PP:
                events.append({"type": "asc_share_shift", "gem": skill,
                               "asc": asc, "before_pp": round(before),
                               "after_pp": round(after)})
    return events


def sync(client, data_dir: Path = DATA_DIR) -> dict:
    """Pull missing cycles + write emergence report. Reusable (watchdog/CLI)."""
    data_dir.mkdir(parents=True, exist_ok=True)
    new = pull(client, data_dir)
    cycles = sorted(p.name for p in data_dir.iterdir()
                    if _manifest_path(data_dir / p.name).exists())
    report: dict = {"new_cycles": new, "events": []}
    if len(cycles) >= 2:
        prev = json.loads(_manifest_path(data_dir / cycles[-2]).read_text())
        cur = json.loads(_manifest_path(data_dir / cycles[-1]).read_text())
        report["prev_cycle"] = cycles[-2]
        report["cycle"] = cycles[-1]
        report["events"] = detect(prev, cur)
    out = data_dir / "report.json"
    out.write_text(json.dumps(report, indent=1, ensure_ascii=False))
    return report


def run(base_url: str | None = None) -> dict:
    from pypoe.config import read_gatherer_url
    from pypoe.flipper.gatherer_client import GathererClient

    client = GathererClient(base_url or read_gatherer_url())
    return sync(client)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base-url", default=None)
    args = ap.parse_args()
    r = run(args.base_url)
    print(json.dumps(r, indent=1, ensure_ascii=False))
