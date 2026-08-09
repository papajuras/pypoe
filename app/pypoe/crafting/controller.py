"""Crafting runtime state + actions — single source of truth for the local BFF.

Shared between main.py's keyboard listener and the BFF REST endpoints.
"""

from __future__ import annotations

import logging
import threading

from pypoe.crafting import CraftingSession, Positions, Settings
from pypoe.crafting.actions import file_logger
from pypoe.config import (
    read_screen_mode,
    read_selected,
    set_screen_mode as _set_screen_mode,
    set_selected as _set_selected,
)
from pypoe.db.affixes import (
    get_cluster_implicit_types,
    get_item_type_names,
    load_affixes,
    save_text_for,
)
from pypoe.db.config import (
    delete_profile as _delete_profile,
    get_profile_settings,
    list_profile_names,
    put_profile_settings,
)

logger = logging.getLogger(__name__)

POSITIONS_3SCREENS = Positions(
    alt=[2073, 386], item=[2352, 620], aug=[2213, 453],
    regal=[2486, 368], exalt=[2306, 381], scour=[2489, 551],
    transmute=[1986, 381], delete_beasts=[2033, 340],
)
POSITIONS_2SCREENS = Positions(
    alt=[2071, 289], item=[2263, 477], aug=[2176, 346],
    regal=[2378, 287], exalt=[2249, 291], scour=[2385, 415],
    transmute=[2016, 279], delete_beasts=[2044, 258],
)

SCREEN_MODES = {"3 screens": POSITIONS_3SCREENS, "2 screens": POSITIONS_2SCREENS}

_session: CraftingSession | None = None
_screen_mode: str = read_screen_mode()
_profiles = list_profile_names()
_selected = read_selected()
_profile_name: str = _selected if _selected in _profiles else (_profiles[0] if _profiles else "Default")


def _positions() -> Positions:
    return SCREEN_MODES[_screen_mode]


def _settings() -> Settings:
    cfg = get_profile_settings(_profile_name)
    return Settings(
        use_regal=cfg.get("use_regal", False),
        exalt_after_regal=cfg.get("exalt_after_regal", False),
    )


def _selected_patterns(side: str) -> list[str]:
    cfg = get_profile_settings(_profile_name)
    return cfg.get(side, []) or [" "]


def _resolve_side(side: str) -> list[str]:
    """Return mod_ids for the selected patterns of a profile side (prefix/suffix)."""
    item_type = get_profile_settings(_profile_name).get("item_type", "Ring")
    cluster = get_profile_settings(_profile_name).get("cluster_implicit_type", "")
    prefixes, suffixes = load_affixes(item_type, cluster)
    entries = {a["mod_id"]: a for a in (prefixes if side == "prefixes" else suffixes)}
    mod_ids = []
    for p in _selected_patterns(side):
        if p == " ":
            continue
        low = p.lower()
        exact = [a for a in entries.values() if save_text_for(a) == p or a["name"] == p]
        if exact:
            mod_ids.append(exact[0]["mod_id"])
            continue
        # legacy fallback: old stat-tail patterns (pre tier-ranges) resolve by substring
        mod_ids.extend(a["mod_id"] for a in entries.values() if low in save_text_for(a).lower())
    return mod_ids


def current_state() -> dict:
    cfg = get_profile_settings(_profile_name)
    running = _session is not None and not _session.should_stop
    return {
        "profiles": list_profile_names(),
        "item_types": get_item_type_names(),
        "cluster_types": get_cluster_implicit_types(),
        "screen_modes": list(SCREEN_MODES.keys()),
        "profile": _profile_name,
        "screen_mode": _screen_mode,
        "item_type": cfg.get("item_type", "Ring"),
        "cluster_implicit_type": cfg.get("cluster_implicit_type", ""),
        "use_regal": cfg.get("use_regal", False),
        "exalt_after_regal": cfg.get("exalt_after_regal", False),
        "prefixes": _resolve_side("prefixes"),
        "suffixes": _resolve_side("suffixes"),
        "running": running,
    }


def set_profile(name: str) -> None:
    global _profile_name
    if name in list_profile_names():
        _profile_name = name
        _set_selected(name)


def create_profile(name: str, item_type: str = "Ring") -> None:
    put_profile_settings(name, {"item_type": item_type})
    set_profile(name)


def delete_profile(name: str) -> None:
    global _profile_name
    if name != _profile_name:
        _delete_profile(name)
        return
    _delete_profile(name)
    remaining = list_profile_names()
    _profile_name = remaining[0] if remaining else "Default"
    _set_selected(_profile_name)


def save_settings(**changes) -> None:
    cfg = get_profile_settings(_profile_name)
    for key in ("use_regal", "exalt_after_regal", "item_type", "cluster_implicit_type"):
        if key in changes:
            cfg[key] = changes[key]
    if "prefixes" in changes or "suffixes" in changes:
        prefixes, suffixes = load_affixes(cfg["item_type"], cfg["cluster_implicit_type"])
        entries = {"prefixes": {a["mod_id"]: a for a in prefixes},
                   "suffixes": {a["mod_id"]: a for a in suffixes}}
        for side in ("prefixes", "suffixes"):
            if side in changes:
                patterns = [save_text_for(entries[side][mid]) for mid in changes[side] if mid in entries[side]]
                cfg[side] = patterns or [" "]
    put_profile_settings(_profile_name, cfg)


def set_screen_mode(mode: str) -> None:
    global _screen_mode
    if mode in SCREEN_MODES:
        _screen_mode = mode
        _set_screen_mode(mode)


def start() -> None:
    global _session
    cfg = get_profile_settings(_profile_name)
    item_type = cfg.get("item_type", "Ring")
    cluster = cfg.get("cluster_implicit_type", "")
    prefixes, suffixes = load_affixes(item_type, cluster)
    prefix_entries = {a["mod_id"]: a for a in prefixes}
    suffix_entries = {a["mod_id"]: a for a in suffixes}
    prefix_patterns = [save_text_for(prefix_entries[mid]) for mid in _resolve_side("prefixes")] or [" "]
    suffix_patterns = [save_text_for(suffix_entries[mid]) for mid in _resolve_side("suffixes")] or [" "]
    _session = CraftingSession(
        prefixes=prefix_patterns,
        suffixes=suffix_patterns,
        positions=_positions(),
        settings=_settings(),
    )
    _log = file_logger()
    _log.info(
        "start: profile=%s item_type=%s screen=%s alt_pos=%s prefixes=%s suffixes=%s",
        _profile_name, item_type, _screen_mode, _positions().alt, prefix_patterns, suffix_patterns,
    )

    def _run():
        try:
            _session.run()
        except Exception:
            _log.exception("session thread crashed")

    threading.Thread(target=_run, daemon=True).start()
    _log.info("start: session thread spawned")


def stop() -> None:
    if _session:
        _session.stop()


def delete_beasts() -> None:
    global _session
    logger.info("delete_beasts: screen_mode=%s pos=%s", _screen_mode, _positions().delete_beasts)
    session = CraftingSession(prefixes=[" "], suffixes=[" "], positions=_positions())
    _session = session

    def _run():
        logger.info("delete_beasts thread started")
        try:
            session.delete_beasts_loop()
        except Exception:
            logger.exception("delete_beasts thread crashed")

    threading.Thread(target=_run, daemon=True).start()


def debug() -> dict:
    cfg = get_profile_settings(_profile_name)
    item_type = cfg.get("item_type", "Ring")
    cluster = cfg.get("cluster_implicit_type", "")
    prefixes, suffixes = load_affixes(item_type, cluster)
    prefix_entries = {a["mod_id"]: a for a in prefixes}
    suffix_entries = {a["mod_id"]: a for a in suffixes}
    return {
        "prefixes": [save_text_for(prefix_entries[mid]) for mid in _resolve_side("prefixes")] or [" "],
        "suffixes": [save_text_for(suffix_entries[mid]) for mid in _resolve_side("suffixes")] or [" "],
    }
