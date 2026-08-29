"""Rare-weapon meta scan over locally pulled ninja_live cycles.

Aggregates main-hand weapons from /character gear JSONs (pulled by
pypoe.ninja_sync) into a compact summary for the SPA "Weapons" tab:

- distinct chars, main-hand rarity split (newest cycle only — a live census)
- per top-skill group, pooled over the last WINDOW_DAYS of cycles:
  rare base distribution, ranked mod templates (frequency + best roll seen),
  exemplar rares w/ mods (deduped across cycles)

Adjusts to whatever data exists: 1 cycle or many.

Usage: from the BFF (GET /api/ninja/weapons) or
PYTHONPATH=app python -m pypoe.ninja_weapons
"""

from __future__ import annotations

import collections
import gzip
import json
import logging
import re
import threading
import time
from datetime import datetime, timedelta, timezone

from pypoe.ninja_sync import DATA_DIR, pull

logger = logging.getLogger(__name__)

FRAME = {0: "Normal", 1: "Magic", 2: "Rare", 3: "Unique"}
WINDOW_DAYS = 5
SKILL_LIST_CAP = 25
# ponytail: minion skills pool many different builds — weapon mods don't
# transfer, so per-skill weapon stats are noise. Popularity stays in `skills`.
EXCLUDED_SKILLS = {"Raise Spectre"}
_cache: dict = {"cycle": None, "data": None}


def _frame(d: dict) -> str:
    ft = d.get("frameTypeId")
    if ft in FRAME.values():
        return str(ft)
    return FRAME.get(d.get("frameType") or 0, "Unknown")


def _tmpl(mod: str) -> str:
    return re.sub(r"\+?\d+(?:\.\d+)?", "#", mod)


def _complete_manifest(p) -> bool:
    """A cycle counts only when its manifest is the collector's final one."""
    try:
        mf = json.loads((p / "manifest.json").read_text())
        return isinstance(mf, dict) and "gem_counts" in mf
    except Exception:
        return False


def _cycles(data_dir, window: timedelta | None) -> list[str]:
    """Cycle ids newest-last; window=None -> all."""
    out = []
    cutoff = datetime.now(timezone.utc) - window if window else None
    if not data_dir.exists():
        return out
    for p in sorted(data_dir.iterdir()):
        if not (p.is_dir() and _complete_manifest(p)):
            continue
        try:
            ts = datetime.strptime(p.name[:15], "%Y%m%dT%H%M%S").replace(
                tzinfo=timezone.utc)
        except ValueError:
            ts = None
        if cutoff and ts and ts < cutoff:
            continue
        out.append(p.name)
    return out


def _load(path) -> dict | None:
    try:
        # ponytail: some synced files are plain JSON despite .gz; accept both
        try:
            text = gzip.open(path, "rt").read()
        except (OSError, EOFError):
            text = path.read_text(encoding="utf-8", errors="replace")
        return json.loads(text)
    except Exception:
        logger.exception("bad char file %s", path)
        return None


def _mods(idata: dict) -> list[dict]:
    return ([{"tag": "F", "text": m} for m in idata.get("fracturedMods") or []]
            + [{"tag": "", "text": m} for m in idata.get("explicitMods") or []]
            + [{"tag": "C", "text": m} for m in idata.get("craftedMods") or []])


def scan(data_dir=DATA_DIR) -> dict | None:
    """Scan local cycles -> summary dict (None if none present)."""
    all_cycles = _cycles(data_dir, None)
    if not all_cycles:
        return None
    cycle = all_cycles[-1]
    if _cache["cycle"] == cycle and _cache["data"] is not None:
        return _cache["data"]

    window = _cycles(data_dir, timedelta(days=WINDOW_DAYS)) or [cycle]

    chars_seen: set[str] = set()          # census: newest cycle only
    rarity = collections.Counter()
    groups: dict[str, dict] = {}          # pooled over the window
    seen_weapons: set[tuple] = set()      # dedup across cycles

    def pool(cycle_id: str) -> None:
        for char_file in sorted((data_dir / cycle_id / "chars").glob("*/*.json.gz")):
            group = char_file.parent.name.replace("%20", " ").split("__")[0]
            if group in EXCLUDED_SKILLS:
                continue
            d = _load(char_file)
            if not d:
                continue
            g = groups.setdefault(group, {
                "bases": collections.Counter(), "rares": [],
                "mods": collections.defaultdict(lambda: [0, None, 0])})
            name = d.get("name") or char_file.stem
            for it in d.get("items", []):
                idata = it.get("itemData") or {}
                if idata.get("inventoryId") != "Weapon":
                    continue
                frame = _frame(idata)
                if frame != "Rare":
                    continue
                base = idata.get("baseType") or idata.get("typeLine")
                mods = _mods(idata)
                key = (name, base, idata.get("ilvl"),
                       tuple(m["text"] for m in mods))
                if key in seen_weapons:
                    continue  # same weapon re-scanned in a later cycle
                seen_weapons.add(key)
                g["bases"][base] += 1
                # ponytail: crafted mods excluded from stats — they're the
                # finisher everyone adds, not a meta signal; fractured counts
                texts = tuple(m["text"] for m in mods if m["tag"] != "C")
                for t in texts:
                    slot = g["mods"][_tmpl(t)]
                    slot[0] += 1
                    score = sum(float(x) for x in re.findall(r"\+?\d+(?:\.\d+)?", t))
                    if score > slot[2]:
                        slot[1], slot[2] = t, score
                g["rares"].append({"char": name, "base": base,
                                   "ilvl": idata.get("ilvl"), "cycle": cycle_id,
                                   "mods": mods})

    for cid in window:
        pool(cid)

    # live census from the newest cycle only
    for char_file in sorted((data_dir / cycle / "chars").glob("*/*.json.gz")):
        d = _load(char_file)
        if not d:
            continue
        name = d.get("name") or char_file.stem
        if name in chars_seen:
            continue  # same char ranked on several asc boards
        chars_seen.add(name)
        for it in d.get("items", []):
            idata = it.get("itemData") or {}
            if idata.get("inventoryId") == "Weapon":
                rarity[_frame(idata)] += 1

    out_groups = {}
    for k, v in sorted(groups.items()):
        n_rares = sum(v["bases"].values())
        out_groups[k] = {
            "bases": v["bases"].most_common(),
            "rares": sorted(v["rares"], key=lambda r: (-r["ilvl"] or 0, r["base"])),
            "mods": sorted(({"tmpl": t, "n": s[0],
                             "best": s[1] if s[0] > 1 else None}
                            for t, s in v["mods"].items()),
                           key=lambda m: -m["n"]),
            "n_rares": n_rares,
        }

    # skill popularity ladder from the newest manifest (ALL gems counted)
    skills = []
    mf = data_dir / cycle / "manifest.json"
    if mf.exists():
        try:
            gem_counts = json.loads(mf.read_text()).get("gem_counts") or {}
            skills = [{"name": n, "count": c,
                       "has_data": n in groups and n not in EXCLUDED_SKILLS,
                       "excluded": n in EXCLUDED_SKILLS}
                      for n, c in sorted(gem_counts.items(), key=lambda t: -t[1])
                      [:SKILL_LIST_CAP]]
        except Exception:
            logger.exception("bad manifest %s", mf)

    data = {
        "cycle": cycle,
        "cycles_used": len(window),
        "window_days": WINDOW_DAYS,
        "chars": len(chars_seen),
        "main_hand": dict(rarity),
        "skills": skills,
        "groups": out_groups,
    }
    _cache.update(cycle=cycle, data=data)
    return data


def run() -> dict | None:
    """Pull new cycles from the gatherer (best effort), then scan. CLI/manual."""
    try:
        from pypoe.config import read_gatherer_url
        from pypoe.flipper.gatherer_client import GathererClient

        pull(GathererClient(read_gatherer_url()))
    except Exception:
        logger.exception("ninja pull failed; scanning local data only")
    return scan()


# ── watchdog: ETag-probe the gatherer every minute, pull only on change ──
_watchdog_started = threading.Event()
_state: dict = {"etag": None}


def _watchdog_loop(interval: int) -> None:
    while True:
        try:
            from pypoe.config import read_gatherer_url
            from pypoe.flipper.gatherer_client import GathererClient

            client = GathererClient(read_gatherer_url())
            changed, etag = client.ninja_cycles_if_changed(_state["etag"])
            if changed:
                logger.info("ninja watchdog: changes detected, pulling")
                from pypoe import ninja_sync
                ninja_sync.sync(client)
                scan()  # refresh the weapon cache
                _state["etag"] = etag
                logger.info("ninja watchdog: synced (etag %s)", etag)
        except Exception:
            logger.exception("ninja watchdog cycle failed")
        time.sleep(interval)


def start_watchdog(interval: int = 60) -> None:
    """Idempotent — starts one daemon thread probing the gatherer."""
    if not _watchdog_started.is_set():
        _watchdog_started.set()
        threading.Thread(target=_watchdog_loop, args=(interval,),
                         daemon=True, name="ninja-watchdog").start()


def _demo() -> None:
    import tempfile
    from pathlib import Path

    def item(ilvl, dot_multi):
        return {"itemData": {"inventoryId": "Weapon", "frameTypeId": "Rare",
                             "baseType": "Void Sceptre", "typeLine": "Void Sceptre",
                             "ilvl": ilvl,
                             "fracturedMods": ["+1 to Level of all Spell Skill Gems"],
                             "explicitMods": [f"{dot_multi}% to Fire Damage over Time Multiplier"],
                             "craftedMods": ["30% increased Damage over Time"]}}

    with tempfile.TemporaryDirectory() as tmp:
        now = datetime.now(timezone.utc)
        payloads = {}
        for age_days, multi in ((2, 38), (0, 41)):
            cyc = (now - timedelta(days=age_days)).strftime("%Y%m%dT%H%M%SZ")
            root = Path(tmp) / cyc / "chars" / "Test%20Skill__Ascendant"
            root.mkdir(parents=True)
            char = {"name": "Tester", "items": [item(86, multi)]}
            raw = gzip.compress(json.dumps(char).encode())
            (root / "tester.json.gz").write_bytes(raw)
            payloads[multi] = raw
            (Path(tmp) / cyc / "manifest.json").write_text(
                json.dumps({"gem_counts": {}}))
        # same weapon-state again on another asc board: must not double-count
        cyc_newest = max(Path(tmp).iterdir(), key=lambda p: p.name)
        dup_dir = cyc_newest / "chars" / "Test%20Skill__Necromancer"
        dup_dir.mkdir(parents=True)
        (dup_dir / "tester.json.gz").write_bytes(payloads[41])
        # excluded skill: collected but never analyzed
        exc = cyc_newest / "chars" / "Raise%20Spectre__Necromancer"
        exc.mkdir(parents=True)
        (exc / "minioner.json.gz").write_bytes(payloads[41])
        # newest manifest drives the popularity ladder
        (cyc_newest / "manifest.json").write_text(json.dumps(
            {"gem_counts": {"Test Skill": 100, "Raise Spectre": 50,
                            "Some Other Skill": 10}}))

        _cache.update(cycle=None, data=None)
        data = scan(Path(tmp))
        assert data and data["cycles_used"] == 2
        assert data["chars"] == 1 and data["main_hand"]["Rare"] == 1
        grp = data["groups"]["Test Skill"]
        assert grp["n_rares"] == 2, "38%->41% are two states, board dup must dedup"
        assert grp["bases"] == [("Void Sceptre", 2)]
        top = next(m for m in grp["mods"]
                   if m["tmpl"] == "#% to Fire Damage over Time Multiplier")
        assert top["n"] == 2 and top["best"] == \
            "41% to Fire Damage over Time Multiplier"
        assert grp["mods"][0]["n"] == 2
        assert grp["rares"][-1]["mods"][1]["text"] == \
            "41% to Fire Damage over Time Multiplier"  # newest variant kept
        assert all(g != "Raise Spectre" for g in data["groups"]), "excluded"
        sk = {s["name"]: s for s in data["skills"]}
        assert [s["name"] for s in data["skills"]] == \
            ["Test Skill", "Raise Spectre", "Some Other Skill"]
        assert sk["Test Skill"]["has_data"] and not sk["Raise Spectre"]["has_data"]
        assert sk["Raise Spectre"]["excluded"] and sk["Test Skill"]["count"] == 100
        print("ninja_weapons demo OK")


if __name__ == "__main__":
    _demo()
    print(json.dumps(run(), indent=1)[:2000])
