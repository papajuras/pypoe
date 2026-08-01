import json
import os
import re
import time
from pathlib import Path

import httpx

MODS_URL = "https://github.com/brather1ng/RePoE/raw/refs/heads/master/RePoE/data/mods.json"
TRANSLATIONS_URL = "https://github.com/brather1ng/RePoE/raw/refs/heads/master/RePoE/data/stat_translations.min.json"
CACHE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "db" / "cache"
CACHE_FILE = CACHE_DIR / "mods.json"
TRANSLATIONS_FILE = CACHE_DIR / "stat_translations.json"
MODS_META = CACHE_DIR / "mods_meta.json"

_translations_cache: list | None = None

ITEM_TYPES: dict[str, list[str]] = {
    "Ring": ["ring"],
    "Amulet": ["amulet"],
    "Belt": ["belt"],
    "Quiver": ["quiver"],
    "Gloves": ["gloves"],
    "Shield": ["shield"],
    "Boots": ["boots"],
    "Helmet": ["helmet"],
    "Body Armour": ["body_armour", "str_armour", "dex_armour", "int_armour", "str_dex_armour", "str_int_armour",
                     "dex_int_armour", "str_dex_int_armour"],
    "Wand": ["wand", "one_hand_weapon"],
    "Sceptre": ["sceptre", "one_hand_weapon"],
    "Staff": ["staff", "two_hand_weapon"],
    "Bow": ["bow", "two_hand_weapon"],
    "Dagger/Rune Dagger": ["dagger", "rune_dagger", "one_hand_weapon"],
    "Claw": ["claw", "one_hand_weapon"],
    "1H Sword": ["sword", "rapier", "one_hand_weapon"],
    "2H Sword": ["2h_sword", "sword", "two_hand_weapon"],
    "1H Axe": ["axe", "one_hand_weapon"],
    "2H Axe": ["2h_axe", "axe", "two_hand_weapon"],
    "1H Mace": ["mace", "one_hand_weapon"],
    "2H Mace": ["2h_mace", "mace", "two_hand_weapon"],
    "Warstaff": ["warstaff", "two_hand_weapon"],
    "Focus": ["focus"],
    "Cluster Jewel (Large)": ["expansion_jewel_large"],
    "Cluster Jewel (Medium)": ["expansion_jewel_medium"],
    "Cluster Jewel (Small)": ["expansion_jewel_small"],
}

CLUSTER_IMPLICIT_TYPES: dict[str, str] = {
    "Maximum Life": "affliction_maximum_life",
    "Maximum Mana": "affliction_maximum_mana",
    "Maximum Energy Shield": "affliction_maximum_energy_shield",
    "Armour": "affliction_armour",
    "Evasion": "affliction_evasion",
    "Fire Resistance": "affliction_fire_resistance",
    "Cold Resistance": "affliction_cold_resistance",
    "Lightning Resistance": "affliction_lightning_resistance",
    "Chaos Resistance": "affliction_chaos_resistance",
    "Spell Damage": "affliction_spell_damage",
    "Fire Damage": "affliction_fire_damage",
    "Cold Damage": "affliction_cold_damage",
    "Lightning Damage": "affliction_lightning_damage",
    "Chaos Damage": "affliction_chaos_damage",
    "Physical Damage": "affliction_physical_damage",
    "Elemental Damage": "affliction_elemental_damage",
    "Area Damage": "affliction_area_damage",
    "Projectile Damage": "affliction_projectile_damage",
    "Bow Damage": "affliction_bow_damage",
    "Wand Damage": "affliction_wand_damage",
    "Minion Damage": "affliction_minion_damage",
    "Totem Damage": "affliction_totem_damage",
    "Trap and Mine Damage": "affliction_trap_and_mine_damage",
    "Brand Damage": "affliction_brand_damage",
    "Channelling Skill Damage": "affliction_channelling_skill_damage",
    "Attack Damage": "affliction_attack_damage_",
    "Damage with Herald Skills": "affliction_damage_while_you_have_a_herald",
    "Axe and Sword Damage": "affliction_axe_and_sword_damage",
    "Mace and Staff Damage": "affliction_mace_and_staff_damage",
    "Dagger and Claw Damage": "affliction_dagger_and_claw_damage",
    "Two-Handed Melee Damage": "affliction_damage_with_two_handed_melee_weapons",
    "Dual Wielding Attack Damage": "affliction_attack_damage_while_dual_wielding_",
    "Attack Damage with Shields": "affliction_attack_damage_while_holding_a_shield",
    "Critical Strike Chance": "affliction_critical_chance",
    "Damage over Time Multiplier": "affliction_damage_over_time_multiplier",
    "Physical DoT Multiplier": "affliction_physical_damage_over_time_multiplier",
    "Cold DoT Multiplier": "affliction_cold_damage_over_time_multiplier",
    "Fire DoT Multiplier": "affliction_fire_damage_over_time_multiplier",
    "Chaos DoT Multiplier": "affliction_chaos_damage_over_time_multiplier",
    "Effect of Non-Damaging Ailments": "affliction_effect_of_non-damaging_ailments",
    "Chance to Block": "affliction_chance_to_block",
    "Chance to Dodge Attacks": "affliction_chance_to_dodge_attacks",
    "Flask Duration": "affliction_flask_duration",
    "Life/Mana Recovery from Flasks": "affliction_life_and_mana_recovery_from_flasks",
    "Reservation Efficiency": "affliction_reservation_efficiency_small",
    "Curse Effect": "affliction_curse_effect_small",
    "Warcry Buff Effect": "affliction_warcry_buff_effect",
    "Minion Life": "affliction_minion_life",
    "Minion Damage with Heralds": "affliction_minion_damage_while_you_have_a_herald",
}


def _read_mods() -> dict:
    with open(CACHE_FILE) as f:
        return json.load(f)


def _format_stat(stat_id: str, stat_min, stat_max) -> str:
    display = stat_id.replace("_", " ").replace("%", "% ").strip()
    if stat_min == stat_max:
        return f"{stat_min} {display}"
    return f"{stat_min}-{stat_max} {display}"


def download(force: bool = False) -> bool:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if not force and MODS_META.exists():
        try:
            with open(MODS_META) as f:
                meta = json.load(f)
            age = time.time() - meta.get("downloaded_at", 0)
            if age < 86400:
                return False
        except (json.JSONDecodeError, OSError):
            pass

    for url, path in [(MODS_URL, CACHE_FILE), (TRANSLATIONS_URL, TRANSLATIONS_FILE)]:
        response = httpx.get(url, follow_redirects=True, timeout=60)
        response.raise_for_status()
        with open(path, "wb") as f:
            f.write(response.content)

    with open(MODS_META, "w") as f:
        json.dump({"downloaded_at": time.time()}, f)

    global _translations_cache
    _translations_cache = None
    return True


def is_cached() -> bool:
    return CACHE_FILE.exists() and TRANSLATIONS_FILE.exists()


def get_item_type_names() -> list[str]:
    return list(ITEM_TYPES.keys())


def get_cluster_implicit_types() -> list[str]:
    return sorted(CLUSTER_IMPLICIT_TYPES.keys(), key=str.lower)


INFLUENCE_MAP = {
    "elder": "ELDER",
    "shaper": "SHAPER",
    "crusader": "CRUSADER",
    "adjudicator": "WARLORD",
    "basilisk": "HUNTER",
    "eyrie": "REDEEMER",
}


def _assign_tiers(entries: list[dict]) -> None:
    import re
    groups: dict[tuple, list[dict]] = {}
    for e in entries:
        key = tuple(e["stat_ids"])
        groups.setdefault(key, []).append(e)
    for g in groups.values():
        g.sort(key=lambda e: -max(
            (float(n) for s in e.get("stats", []) for n in re.findall(r"\d+", s)),
            default=0
        ))
        for i, e in enumerate(g, 1):
            e["tier"] = i


def _name_slug(name: str) -> str:
    return name.lower().strip()


def save_text_for(entry: dict) -> str:
    """Return the string to store/match against item text for an affix entry."""
    if entry.get("influence"):
        return entry.get("search_text", entry.get("game_text", ""))
    if any("notable" in sid for sid in entry.get("stat_ids", [])):
        return entry.get("game_text", entry["name"])
    return entry["name"]


def load_affixes(item_type_name: str, cluster_implicit_type: str = "") -> tuple[list[dict], list[dict]]:
    mods = _read_mods()
    tags = ITEM_TYPES.get(item_type_name, [item_type_name.lower().replace(" ", "_")])
    is_cluster = item_type_name.startswith("Cluster Jewel")
    implicit_tag = CLUSTER_IMPLICIT_TYPES.get(cluster_implicit_type, "")

    prefixes = []
    suffixes = []

    for mod_id, m in mods.items():
        if is_cluster:
            if m.get("domain") != "affliction_jewel":
                continue
        elif m.get("domain") != "item":
            continue
        if m.get("generation_type") not in ("prefix", "suffix"):
            continue
        name = m.get("name", "").strip()
        if not name:
            continue

        sw = m.get("spawn_weights", [])
        if is_cluster:
            if not _matches_affliction_jewel(sw, tags, implicit_tag):
                continue
        elif not _matches_item(sw, tags):
            continue

        raw_stats = m.get("stats", [])
        stat_lines = [_format_stat(s["id"], s["min"], s["max"]) for s in raw_stats[:3]]
        stat_ids = [s["id"] for s in raw_stats]

        influence = _get_influence(sw, tags)
        use_game_text = influence or is_cluster
        if use_game_text:
            display_text = format_display_text(raw_stats) if raw_stats else ", ".join(stat_lines[:2])
            search_text = get_search_text(stat_ids) or ", ".join(stat_lines[:2])
        else:
            display_text = ", ".join(stat_lines[:2])
            search_text = ", ".join(stat_lines[:2])

        entry = {
            "name": name,
            "stats": stat_lines,
            "stat_ids": stat_ids,
            "game_text": display_text,
            "search_text": search_text,
            "mod_id": mod_id,
            "required_level": m.get("required_level", 1),
            "influence": influence,
        }

        if m["generation_type"] == "prefix":
            prefixes.append(entry)
        else:
            suffixes.append(entry)

    _assign_tiers(prefixes)
    _assign_tiers(suffixes)
    prefixes.sort(key=lambda x: _name_slug(x["name"]))
    suffixes.sort(key=lambda x: _name_slug(x["name"]))

    return prefixes, suffixes


def _matches_affliction_jewel(spawn_weights: list[dict], tags: list[str], implicit_tag: str) -> bool:
    if not spawn_weights:
        return False
    has_expansion = any(sw["tag"].startswith("expansion_jewel") and sw["weight"] > 0 for sw in spawn_weights)
    has_default = any(sw["tag"] == "default" and sw["weight"] > 0 for sw in spawn_weights)
    if has_expansion:
        for sw in spawn_weights:
            if sw["weight"] > 0 and (sw["tag"] in tags or sw["tag"] == "default"):
                return True
    if has_default:
        return True
    if implicit_tag:
        for sw in spawn_weights:
            if sw["tag"] == implicit_tag and sw["weight"] > 0:
                return True
    return False


def _matches_item(spawn_weights: list[dict], tags: list[str]) -> bool:
    if not spawn_weights:
        return False

    # Exclude mods that explicitly block 1H or 2H weapons
    is_one_hand = "one_hand_weapon" in tags
    is_two_hand = "two_hand_weapon" in tags
    for sw in spawn_weights:
        if is_one_hand and sw["tag"] == "one_hand_weapon" and sw["weight"] <= 0:
            return False
        if is_two_hand and sw["tag"] == "two_hand_weapon" and sw["weight"] <= 0:
            return False

    for sw in spawn_weights:
        if sw["tag"] == "default" or sw["weight"] <= 0:
            continue
        if sw["tag"] in tags:
            return True
        for data_tag in INFLUENCE_MAP:
            suffix = f"_{data_tag}"
            if sw["tag"].endswith(suffix) and sw["tag"][:-len(suffix)] in tags:
                return True
    return any(sw["tag"] == "default" and sw["weight"] > 0 for sw in spawn_weights)


def _get_influence(spawn_weights: list[dict], tags: list[str]) -> str | None:
    for sw in spawn_weights:
        if sw["weight"] <= 0:
            continue
        for data_tag, display in INFLUENCE_MAP.items():
            suffix = f"_{data_tag}"
            if sw["tag"].endswith(suffix) and sw["tag"][:-len(suffix)] in tags:
                return display
    return None


def search_affixes(item_type_name: str, query: str, cluster_implicit_type: str = "") -> tuple[list[dict], list[dict]]:
    prefixes, suffixes = load_affixes(item_type_name, cluster_implicit_type)
    q = query.lower().strip()
    if not q:
        return prefixes, suffixes

    prefixes = [p for p in prefixes if q in p["name"].lower() or q in " ".join(p["stats"]).lower()]
    suffixes = [s for s in suffixes if q in s["name"].lower() or q in " ".join(s["stats"]).lower()]
    return prefixes, suffixes


def _load_translations() -> list:
    global _translations_cache
    if _translations_cache is None:
        with open(TRANSLATIONS_FILE) as f:
            _translations_cache = json.load(f)
    return _translations_cache


def _fill_template(stats: list[dict], template: str, formats: list[str]) -> str:
    result = template
    for i, fmt in enumerate(formats):
        if i < len(stats) and f"{{{i}}}" in result:
            s = stats[i]
            val = f"{s['min']}-{s['max']}" if s['min'] != s['max'] else str(s['min'])
            result = result.replace(f"{{{i}}}", val, 1)
    return result


def _find_translation(stat_ids: list[str], translations: list) -> tuple[dict, int, int] | None:
    """Find a translation entry whose ids appear as a consecutive subsequence of stat_ids.
    Returns (entry, start_index, match_count) or None."""
    for entry in translations:
        eids = entry["ids"]
        if len(eids) > len(stat_ids):
            continue
        for start in range(len(stat_ids) - len(eids) + 1):
            if all(stat_ids[start + j] == eids[j] for j in range(len(eids))):
                return entry, start, len(eids)
    return None


def get_search_text(stat_ids: list[str]) -> str | None:
    """Return text after the last stat placeholder from the first matching translation."""
    translations = _load_translations()
    result = _find_translation(stat_ids, translations)
    if result is None:
        return None
    entry = result[0]
    parts = re.split(r"\{[0-9]+\}", entry["English"][0]["string"])
    return parts[-1].strip() if parts else None


def format_display_text(stats: list[dict]) -> str:
    """Build a display string using game translation templates with values filled in."""
    translations = _load_translations()
    stat_ids = [s["id"] for s in stats]
    parts: list[str] = []
    remaining = list(range(len(stats)))
    while remaining:
        best_start = -1
        best_count = 0
        best_entry = None
        for entry in translations:
            eids = entry["ids"]
            for i in remaining:
                if i + len(eids) <= len(stats) and all(stat_ids[i + j] == eids[j] for j in range(len(eids))):
                    if len(eids) > best_count:
                        best_start = i
                        best_count = len(eids)
                        best_entry = entry
        if best_entry is None:
            break
        slice_stats = stats[best_start:best_start + best_count]
        template = _fill_template(slice_stats, best_entry["English"][0]["string"], best_entry["English"][0].get("format", []))
        parts.append(template)
        for j in range(best_count):
            idx = best_start + j
            if idx in remaining:
                remaining.remove(idx)

    if parts:
        return ", ".join(parts)
    return ", ".join(
        f"{s['min']}-{s['max']}" if s['min'] != s['max'] else str(s['min'])
        for s in stats
    )
