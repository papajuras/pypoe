from __future__ import annotations

import json
import logging
import time
from queue import Queue, Empty as QueueEmpty
from threading import Thread

from .client import TradeClient
from .ninja import NinjaClient
from .store import Store, _extract_query

logger = logging.getLogger(__name__)
SCAN_INTERVAL = 60
STALE_AFTER = 3600


class PriceFetcher:
    def __init__(self, client: TradeClient, store: Store):
        self._client = client
        self._store = store
        self._ninja = NinjaClient()
        self._queue: Queue[str] = Queue()
        self._running = True

        self._scanner = Thread(target=self._scan_loop, daemon=True, name="price-scanner")
        self._worker = Thread(target=self._work_loop, daemon=True, name="price-worker")
        self._scanner.start()
        self._worker.start()

    def stop(self):
        self._running = False

    def enqueue(self, flip_id: str):
        self._queue.put(flip_id)

    def set_league(self, league: str):
        self._client.league = league

    # ── scanner ─────────────────────────────────────────────────

    def _scan_loop(self):
        while self._running:
            try:
                for fid in self._store.stale_flip_ids(STALE_AFTER):
                    self._queue.put(fid)
            except Exception:
                logger.exception("scan error")
            time.sleep(SCAN_INTERVAL)

    # ── worker ──────────────────────────────────────────────────

    def _work_loop(self):
        while self._running:
            try:
                flip_id = self._queue.get(timeout=1)
            except QueueEmpty:
                continue
            try:
                self._fetch_prices(flip_id)
            except Exception:
                logger.exception("price fetch error for %s", flip_id)

    def _fetch_prices(self, flip_id: str):
        flip = self._store.get(flip_id)
        if not flip:
            return

        league = flip.league
        src_avg, src_cnt = self._fetch_source(flip, league)
        tgt_avg, tgt_cnt = self._fetch_target(flip, league)
        self._store.save_price(flip_id, src_avg, src_cnt, tgt_avg, tgt_cnt)
        logger.info(
            "Priced %s: src=%.1f (%d)  tgt=%.1f (%d)",
            flip.name or flip_id, src_avg, src_cnt, tgt_avg, tgt_cnt,
        )

    def _fetch_source(self, flip, league: str) -> tuple[float, int]:
        if flip.source_type == "ninja":
            return self._ninja_price(flip.source_ninja_item, flip.source_ninja_type, league)
        return self._fetch_source_trade(flip.source_queries)

    def _fetch_target(self, flip, league: str) -> tuple[float, int]:
        if flip.target_type == "ninja":
            return self._ninja_price(flip.target_ninja_item, flip.target_ninja_type, league)
        return self._fetch_target_trade(flip.target_queries)

    # ── ninja pricing ──────────────────────────────────────────

    def _ninja_price(self, item_name: str, item_type: str, league: str) -> tuple[float, int]:
        data = self._ninja.overview(item_type, league)
        divine = self._ninja.divine_rate(league)
        for line in data.get("lines", []):
            if line["id"] == item_name:
                val = line.get("primaryValue", 0) / divine if divine else 0
                cnt = 1 if val > 0 else 0
                return val, cnt
        return 0.0, 0

    # ── trade source: average of cheapest 5 ────────────────────

    def _fetch_source_trade(self, queries: list[str]) -> tuple[float, int]:
        prices = self._collect_divine_prices(queries)
        if not prices:
            return 0.0, 0
        return sum(prices) / len(prices), len(prices)

    # ── trade target: cheapest single listing ──────────────────

    def _fetch_target_trade(self, queries: list[str]) -> tuple[float, int]:
        prices = self._collect_divine_prices(queries)
        if not prices:
            return 0.0, 0
        return min(prices), len(prices)

    # ── shared ─────────────────────────────────────────────────

    def _collect_divine_prices(self, queries: list[str]) -> list[float]:
        all_prices: list[float] = []
        for raw in queries:
            try:
                q = json.loads(_extract_query(raw)[0])
            except json.JSONDecodeError:
                continue

            result = self._client.search(q)
            total = result.get("total", 0)
            if total < 10:
                return []

            ids: list[str] = result.get("result", [])[:5]
            if not ids:
                continue

            items = self._client.fetch(ids).get("result", [])
            for item in items:
                price = item.get("listing", {}).get("price", {})
                if price.get("currency") == "divine":
                    all_prices.append(float(price["amount"]))
        return all_prices
