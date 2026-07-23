from __future__ import annotations

import json
import logging
import time
from collections import OrderedDict
from threading import Event, Lock, Thread

import requests

from pypoe.config import read_league

from .client import TradeClient
from .ninja import NinjaClient
from .store import Store, _extract_query

logger = logging.getLogger(__name__)
SCAN_INTERVAL = 120
TARGET_QUEUE = 10


def _quality_allowed(name: str) -> bool:
    for q in (27, 28, 29, 30):
        if f" {q} " in f" {name} ":
            from pypoe.db.config import get_meta
            if not get_meta(f"flipper_quality_{q}", True):
                return False
    return True


class PriceFetcher:
    def __init__(self, client: TradeClient, store: Store):
        self._client = client
        self._store = store
        self._ninja = NinjaClient()
        self._pending: OrderedDict[str, None] = OrderedDict()
        self._lock = Lock()
        self._has_items = Event()
        self._running = True
        self._cloudflare_blocked = False
        self._cloudflare_pending_ids: list[str] = []

        self._scanner = Thread(target=self._scan_loop, daemon=True, name="price-scanner")
        self._worker = Thread(target=self._work_loop, daemon=True, name="price-worker")
        self._scanner.start()
        self._worker.start()

    @property
    def queue_size(self) -> int:
        return len(self._pending)

    def stop(self):
        self._running = False

    def enqueue(self, flip_id: str, front: bool = False):
        with self._lock:
            if flip_id in self._pending:
                if front:
                    self._pending.move_to_end(flip_id, last=False)
                return
            self._pending[flip_id] = None
            if front:
                self._pending.move_to_end(flip_id, last=False)
            self._has_items.set()

    def resume_after_cloudflare(self, cf_clearance: str):
        if cf_clearance:
            self._client.session.cookies.set("cf_clearance", cf_clearance, domain="www.pathofexile.com")
        for fid in self._cloudflare_pending_ids:
            self.enqueue(fid)
        self._cloudflare_pending_ids.clear()
        self._cloudflare_blocked = False
        logger.info("Cloudflare challenge resolved, resuming")

    # ── scanner ─────────────────────────────────────────────────

    def _scan_loop(self):
        while self._running:
            try:
                needed = TARGET_QUEUE - self.queue_size
                if needed > 0:
                    fids = self._store.oldest_unpriced(needed)
                    for fid in fids:
                        self.enqueue(fid)
                    logger.info("scan: queued %d, queue now %d", len(fids), self.queue_size)
            except Exception:
                logger.exception("scan error")
            time.sleep(SCAN_INTERVAL)

    # ── worker ──────────────────────────────────────────────────

    def _work_loop(self):
        while self._running:
            if self._cloudflare_blocked:
                time.sleep(1)
                continue

            with self._lock:
                try:
                    flip_id = self._pending.popitem(last=False)[0]
                except KeyError:
                    flip_id = None
                if not self._pending:
                    self._has_items.clear()

            if flip_id is None:
                self._has_items.wait(timeout=1)
                continue

            try:
                self._fetch_prices(flip_id)
            except requests.exceptions.HTTPError as e:
                if (e.response is not None and e.response.status_code == 429
                        and "X-Rate-Limit-Rules" not in e.response.headers):
                    self._cloudflare_blocked = True
                    self._cloudflare_pending_ids.append(flip_id)
                    logger.warning("Cloudflare 429 — pausing %s, solve the challenge", flip_id)
                else:
                    logger.exception("price fetch error for %s", flip_id)
            except Exception:
                logger.exception("price fetch error for %s", flip_id)

    def _fetch_prices(self, flip_id: str):
        flip = self._store.get(flip_id)
        if not flip or not flip.enabled or not _quality_allowed(flip.name):
            return

        league = read_league()
        src_avg, src_cnt = self._fetch_source(flip, league)
        tgt_avg, tgt_cnt = self._fetch_target(flip, league)
        self._store.save_price(flip_id, src_avg, src_cnt, tgt_avg, tgt_cnt)
        flip.updated_at = time.time()
        self._store.put(flip)
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
