"""poe.ninja client — local copy for the app, extended with item pricing.

Moved from gatherer/gatherer/ninja.py + stash-item-overview support. ETag
caching per poe.ninja's usage guidance (responses cached ~5min, data refreshes
~15min for PoE1). Polite: descriptive UA, conditional requests, low volume.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)
BASE = "https://poe.ninja/poe1/api/economy"
TYPES = {
    "DivinationCard": "/exchange/current/overview",
    "Currency": "/exchange/current/overview",
}
ITEM_TYPES = [
    "UniqueWeapon",
    "UniqueArmour",
    "UniqueAccessory",
    "UniqueFlask",
    "UniqueJewel",
    "UniqueMap",
    "UniqueRelic",
    "ForbiddenJewel",
]
POLL = 900  # 15 min


class NinjaClient:
    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "pypoe/0.1.0 (div-card scanner)"})
        self._cache: dict[str, dict] = {}  # f"{league}:{type_key}" -> {"etag": str, "data": dict, "expires": float, "stale_ok": float}

    def overview(self, type_key: str, league: str = "Standard") -> dict:
        now = time.time()
        cache_key = f"{league}:{type_key}"
        cached = self._cache.get(cache_key)

        if cached and now < cached["expires"]:
            return cached["data"]
        if cached and cached["stale_ok"] > now:
            return cached["data"]

        return self._fetch(f"{BASE}{TYPES[type_key]}?league={league}&type={type_key}", cache_key)

    def item_overview(self, type_key: str, league: str = "Standard") -> dict:
        now = time.time()
        cache_key = f"{league}:{type_key}"
        cached = self._cache.get(cache_key)

        if cached and now < cached["expires"]:
            return cached["data"]
        if cached and cached["stale_ok"] > now:
            return cached["data"]

        return self._fetch(f"{BASE}/stash/current/item/overview?league={league}&type={type_key}", cache_key)

    def leagues(self) -> list[dict]:
        resp = self._session.get(f"{BASE}/leagues", timeout=15)
        resp.raise_for_status()
        return resp.json()

    def _fetch(self, url: str, cache_key: str) -> dict:
        cached = self._cache.get(cache_key) or {}
        headers = {}
        if cached.get("etag"):
            headers["If-None-Match"] = cached["etag"]

        resp = self._session.get(url, headers=headers, timeout=15)
        now = time.time()

        if resp.status_code == 304:
            cached["expires"] = now + POLL
            cached["stale_ok"] = now + POLL + 300
            return cached["data"]

        resp.raise_for_status()
        data = resp.json()

        etag = resp.headers.get("etag", "")
        self._cache[cache_key] = {
            "etag": etag,
            "data": data,
            "expires": now + POLL,
            "stale_ok": now + POLL + 300,
        }
        logger.info("Fetched poe.ninja %s (%d lines)", cache_key, len(data.get("lines", [])))
        return data

    def divine_rate(self, league: str = "Standard") -> float:
        data = self.overview("Currency", league)
        for line in data.get("lines", []):
            if line.get("id") == "divine":
                return line.get("primaryValue", 1.0)
        return 1.0

    def _to_divine(self, lines: list[dict], divine: float) -> list[dict[str, Any]]:
        out = []
        for line in lines:
            val_chaos = line.get("primaryValue", 0)
            val_divine = val_chaos / divine if divine else 0
            if val_divine > 0:
                out.append({
                    "name": line["id"],
                    "chaos_value": val_chaos,
                    "divine_value": val_divine,
                })
        out.sort(key=lambda x: x["name"].lower())
        return out

    def divination_card_options(self, league: str = "Standard") -> list[dict[str, Any]]:
        data = self.overview("DivinationCard", league)
        return self._to_divine(data.get("lines", []), self.divine_rate(league))

    def item_options(self, league: str = "Standard") -> list[dict[str, Any]]:
        divine = self.divine_rate(league)
        out = []
        for t in ["DivinationCard", "Currency"]:
            data = self.overview(t, league)
            for line in data.get("lines", []):
                val_chaos = line.get("primaryValue", 0)
                val_divine = val_chaos / divine if divine else 0
                if val_divine > 0:
                    out.append({
                        "type": t,
                        "name": line["id"],
                        "chaos_value": val_chaos,
                        "divine_value": val_divine,
                    })
        out.sort(key=lambda x: (x["type"], x["name"].lower()))
        return out
