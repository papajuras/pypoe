"""PoE Trade API client — SyncClient (mutex+backoff) with curl_cffi (Chrome TLS fingerprint)."""

from __future__ import annotations

import json
import logging
import os
import random
import threading
import time
from pathlib import Path
from urllib.parse import quote

import requests
from curl_cffi import requests as curl_requests

from pypoe.config import read_league

logger = logging.getLogger(__name__)

BASE = "https://www.pathofexile.com/api/trade"
LIVE_BASE = "wss://www.pathofexile.com/api/trade/live"
BUFFER = 1

# ── audit log ─────────────────────────────────────────────────────
_audit_logger = logging.getLogger("requests_audit")
_audit_logger.setLevel(logging.INFO)
_audit_logger.propagate = False
_audit_handler = None


def _setup_audit():
    global _audit_handler
    if _audit_handler is not None and _audit_handler.stream is not None:
        return
    if _audit_handler is not None:
        _audit_logger.removeHandler(_audit_handler)
    Path("log").mkdir(exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    fh = logging.FileHandler(f"log/requests-{ts}.log", mode="w")
    fh.setFormatter(logging.Formatter(
        "%(asctime)s.%(msecs)03d  %(message)s", datefmt="%H:%M:%S"))
    _audit_logger.addHandler(fh)
    _audit_handler = fh


def _audit(msg: str, *args):
    if _audit_handler is not None and _audit_handler.stream is None:
        _setup_audit()
    _audit_logger.info(msg, *args)


class TradeClient:
    def __init__(self, user_agent: str, league: str | None = None):
        self.league = league or read_league()
        self._ua = user_agent
        self._sync = SyncClient(user_agent)

    def search(self, query: dict) -> dict:
        url = f"{BASE}/search/{quote(self.league)}"
        return self._sync.post(url, data=query)

    def fetch(self, item_ids: list[str]) -> dict:
        ids = ",".join(item_ids[:10])
        url = f"{BASE}/fetch/{quote(ids)}"
        return self._sync.get(url)

    def live(self, search_id: str, on_result, league: str | None = None):
        import asyncio
        import websockets
        async def _run():
            uri = f"{LIVE_BASE}/{quote(league or self.league)}/{quote(search_id)}"
            async for raw in websockets.connect(uri, user_agent_header=self._ua):
                msg = json.loads(raw)
                if msg.get("type") == "new":
                    on_result(msg)
        asyncio.run(_run())

    @property
    def session(self):
        return self._sync._fallback
    @session.setter
    def session(self, s):
        self._sync._fallback = s

    @property
    def rate_limits(self):
        return list(self._sync._rate_limits.values())

    def solve_challenge(self):
        pass  # no bridge, curl_cffi either works or doesn't

    # proxies for tests
    @property
    def _delay(self): return self._sync._delay
    @_delay.setter
    def _delay(self, v): self._sync._delay = v
    @property
    def _min_gap(self): return self._sync._min_gap
    @_min_gap.setter
    def _min_gap(self, v): self._sync._min_gap = v
    @property
    def _last(self): return self._sync._last
    @_last.setter
    def _last(self, v): self._sync._last = v
    @property
    def _lock(self): return self._sync._lock
    @_lock.setter
    def _lock(self, v): self._sync._lock = v
    @property
    def _jitter_fn(self): return self._sync._jitter_fn
    @_jitter_fn.setter
    def _jitter_fn(self, v): self._sync._jitter_fn = v
    def _enforce(self): self._sync._enforce()
    def _parse_rate_headers(self, h): self._sync._parse_rate_headers(h)


class SyncClient:
    def __init__(self, user_agent: str):
        _setup_audit()
        self._request_lock = threading.Lock()
        self._lock = 0.0  # dead: old 429 retry, kept for test compat
        self._delay = 0.0
        self._min_gap = 1.0
        self._last = time.time()
        self._jitter_fn = lambda: random.uniform(1.0, 2.5)
        self._backoff_until = 0.0
        self._rate_limits: dict[str, dict] = {}
        self._fallback = curl_requests.Session()
        self._fallback.impersonate = "chrome110"
        self._fallback.headers.update({"User-Agent": user_agent, "Accept": "application/json"})
        _audit("INIT  user_agent=%s delay=%s min_gap=%s", user_agent, self._delay, self._min_gap)

    def post(self, url: str, *, data: dict | None = None) -> dict:
        return self._request("POST", url, data=data)

    def get(self, url: str) -> dict:
        return self._request("GET", url)

    def _request(self, method: str, url: str, *, data: dict | None = None) -> dict:
        _audit("PRE   %s %s  delay=%.3f min_gap=%.3f last=%.3f",
               method, url.split(".com")[-1], self._delay, self._min_gap, self._last)
        t0 = time.time()
        with self._request_lock:
            self._enforce()
            if method == "POST":
                resp = self._fallback.post(url, json=data, timeout=30)
            else:
                resp = self._fallback.get(url, timeout=30)
            elapsed = time.time() - t0
            self._parse_rate_headers(resp.headers)
            for k, v in resp.headers.items():
                kl = k.lower()
                if kl.startswith("x-rate-limit-") or kl.startswith("cf-") or kl == "content-type":
                    _audit("RAW   %s: %s", k, v)
            self._last = time.time()
            _audit("RESP  %s %s → %s  %.3fs  delay=%.3f min_gap=%.3f last=%.3f",
                   method, url.split(".com")[-1], resp.status_code,
                   elapsed, self._delay, self._min_gap, self._last)
            if resp.status_code != 200:
                _audit("BODY  req=%s", json.dumps(data) if data else "(none)")
                _audit("BODY  resp=%s", resp.text[:2000])
            if resp.status_code == 429:
                h = {k.lower(): v for k, v in resp.headers.items()}
                _audit("!! 429 ! headers=%s  state_delay=%.3f state_min_gap=%.3f state_last=%.3f",
                       dict(resp.headers), self._delay, self._min_gap, self._last)
                if "x-rate-limit-rules" in h:
                    logger.critical("429 rate limited — fatal, shutting down")
                    os._exit(1)
                logger.warning("Cloudflare 429 — continuing (%s)", url)
            self._last = time.time()
            resp.raise_for_status()
            return resp.json()

    def _enforce(self):
        now = time.time()
        if self._backoff_until > now:
            sleep = self._backoff_until - now
            _audit("BACK  sleep=%.1f", sleep)
            logger.warning("Usage >70%% — backoff %.0fs", sleep)
            time.sleep(sleep)
            self._backoff_until = 0
            self._rate_limits["_sleep"] = {"label": f"sleep: {sleep:.2f}s", "tooltip": f"Backoff: {sleep:.1f}s remaining", "pct": 0}
        if self._lock > now:  # dead: old 429 retry, kept for test compat
            sleep = self._lock - now + self._jitter_fn()
            _audit("LOCK  sleep=%.3f", sleep)
            logger.info("Locked, sleeping %.1fs", sleep)
            time.sleep(sleep)
            self._lock = 0
            self._rate_limits["_sleep"] = {"label": f"sleep: {sleep:.2f}s", "tooltip": f"Lock: slept {sleep:.1f}s", "pct": 0}
        jitter = self._jitter_fn()
        gap = max(self._delay, self._min_gap) + jitter
        since_last = now - self._last
        if since_last < gap:
            sleep = gap - since_last
            _audit("ENF   delay=%.3f min_gap=%.3f jitter=%.3f gap=%.3f since_last=%.3f sleep=%.3f",
                   self._delay, self._min_gap, jitter, gap, since_last, sleep)
            logger.info("Staggering, sleeping %.2fs", sleep)
            time.sleep(sleep)
            self._rate_limits["_sleep"] = {"label": f"sleep: {sleep:.2f}s", "tooltip": f"Stagger: slept {sleep:.2f}s", "pct": 0}

    def _parse_rate_headers(self, headers):
        h = {k.lower(): v for k, v in headers.items()}
        rules_str = h.get("x-rate-limit-rules", "")
        if not rules_str:
            return
        new_limits: list[dict] = []
        info = []
        delays: list[float] = []
        max_usage = 0.0
        for rule_name in rules_str.split(","):
            rule_name = rule_name.strip()
            limits = h.get(f"x-rate-limit-{rule_name.lower()}", "")
            if not limits:
                continue
            states = h.get(f"x-rate-limit-{rule_name.lower()}-state", "")
            limit_tiers = limits.split(",")
            state_tiers = states.split(",") if states else []
            for i, tier in enumerate(limit_tiers):
                parts = tier.strip().split(":")
                if len(parts) < 3:
                    continue
                a, b, c = int(parts[0]), int(parts[1]), int(parts[2])
                if a > 0:
                    resp_rate = b / a
                    used = int(state_tiers[i].strip().split(":")[0]) if i < len(state_tiers) and state_tiers[i].strip() else 0
                    if used > 0:
                        usage = used / a
                        tier_gap = resp_rate * (0.5 + usage * 1.5)
                    else:
                        tier_gap = resp_rate * 0.3
                    delays.append(tier_gap)
                    info.append(f"{rule_name} {a}:{b}:{c} → {tier_gap:.3f}s/req pen={c}s (used={used})")
                    pct = used / a * 100 if a > 0 else 0
                    label = f"{rule_name}/{b}s: {used}/{a} ({pct:.0f}%)" if used else f"{rule_name}/{b}s: ?/{a}"
                    tooltip = f"{rule_name}: {a} per {b}s — {c}s penalty"
                    new_limits.append({"label": label, "tooltip": tooltip, "pct": pct, "rule": rule_name})
                    if i < len(state_tiers) and c >= 120:
                        sp = state_tiers[i].strip().split(":")
                        if sp:
                            used_val = int(sp[0])
                            usage = used_val / a if a > 0 else 0
                            if usage > max_usage:
                                max_usage = usage
        if delays:
            old = self._delay
            self._delay = max(delays) + BUFFER
            self._min_gap = 0.0
            _audit("PARSE %s  delay %.3f→%.3f  min_gap→0  max_usage=%.0f%%",
                   "; ".join(info), old, self._delay, max_usage * 100)
            if max_usage >= 0.70 and self._backoff_until <= time.time():
                factor = min((max_usage - 0.70) / 0.30, 1.0)
                backoff = factor * 300
                self._backoff_until = time.time() + backoff
                _audit("BACK  set %.0fs backoff at %.0f%% usage", backoff, max_usage * 100)
                logger.warning("Rate usage %.0f%% — pausing %.0fs", max_usage * 100, backoff)
        for nl in new_limits:
            self._rate_limits[nl["tooltip"]] = nl
