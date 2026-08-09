"""Remote data gatherer — owns flips.db, TradeClient, PriceFetcher.

Runs on the remote host (24/7, POESESSID). Exposes a pure JSON REST API
that the local BFF proxies.

Run: python -m gatherer [--port 23467]
"""

from __future__ import annotations

import argparse
import gzip
import json
import logging
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from .client import TradeClient
from .config import data_path, read_league
from .ninja import NinjaClient
from .pricer import PriceFetcher
from .store import Flip, Store

logger = logging.getLogger(__name__)

_store = Store()
_pricer: PriceFetcher | None = None
_server: HTTPServer | None = None

QUALITY_KEYS = [f"flipper_quality_{q}" for q in (27, 28, 29, 30)]


def _init_pricer():
    global _pricer
    if _pricer is not None:
        return
    poesessid = data_path("POESESSID").read_text().strip()
    client = TradeClient("OAuth pypoe/0.1.0 (gatherer)")
    client.session.cookies.set("POESESSID", poesessid, domain="www.pathofexile.com")
    _pricer = PriceFetcher(client, _store)


class GathererHandler(BaseHTTPRequestHandler):

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept-Encoding")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _reply(self, status: int, body: bytes | str, content_type: str = "application/json"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        compressed = gzip.compress(body)
        try:
            self.send_response(status)
            self._cors()
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Vary", "Accept-Encoding")
            self.send_header("Content-Length", str(len(compressed)))
            self.end_headers()
            self.wfile.write(compressed)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass  # client disconnected mid-response; nothing to send to

    def _reply_json(self, status: int, data: object):
        self._reply(status, json.dumps(data, default=str))

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0) or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except json.JSONDecodeError:
            return {}

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        params = parse_qs(parsed.query)

        if path == "/api/flips":
            self._handle_get_flips(params)
        elif path == "/api/history":
            self._handle_get_history(params)
        elif path == "/api/listings":
            self._handle_get_listings(params)
        elif path == "/api/status":
            self._handle_get_status()
        elif path == "/api/league":
            self._reply_json(200, {"league": read_league()})
        elif path == "/api/settings":
            self._handle_get_settings()
        else:
            self._reply_json(404, {"error": "not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/api/flips":
            self._handle_seed()
        elif path.startswith("/api/flips/") and path.endswith("/refresh"):
            flip_id = path[len("/api/flips/"):-len("/refresh")]
            self._handle_refresh(flip_id)
        elif path.startswith("/api/flips/") and path.endswith("/fast"):
            flip_id = path[len("/api/flips/"):-len("/fast")]
            self._handle_set_fast(flip_id)
        elif path == "/api/shutdown":
            self._handle_shutdown()
        else:
            self._reply_json(404, {"error": "not found"})

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/api/settings":
            self._handle_put_settings()
        else:
            self._reply_json(404, {"error": "not found"})

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path.startswith("/api/flips/"):
            flip_id = path[len("/api/flips/"):]
            self._handle_delete(flip_id)
        else:
            self._reply_json(404, {"error": "not found"})

    # ── GET /api/flips?since=<timestamp> ────────────────────────

    def _handle_get_flips(self, params):
        since = 0.0
        raw = params.get("since", [None])[0]
        if raw:
            try:
                since = float(raw)
            except ValueError:
                self._reply_json(400, {"error": "invalid since parameter"})
                return

        flips = _store.list()
        pricing = {f.id: _store.get_price(f.id) for f in flips}
        items = []
        for f in flips:
            if f.updated_at <= since:
                continue
            price = pricing.get(f.id)
            items.append({
                "id": f.id,
                "name": f.name,
                "source_type": f.source_type,
                "source_search_ids": f.source_search_ids,
                "target_type": f.target_type,
                "target_search_ids": f.target_search_ids,
                "multiplier": f.multiplier,
                "cost": f.cost,
                "enabled": f.enabled,
                "fast": f.fast,
                "notes": f.notes,
                "created_at": f.created_at,
                "updated_at": f.updated_at,
                "price": price,
            })

        self._reply_json(200, {
            "flips": items,
            "server_time": time.time(),
            "queue_size": _pricer.queue_size if _pricer else 0,
            "league": read_league(),
        })

    # ── POST /api/flips (seed batch) ────────────────────────────

    def _handle_seed(self):
        body = self._read_body()
        flips = body.get("flips", [])
        if not isinstance(flips, list) or not flips:
            self._reply_json(400, {"error": "expected {\"flips\": [...]}"})
            return

        def _flip(item: dict) -> Flip:
            return Flip(
                name=item.get("name", ""),
                source_type=item.get("source_type", "query"),
                source_queries=item.get("source_queries", []),
                source_search_ids=item.get("source_search_ids", []),
                source_ninja_item=item.get("source_ninja_item", ""),
                source_ninja_type=item.get("source_ninja_type", "DivinationCard"),
                target_type=item.get("target_type", "query"),
                target_queries=item.get("target_queries", []),
                target_search_ids=item.get("target_search_ids", []),
                target_ninja_item=item.get("target_ninja_item", ""),
                target_ninja_type=item.get("target_ninja_type", "DivinationCard"),
                multiplier=item.get("multiplier", 1.0),
                cost=item.get("cost", 0),
                enabled=item.get("enabled", True),
                fast=item.get("fast", True),
                notes=item.get("notes", ""),
                uuid=item.get("uuid", ""),
            )

        removed = 0
        for item in flips:
            flip = _flip(item)
            for f in _store.list():
                if f.name == flip.name and f.id != flip.id:
                    _store.delete(f.id)
                    removed += 1
            _store.put(flip)
            if "created_at" in item or "updated_at" in item:
                created = item.get("created_at", flip.created_at)
                updated = item.get("updated_at", flip.updated_at)
                _store.set_timestamps(flip.id, created, updated)

        self._reply_json(200, {"status": "seeded", "count": len(flips), "removed": removed})

    # ── POST /api/flips/{id}/refresh ────────────────────────────

    def _handle_refresh(self, flip_id: str):
        _init_pricer()
        assert _pricer is not None
        _pricer.enqueue(flip_id, front=True)
        self._reply_json(202, {"status": "queued", "id": flip_id})

    # ── POST /api/flips/{id}/fast — toggle refresh cadence ──────

    def _handle_set_fast(self, flip_id: str):
        fast = bool(self._read_body().get("fast", True))
        if not _store.set_fast(flip_id, fast):
            self._reply_json(404, {"error": "flip not found"})
            return
        self._reply_json(200, {"status": "ok", "fast": fast})

    # ── DELETE /api/flips/{id} ──────────────────────────────────

    def _handle_delete(self, flip_id: str):
        _store.delete(flip_id)
        self._reply_json(200, {"status": "deleted", "id": flip_id})

    # ── GET /api/history?since=<epoch_ms> ──────────────────────

    def _handle_get_history(self, params):
        since = 0
        raw = params.get("since", [None])[0]
        if raw:
            try:
                since = int(raw)
            except ValueError:
                self._reply_json(400, {"error": "invalid since parameter"})
                return
        self._reply_json(200, {"rows": _store.history(since)})

    # ── GET /api/listings?since=<epoch_ms> — target-side listing snapshots ─

    def _handle_get_listings(self, params):
        since = 0
        raw = params.get("since", [None])[0]
        if raw:
            try:
                since = int(raw)
            except ValueError:
                self._reply_json(400, {"error": "invalid since parameter"})
                return
        self._reply_json(200, {"rows": _store.listings_since(since)})

    # ── GET /api/status — combined health + rate-limit + last-refreshed ─

    def _handle_get_status(self):
        data: dict = {"status": "ok", "server_time": time.time(), "league": read_league(), "db_size": _store.db_size_bytes()}
        if _pricer is not None:
            data.update(_pricer._client.metrics())
            data["next_scan_in"] = _pricer.next_scan_in
            data["queue_size"] = _pricer.queue_size
        else:
            data.update({"rate_limits": [], "backoff_remaining": 0.0, "delay": 0.0, "min_gap": 1.0, "next_scan_in": 0.0, "queue_size": 0})
        data["last_refreshed"] = _store.recently_priced(5)
        self._reply_json(200, data)

    # ── GET/PUT /api/settings — quality flags (DB meta) ────────

    def _handle_get_settings(self):
        self._reply_json(200, {k: _store.get_meta(k, True) for k in QUALITY_KEYS})

    def _handle_put_settings(self):
        body = self._read_body()
        for k in QUALITY_KEYS:
            if k in body:
                _store.set_meta(k, bool(body[k]))
        self._reply_json(200, {k: _store.get_meta(k, True) for k in QUALITY_KEYS})

    # ── POST /api/shutdown — graceful stop for deploys ─────────

    def _handle_shutdown(self):
        self._reply_json(200, {"status": "shutting down"})
        _graceful_stop()

    def log_message(self, format, *args):
        if args and not str(args[0]).startswith("200"):
            logger.info("HTTP %s", format % args)


def _graceful_stop():
    """Stop the pricer threads, then stop serving. Called from SIGTERM or /api/shutdown."""
    import threading

    def _stop():
        if _pricer is not None:
            _pricer.stop()
        if _server is not None:
            _server.shutdown()

    threading.Thread(target=_stop, daemon=True).start()


def start_gatherer(port: int = 23467) -> None:
    import signal

    global _server
    _init_pricer()
    _server = HTTPServer(("0.0.0.0", port), GathererHandler)
    signal.signal(signal.SIGTERM, lambda *_: _graceful_stop())
    logger.info("Gatherer listening on 0.0.0.0:%d", port)
    print(f"GATHERER: http://0.0.0.0:{port}")
    try:
        _server.serve_forever()
    except KeyboardInterrupt:
        _graceful_stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Remote data gatherer")
    parser.add_argument("--port", type=int, default=23467)
    args = parser.parse_args()
    start_gatherer(args.port)


if __name__ == "__main__":
    main()
