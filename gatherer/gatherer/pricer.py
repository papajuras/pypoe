from __future__ import annotations

import json
import logging
import os
import time
from collections import OrderedDict
from logging.handlers import RotatingFileHandler
from threading import Event, Lock, Thread

import requests

from .config import data_path, read_league

from .client import TradeClient
from .ninja import NinjaClient
from .scheduler import TARGET_QUEUE
from .store import Store, _extract_query

logger = logging.getLogger(__name__)
SCAN_INTERVAL = 30

_LOG_FILE = data_path("flipper.log")


def _setup_file_logging():
    _LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger("gatherer")
    if any(h.baseFilename == str(_LOG_FILE) for h in root.handlers if isinstance(h, RotatingFileHandler)):
        return
    root.setLevel(logging.INFO)
    h = RotatingFileHandler(_LOG_FILE, maxBytes=1_000_000, backupCount=3)
    h.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)-7s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    root.addHandler(h)


def _quality_allowed(store: Store, name: str) -> bool:
    for q in (27, 28, 29, 30):
        if f" {q} " in f" {name} ":
            if not store.get_meta(f"flipper_quality_{q}", True):
                return False
    return True


def _parse_indexed(ts: str) -> int:
    """'2026-08-08T05:26:43Z' → epoch ms. 0 when unparseable."""
    try:
        import datetime

        dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return int(dt.timestamp() * 1000)
    except (ValueError, TypeError):
        return 0


class PriceFetcher:
    def __init__(self, client: TradeClient, store: Store):
        self._client = client
        self._store = store
        _setup_file_logging()
        logger.info("initialised")
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

        self._last_scan = time.time()

    @property
    def next_scan_in(self) -> float:
        return max(0.0, SCAN_INTERVAL - (time.time() - self._last_scan))

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
            self._last_scan = time.time()
            try:
                needed = TARGET_QUEUE - self.queue_size
                if needed > 0:
                    fids = self._store.next_to_price(needed)
                    for fid in fids:
                        self.enqueue(fid)
                    logger.info("scan: queued %d, queue now %d", len(fids), self.queue_size)
                else:
                    logger.debug("scan: queue saturated (needed=%d), skipping", needed)
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
                logger.info("worker: processing %s (queue left=%d)", flip_id, self.queue_size)
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
        if not flip:
            logger.warning("skip: %s not found in store", flip_id)
            return
        if not flip.enabled:
            logger.info("skip: %s disabled", flip.name or flip_id)
            return
        if not _quality_allowed(self._store, flip.name):
            logger.info("skip: %s quality-blocked", flip.name or flip_id)
            return

        logger.info("fetch: %s src=%s tgt=%s", flip.name or flip_id, flip.source_type, flip.target_type)
        league = read_league()
        src_avg, src_cnt, src_chaos_avg, src_chaos_cnt, src_ids, src_total = self._fetch_source(flip, league)
        tgt_avg, tgt_cnt, tgt_ids, tgt_total, tgt_listings = self._fetch_target(flip, league)
        flip.source_search_ids = src_ids
        flip.target_search_ids = tgt_ids
        self._store.save_price(flip_id, src_avg, src_cnt, tgt_avg, tgt_cnt, src_total, tgt_total, src_chaos_avg, src_chaos_cnt)
        if tgt_listings:
            self._store.save_listings(flip_id, int(time.time() * 1000), tgt_listings)
        flip.updated_at = time.time()
        self._store.put(flip)
        logger.info(
            "Priced %s: src=%.1f (%d/%d) [chaos %.1f x%d]  tgt=%.1f (%d/%d)",
            flip.name or flip_id, src_avg, src_cnt, src_total, src_chaos_avg, src_chaos_cnt, tgt_avg, tgt_cnt, tgt_total,
        )

    def _fetch_source(self, flip, league: str) -> tuple[float, int, float, int, list[str], int]:
        if flip.source_type == "ninja":
            avg, cnt = self._ninja_price(flip.source_ninja_item, flip.source_ninja_type, league)
            return avg, cnt, 0.0, 0, [], 0
        return self._fetch_source_trade(flip.source_queries)

    def _fetch_target(self, flip, league: str) -> tuple[float, int, list[str], int, list[dict]]:
        if flip.target_type == "ninja":
            avg, cnt = self._ninja_price(flip.target_ninja_item, flip.target_ninja_type, league)
            return avg, cnt, [], 0, []
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

    def _fetch_source_trade(self, queries: list[str]) -> tuple[float, int, float, int, list[str], int]:
        divine, chaos, search_ids, totals, _ = self._collect_divine_prices(queries)
        d_avg = sum(divine) / len(divine) if divine else 0.0
        d_cnt = len(divine)
        c_avg = sum(chaos) / len(chaos) if chaos else 0.0
        c_cnt = len(chaos)
        return d_avg, d_cnt, c_avg, c_cnt, search_ids, totals[0] if totals else 0

    # ── trade target: cheapest single listing ──────────────────

    def _fetch_target_trade(self, queries: list[str]) -> tuple[float, int, list[str], int, list[dict]]:
        divine, _chaos, search_ids, totals, listings = self._collect_divine_prices(queries, min_total=1)
        if not divine:
            return 0.0, 0, search_ids, totals[0] if totals else 0, listings
        return min(divine), len(divine), search_ids, totals[0] if totals else 0, listings

    # ── shared ─────────────────────────────────────────────────

    def _collect_divine_prices(self, queries: list[str], min_total: int = 0) -> tuple[list[float], list[float], list[str], list[int], list[dict]]:
        divine_prices: list[float] = []
        chaos_prices: list[float] = []
        search_ids: list[str] = []
        totals: list[int] = []
        all_listings: list[dict] = []
        for raw in queries:
            try:
                q = json.loads(_extract_query(raw)[0])
            except json.JSONDecodeError:
                logger.warning("collect: JSON decode error for query hash")
                continue

            result = self._client.search(q)
            total = result.get("total", 0)
            totals.append(int(total))
            logger.debug("collect: search total=%d for query %s", total, raw[:60])
            if min_total and total < min_total:
                logger.info("collect: too few results (%d<%d), skipping", total, min_total)
                return [], [], search_ids, totals, all_listings

            search_id = result.get("id")
            if search_id:
                search_ids.append(search_id)

            ids: list[str] = result.get("result", [])[:10]
            if not ids:
                logger.debug("collect: no result IDs from search")
                continue

            items = self._client.fetch(ids).get("result", [])
            divine_count = 0
            for rank, item in enumerate(items):
                listing = item.get("listing", {})
                price = listing.get("price", {})
                if price.get("currency") == "divine":
                    divine_prices.append(float(price["amount"]))
                    divine_count += 1
                elif price.get("currency") == "chaos":
                    chaos_prices.append(float(price["amount"]))
                indexed = listing.get("indexed", "")
                all_listings.append({
                    "rank": rank,
                    "seller": listing.get("account", {}).get("name", ""),
                    "amount": float(price.get("amount", 0)),
                    "currency": price.get("currency", ""),
                    "indexed_ms": _parse_indexed(indexed),
                    "ilvl": item.get("item", {}).get("ilvl"),
                    "rarity": item.get("item", {}).get("rarity"),
                })
            logger.debug("collect: %d divine listings from %d items", divine_count, len(items))
        return divine_prices, chaos_prices, search_ids, totals, all_listings
