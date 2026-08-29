"""BFF — local JSON REST API for the Vue SPA.

Serves crafting endpoints (local clicking/automation) and proxies flipper
endpoints to the remote data gatherer. No static serving.

Run: python main.py (starts this thread)
"""

from __future__ import annotations

import gzip
import json
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from pypoe.config import read_gatherer_url
from pypoe.crafting import controller
from pypoe.crafting.actions import file_logger
from pypoe.db.affixes import load_affixes
from pypoe.flipper import journal as journal_store
from pypoe.flipper.gatherer_client import GathererClient

from ninja import NinjaClient

logger = logging.getLogger(__name__)

_gatherer = GathererClient(read_gatherer_url())

# Latest flip per id, merged across polls. Keeps the FE alive on refresh even
# when the gatherer is briefly unreachable.
_flip_cache: dict[str, dict] = {}
_cache_lock = threading.Lock()
_last_queue = 0
_last_league = ""
_last_server_time = 0.0

# In-flight manual refreshes: flip id -> {"baseline": updated_at, "requested_at": t}.
# Cleared when the re-priced flip's updated_at passes the baseline.
_REFRESH_TTL = 600  # leak-guard for never-completing refreshes
_refreshing: dict[str, dict] = {}

# Cached cloud responses — the gatherer is only queried on this interval.
_SYNC_INTERVAL = 3
_settings_cache: dict = {}


class APIHandler(BaseHTTPRequestHandler):

    # ── CORS ────────────────────────────────────────────────────

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept-Encoding")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    # ── gzip reply ──────────────────────────────────────────────

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

    # ── routing ─────────────────────────────────────────────────

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        params = parse_qs(parsed.query)

        if path == "/api/flips":
            self._proxy_get(path, params)
        elif path == "/api/status":
            self._proxy_get(path, params)
        elif path == "/api/league":
            self._proxy_get(path, params)
        elif path == "/api/settings":
            self._proxy_get(path, params)
        elif path == "/api/ninja/cycles":
            self._proxy_ninja_cycles()
        elif path == "/api/ninja/weapons":
            from pypoe import ninja_weapons
            data = ninja_weapons.scan()  # watchdog owns pulling
            self._reply_json(200, data) if data is not None else \
                self._reply_json(503, {"error": "no ninja cycles available"})
        elif path.startswith("/api/ninja/") and path.endswith("/files"):
            self._proxy_ninja_files(path[len("/api/ninja/"):-len("/files")])
        elif path.startswith("/api/ninja/") and path.endswith("/file"):
            self._proxy_ninja_file(path[len("/api/ninja/"):-len("/file")],
                                   params.get("path", [""])[0])
        elif path == "/api/crafting/state":
            self._reply_json(200, controller.current_state())
        elif path == "/api/crafting/profiles":
            self._reply_json(200, {"profiles": controller.current_state()["profiles"]})
        elif path == "/api/crafting/affixes":
            self._handle_get_affixes(params)
        elif path == "/api/crafting/debug":
            self._reply_json(200, controller.debug())
        elif path == "/api/crafting/counters":
            self._reply_json(200, controller.counters())
        elif path == "/api/journal":
            self._reply_json(200, {
                "records": journal_store.list_all(),
                "definitions": journal_store.definitions(),
                "league": _last_league or "Standard",
            })
        elif path == "/api/analysis":
            self._handle_analysis(params)
        else:
            self._reply_json(404, {"error": "not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        body = self._read_body()

        if path.startswith("/api/flips/") and path.endswith("/refresh"):
            flip_id = path[len("/api/flips/"):-len("/refresh")]
            self._proxy_post(path, flip_id)
        elif path.startswith("/api/flips/") and path.endswith("/enabled"):
            flip_id = path[len("/api/flips/"):-len("/enabled")]
            self._proxy_set_enabled(flip_id, body)
        elif "/sources/" in path and path.endswith("/priced"):
            flip_id = path[len("/api/flips/"):].split("/sources/")[0]
            idx = int(path.split("/sources/")[1][:-len("/priced")])
            self._proxy_set_source_priced(flip_id, idx, body)
        elif path == "/api/flips/refresh-all":
            self._handle_refresh_all()
        elif path == "/api/crafting/start":
            file_logger().info("crafting start POST received")
            controller.start()
            self._reply_json(200, {"status": "started"})
        elif path == "/api/crafting/stop":
            controller.stop()
            self._reply_json(200, {"status": "stopped"})
        elif path == "/api/crafting/delete-beasts":
            logger.info("crafting delete-beasts request")
            controller.delete_beasts()
            self._reply_json(200, {"status": "deleting"})
        elif path == "/api/crafting/profile":
            controller.set_profile(body.get("name", ""))
            self._reply_json(200, {"status": "ok", "profile": controller.current_state()["profile"]})
        elif path == "/api/crafting/profiles":
            controller.create_profile(body.get("name", ""), body.get("item_type", "Ring"))
            self._reply_json(200, {"status": "created", "profile": body.get("name", "")})
        elif path == "/api/crafting/settings":
            controller.save_settings(**body)
            self._reply_json(200, {"status": "ok"})
        elif path == "/api/crafting/screen-mode":
            controller.set_screen_mode(body.get("mode", ""))
            self._reply_json(200, {"status": "ok"})
        elif path == "/api/journal":
            base = body.get("base")
            quality = body.get("quality")
            if not base or quality is None:
                self._reply_json(400, {"error": "base and quality required"})
                return
            cost = body.get("cost")
            income = body.get("income")
            rid = journal_store.add(
                _last_league or "Standard",
                base,
                int(quality),
                float(cost) if cost not in (None, "") else None,
                float(income) if income not in (None, "") else None,
                body.get("note", ""),
            )
            self._reply_json(200, {"id": rid})
        else:
            self._reply_json(404, {"error": "not found"})

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path.startswith("/api/flips/"):
            flip_id = path[len("/api/flips/"):]
            self._proxy_delete(path, flip_id)
        elif path.startswith("/api/crafting/profiles/"):
            name = path[len("/api/crafting/profiles/"):]
            controller.delete_profile(name)
            self._reply_json(200, {"status": "deleted", "name": name})
        elif path.startswith("/api/journal/"):
            rid = int(path[len("/api/journal/"):])
            ok = journal_store.delete(rid)
            self._reply_json(200 if ok else 404, {"status": "ok" if ok else "not found"})
        else:
            self._reply_json(404, {"error": "not found"})

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/api/settings":
            self._proxy_put(path, self._read_body())
        elif path.startswith("/api/journal/"):
            rid = int(path[len("/api/journal/"):])
            body = self._read_body()
            kwargs = {}
            if "cost" in body:
                kwargs["cost"] = float(body["cost"]) if body["cost"] not in (None, "") else None
            if "income" in body:
                kwargs["income"] = float(body["income"]) if body["income"] not in (None, "") else None
            if "note" in body:
                kwargs["note"] = body["note"]
            ok = journal_store.update(rid, **kwargs)
            self._reply_json(200 if ok else 404, {"status": "ok" if ok else "not found"})
        else:
            self._reply_json(404, {"error": "not found"})

    # ── routing ─────────────────────────────────────────────────

    def _proxy_get(self, path: str, params: dict):
        if path == "/api/flips":
            since = 0.0
            raw = params.get("since", [None])[0]
            if raw:
                try:
                    since = float(raw)
                except ValueError:
                    self._reply_json(400, {"error": "invalid since parameter"})
                    return
            self._reply_json(200, _cache_payload(since))
        elif path == "/api/status":
            try:
                self._reply_json(200, _gatherer.status())
            except Exception:
                logger.exception("gatherer proxy failed for GET %s", path)
                self._reply_json(502, {"error": "gatherer unreachable"})
        elif path == "/api/league":
            try:
                self._reply_json(200, _gatherer.league())
            except Exception:
                logger.exception("gatherer proxy failed for GET %s", path)
                self._reply_json(502, {"error": "gatherer unreachable"})
        elif path == "/api/settings":
            self._reply_json(200, _settings_cache)
        else:
            self._reply_json(404, {"error": "not found"})

    def _proxy_ninja_cycles(self):
        try:
            self._reply_json(200, _gatherer.ninja_cycles())
        except Exception:
            logger.exception("gatherer proxy failed for ninja cycles")
            self._reply_json(502, {"error": "gatherer unreachable"})

    def _proxy_ninja_files(self, cycle: str):
        try:
            self._reply_json(200, _gatherer.ninja_files(cycle))
        except Exception:
            logger.exception("gatherer proxy failed for ninja files %s", cycle)
            self._reply_json(502, {"error": "gatherer unreachable"})

    def _proxy_ninja_file(self, cycle: str, rel: str):
        if not rel:
            self._reply_json(400, {"error": "missing path parameter"})
            return
        try:
            data = _gatherer.ninja_file(cycle, rel)
        except Exception:
            logger.exception("gatherer proxy failed for ninja file %s/%s", cycle, rel)
            self._reply_json(502, {"error": "gatherer unreachable"})
            return
        ct = "application/json" if rel.endswith(".json") else \
            "application/x-protobuf" if rel.endswith(".pb") else \
            "application/octet-stream"
        body = gzip.compress(data)
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", ct)
        self.send_header("Content-Encoding", "gzip")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_refresh_all(self):
        """Full refetch + cache rebuild (drops flips deleted on the gatherer)."""
        try:
            self._reply_json(200, _pull_flips())
        except Exception:
            logger.exception("gatherer proxy failed for refresh-all")
            self._reply_json(502, {"error": "gatherer unreachable"})

    def _proxy_put(self, path: str, body: dict):
        global _settings_cache
        try:
            data = _gatherer.put_settings(body)
        except Exception:
            logger.exception("gatherer proxy failed for PUT %s", path)
            self._reply_json(502, {"error": "gatherer unreachable"})
            return
        _settings_cache = data
        self._reply_json(200, data)

    def _proxy_post(self, path: str, flip_id: str):
        try:
            data = _gatherer.refresh(flip_id)
        except Exception:
            logger.exception("gatherer proxy failed for POST %s", path)
            self._reply_json(502, {"error": "gatherer unreachable"})
            return
        with _cache_lock:
            cached = _flip_cache.get(flip_id)
            if cached is not None:
                _refreshing[flip_id] = {
                    "baseline": cached.get("updated_at", 0),
                    "requested_at": time.time(),
                }
        self._reply_json(202, data)

    def _proxy_set_enabled(self, flip_id: str, body: dict):
        enabled = bool(body.get("enabled", True))
        try:
            data = _gatherer.set_enabled(flip_id, enabled)
        except Exception:
            logger.exception("gatherer proxy failed for enabled toggle %s", flip_id)
            self._reply_json(502, {"error": "gatherer unreachable"})
            return
        with _cache_lock:
            if flip_id in _flip_cache:
                _flip_cache[flip_id]["enabled"] = enabled
        self._reply_json(200, data)

    def _proxy_set_source_priced(self, flip_id: str, idx: int, body: dict):
        priced = bool(body.get("priced", True))
        try:
            data = _gatherer.set_source_priced(flip_id, idx, priced)
        except Exception:
            logger.exception("gatherer proxy failed for priced toggle %s", flip_id)
            self._reply_json(502, {"error": "gatherer unreachable"})
            return
        with _cache_lock:
            cached = _flip_cache.get(flip_id)
            if cached is not None:
                flags = list(cached.get("source_priced") or [])
                while len(flags) <= idx:
                    flags.append(True)
                flags[idx] = priced
                cached["source_priced"] = flags
        self._reply_json(200, data)

    def _proxy_delete(self, path: str, flip_id: str):
        try:
            data = _gatherer.delete(flip_id)
        except Exception:
            logger.exception("gatherer proxy failed for DELETE %s", path)
            self._reply_json(502, {"error": "gatherer unreachable"})
            return
        self._reply_json(200, data)

    # ── GET /api/crafting/affixes?item_type=X&cluster=Y ─────────

    def _handle_get_affixes(self, params):
        item_type = params.get("item_type", [None])[0] or "Ring"
        cluster = params.get("cluster", [None])[0] or ""
        prefixes, suffixes = load_affixes(item_type, cluster)
        self._reply_json(200, {
            "item_type": item_type,
            "prefixes": prefixes,
            "suffixes": suffixes,
        })

    def _handle_analysis(self, params):
        flip_id = params.get("flip_id", [None])[0]
        if not flip_id:
            self._reply_json(400, {"error": "missing flip_id"})
            return
        with _cache_lock:
            flip = _flip_cache.get(flip_id)
            flips = list(_flip_cache.values())
        if not flip:
            self._reply_json(404, {"error": "flip not found"})
            return
        from pypoe.analysis import analyze_flip, mirror
        from pypoe.analysis.simple import analyze as simple_analyze

        simple = simple_analyze(mirror.snapshots(flip_id))
        result = analyze_flip(flip["id"], flip.get("name", ""), flips)
        if result is None:
            self._reply_json(200, {"status": "insufficient_data", "simple": simple})
        else:
            self._reply_json(200, {
                "flip_id": flip_id,
                "name": flip.get("name", ""),
                "horizons": {str(k): {
                    "p_sell": v.p_sell, "p_drop": v.p_drop,
                    "p_stagnation": v.p_stagnation, "confidence": v.confidence,
                } for k, v in result.items()},
                "simple": simple,
            })

    def log_message(self, format, *args):
        if args and not str(args[1]).startswith("2"):
            logger.info("HTTP %s", format % args)


def _sync_loop():
    """Background cache refresh — the only place the BFF calls the gatherer."""
    while True:
        try:
            _pull_flips()
        except Exception as e:
            logger.warning("sync: flips pull failed: %s", type(e).__name__)
        with _cache_lock:
            if not _settings_cache:
                try:
                    _pull_settings()
                except Exception as e:
                    logger.warning("sync: settings pull failed: %s", type(e).__name__)
        time.sleep(_SYNC_INTERVAL)


def _pull_flips() -> dict:
    global _last_queue, _last_league, _last_server_time
    data = _gatherer.list_flips(0)
    with _cache_lock:
        _flip_cache.clear()
        _last_league = data.get("league", "")
        for item in data.get("flips", []):
            flip_id = item.get("id")
            if flip_id:
                _blend_source_chaos(item, _last_league)
                _flip_cache[flip_id] = item
        _last_queue = data.get("queue_size", 0)
        _last_server_time = data.get("server_time", time.time())
    logger.info("sync: flips refreshed (%d)", len(_flip_cache))
    return _cache_payload()


def _blend_source_chaos(item: dict, league: str) -> None:
    """Merge chaos source listings into source_avg at the divine rate (app-side)."""
    price = item.get("price")
    if not price:
        return
    chaos_cnt = int(price.get("source_chaos_count") or 0)
    divine_cnt = int(price.get("source_count") or 0)
    if chaos_cnt <= 0:
        return
    try:
        rate = NinjaClient().divine_rate(league or "Standard")
    except Exception:
        logger.exception("divine_rate fetch failed — leaving source divine-only")
        return
    chaos_avg = float(price.get("source_chaos_avg") or 0.0)
    divine_avg = float(price.get("source_avg") or 0.0)
    total = divine_cnt + chaos_cnt
    if total <= 0:
        return
    price["source_avg"] = (divine_avg * divine_cnt + chaos_avg / rate * chaos_cnt) / total
    price["source_count"] = total


def _pull_settings() -> None:
    global _settings_cache
    _settings_cache = _gatherer.get_settings()


def _cache_payload(since: float = 0.0) -> dict:
    with _cache_lock:
        now = time.time()
        for flip_id in list(_refreshing):
            rec = _refreshing[flip_id]
            cached = _flip_cache.get(flip_id)
            done = cached is None or cached.get("updated_at", 0) > rec["baseline"]
            expired = now - rec["requested_at"] > _REFRESH_TTL
            if done or expired:
                del _refreshing[flip_id]
        flips = [f for f in _flip_cache.values() if f.get("updated_at", 0) > since]
        return {
            "flips": flips,
            "server_time": _last_server_time,
            "queue_size": _last_queue,
            "league": _last_league,
            "refreshing": list(_refreshing),
        }


def _history_loop():
    """Incremental sync of the gatherer's price history into the local store."""
    from pypoe.flipper import history
    from pypoe.analysis import mirror as listings_db

    while True:
        try:
            added = history.sync(_gatherer)
            if added:
                logger.info("history: synced %d new rows", added)
        except Exception:
            logger.exception("history sync failed")
        try:
            added = listings_db.sync(_gatherer)
            if added:
                logger.info("listings: synced %d new rows", added)
        except Exception:
            logger.exception("listings sync failed")
        time.sleep(300)


def start_api(port: int = 8765) -> None:
    from pypoe import ninja_weapons
    ninja_weapons.start_watchdog()
    threading.Thread(target=_sync_loop, daemon=True).start()
    threading.Thread(target=_history_loop, daemon=True).start()
    server = HTTPServer(("127.0.0.1", port), APIHandler)
    logger.info("BFF listening on http://127.0.0.1:%d", port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
