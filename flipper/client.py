from __future__ import annotations

import json
import logging
import time
from typing import Callable
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)

BASE = "https://www.pathofexile.com/api/trade"
LIVE_BASE = "wss://www.pathofexile.com/api/trade/live"
TIMEOUT = 30
BUFFER = 1


class TradeClient:
    def __init__(self, user_agent: str, league: str = "Sanctum"):
        self.league = league
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": user_agent, "Accept": "application/json"}
        )
        self._delay = 0.0
        self._min_gap = 1.0
        self._last = time.time()
        self._lock = 0.0

    # ── rate limit ──────────────────────────────────────────────

    def _parse_rate_headers(self, resp: requests.Response):
        rules_str = resp.headers.get("X-Rate-Limit-Rules", "")
        if not rules_str:
            return
        delays: list[float] = []
        for rule_name in rules_str.split(","):
            rule_name = rule_name.strip()
            limits = resp.headers.get(f"X-Rate-Limit-{rule_name}", "")
            if not limits:
                continue
            for tier in limits.split(","):
                parts = tier.strip().split(":")
                if len(parts) < 2:
                    continue
                a, b = int(parts[0]), int(parts[1])
                if a > 0:
                    delays.append(b / a)
        if delays:
            self._delay = max(self._delay, max(delays) + BUFFER)
            self._min_gap = 0.0

    def _enforce(self):
        now = time.time()
        if self._lock > now:
            sleep = self._lock - now
            logger.info("Locked (429 backoff), sleeping %.1fs", sleep)
            time.sleep(sleep)
            self._lock = 0

        gap = max(self._delay, self._min_gap)
        since_last = now - self._last
        if since_last < gap:
            sleep = gap - since_last
            logger.info("Staggering, sleeping %.2fs", sleep)
            time.sleep(sleep)

    def _handle_429(self, resp: requests.Response):
        retry = int(resp.headers.get("Retry-After", 5))
        logger.warning("429 rate limited, retrying after %ds", retry)
        self._lock = time.time() + retry
        time.sleep(retry)
        self._parse_rate_headers(resp)

    # ── public API ──────────────────────────────────────────────

    def search(self, query: dict) -> dict:
        url = f"{BASE}/search/{quote(self.league)}"
        return self._post(url, query)

    def fetch(self, item_ids: list[str]) -> dict:
        ids = ",".join(item_ids[:10])
        url = f"{BASE}/fetch/{quote(ids)}"
        return self._get(url)

    def live(
        self,
        search_id: str,
        on_result: Callable[[dict], None],
        league: str | None = None,
    ):
        import asyncio
        import websockets

        async def _run():
            uri = f"{LIVE_BASE}/{quote(league or self.league)}/{quote(search_id)}"
            async for raw in websockets.connect(uri, user_agent_header=self.session.headers["User-Agent"]):
                msg = json.loads(raw)
                if msg.get("type") == "new":
                    on_result(msg)

        asyncio.run(_run())

    # ── HTTP helpers ────────────────────────────────────────────

    def _post(self, url: str, body: dict) -> dict:
        self._enforce()
        resp = self.session.post(url, json=body, timeout=TIMEOUT)
        self._parse_rate_headers(resp)
        if resp.status_code == 429:
            self._handle_429(resp)
            resp.raise_for_status()
        self._last = time.time()
        resp.raise_for_status()
        return resp.json()

    def _get(self, url: str) -> dict:
        self._enforce()
        resp = self.session.get(url, timeout=TIMEOUT)
        self._parse_rate_headers(resp)
        if resp.status_code == 429:
            self._handle_429(resp)
            resp.raise_for_status()
        self._last = time.time()
        resp.raise_for_status()
        return resp.json()
