"""Tests for TradeClient rate limiting.

Run: uv run python -m flipper.test_throttle
"""

import time
import unittest
import unittest.mock
from unittest.mock import patch, MagicMock
from flipper.client import TradeClient


class FakeResponse:
    status_code = 200
    headers = {}
    _json = {"result": [], "total": 0}

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            from requests.exceptions import HTTPError
            raise HTTPError(f"{self.status_code} error", response=self)


class FakeSession:
    def __init__(self):
        self.cookies = {}
        self.headers = {}
        self.hooks = {}
        self._last_resp = FakeResponse()

    def set_last(self, resp: FakeResponse):
        self._last_resp = resp

    def post(self, url, **kw):
        return self._last_resp

    def get(self, url, **kw):
        return self._last_resp


def mk_headers(rules_str: str, **rule_headers) -> dict:
    h = {"X-Rate-Limit-Rules": rules_str}
    for k, v in rule_headers.items():
        h[f"X-Rate-Limit-{k}"] = v
    return h


class TestStagger(unittest.TestCase):
    def setUp(self):
        self.session = FakeSession()
        self.client = TradeClient("test/0.1.0")
        self.client.session = self.session  # type: ignore

    # ── 1. first_request_min_gap ────────────────────────────────

    def test_first_request_has_min_gap(self):
        """Before any headers, two consecutive calls wait at least 1s between them."""
        with patch("time.sleep") as mock_sleep:
            self.session.set_last(FakeResponse())
            self.client.search({})
            # last was set to now; second call should sleep ~1s
            self.client.search({})
            slept = [args[0][0] for args in mock_sleep.call_args_list if args[0][0] > 0.01]
            self.assertGreaterEqual(len(slept), 1, "should have slept at least once")
            self.assertAlmostEqual(slept[0], 1.0, delta=0.1)

    # ── 2. headers_set_delay ────────────────────────────────────

    def test_headers_set_delay(self):
        """Account: 3:5:60 → _delay = 5/3 + 1 = 2.67."""
        resp = FakeResponse()
        resp.headers = mk_headers("Account", Account="3:5:60")
        self.session.set_last(resp)
        self.client.search({})
        self.assertAlmostEqual(self.client._delay, 5 / 3 + 1, places=2)
        self.assertEqual(self.client._min_gap, 0.0)

    # ── 3. multi_tier_picks_restrictive ─────────────────────────

    def test_multi_tier_picks_restrictive(self):
        """Ip: 8:10:60,15:60:120,60:300:1800 → _delay = 300/60 + 1 = 6.0."""
        resp = FakeResponse()
        resp.headers = mk_headers("Ip", Ip="8:10:60,15:60:120,60:300:1800")
        self.session.set_last(resp)
        self.client.search({})
        self.assertAlmostEqual(self.client._delay, 300 / 60 + 1, places=2)

    # ── 4. multiple_rules_takes_max ─────────────────────────────

    def test_multiple_rules_takes_max(self):
        """Account: 3:5:60  +  Ip: 60:300:1800 → _delay = max(2.67, 6.0) = 6.0."""
        resp = FakeResponse()
        resp.headers = mk_headers("Account,Ip", Account="3:5:60", Ip="60:300:1800")
        self.session.set_last(resp)
        self.client.search({})
        self.assertAlmostEqual(self.client._delay, 6.0, places=2)

    # ── 5. delay_only_increases ─────────────────────────────────

    def test_delay_only_increases(self):
        """First response sets delay=6.0, second with looser policy keeps 6.0."""
        resp1 = FakeResponse()
        resp1.headers = mk_headers("Ip", Ip="60:300:1800")
        resp2 = FakeResponse()
        resp2.headers = mk_headers("Account", Account="10:1:2")

        self.session.set_last(resp1)
        self.client.search({})
        d1 = self.client._delay

        self.session.set_last(resp2)
        self.client.search({})
        self.assertEqual(self.client._delay, d1)

    # ── 6. handle_429_sets_lock ─────────────────────────────────

    def test_handle_429_sets_lock(self):
        """_handle_429 sets _lock and sleeps Retry-After seconds."""
        resp = FakeResponse()
        resp.status_code = 429
        resp.headers = {"Retry-After": "10"}

        with patch("time.sleep") as mock_sleep:
            self.client._handle_429(resp)
            self.assertGreater(self.client._lock, time.time() + 8)
            mock_sleep.assert_has_calls([unittest.mock.call(10)])

    # ── 7. lock_overrides_stagger ───────────────────────────────

    def test_lock_overrides_stagger(self):
        """When locked, stagger delay is ignored and lock sleep happens."""
        with patch("time.sleep") as mock_sleep:
            self.client._lock = time.time() + 9999
            self.client._last = time.time()
            self.client._delay = 0.01
            self.client._enforce()
            slept = [args[0][0] for args in mock_sleep.call_args_list if args[0][0] > 0.01]
            self.assertGreaterEqual(len(slept), 1)
            self.assertGreaterEqual(slept[0], 9000)

    # ── 8. min_gap_removed_after_headers ────────────────────────

    def test_min_gap_removed_after_headers(self):
        """After first response with rate limit headers, _min_gap becomes 0."""
        resp = FakeResponse()
        resp.headers = mk_headers("Account", Account="3:5:60")
        self.session.set_last(resp)
        self.client.search({})
        self.assertEqual(self.client._min_gap, 0.0)

    # ── 9. buffer_always_added ──────────────────────────────────

    def test_buffer_always_added(self):
        """Header 1:1:1 → delay = 1/1 + 1 = 2.0."""
        resp = FakeResponse()
        resp.headers = mk_headers("Account", Account="1:1:1")
        self.session.set_last(resp)
        self.client.search({})
        self.assertAlmostEqual(self.client._delay, 2.0, places=2)

    # ── 10. no_headers_keeps_min_gap ────────────────────────────

    def test_no_headers_keeps_min_gap(self):
        """After a response without rate limit headers, _min_gap stays 1.0."""
        self.client.search({})
        self.assertEqual(self.client._min_gap, 1.0)
        self.assertEqual(self.client._delay, 0.0)

    # ── 11. consecutive_search_and_fetch_stagger ────────────────

    def test_consecutive_search_fetch_stagger(self):
        """search + fetch back to back each obey the delay."""
        resp = FakeResponse()
        resp.headers = mk_headers("Account", Account="3:5:60")
        self.session.set_last(resp)

        with patch("time.sleep") as mock_sleep:
            self.client.search({})
            self.client.fetch(["a"])
            sleeps = [args[0][0] for args in mock_sleep.call_args_list if args[0][0] > 0.01]
            # first sleep is the 1s min_gap before first request
            # second sleep is the _delay stagger after headers arrived
            self.assertGreaterEqual(len(sleeps), 2, "need at least two sleeps")
            self.assertAlmostEqual(sleeps[1], self.client._delay, delta=0.5)

    # ── 12. 429_clears_on_success ───────────────────────────────

    def test_429_clears_on_success(self):
        """After 429 with 10s retry, successful request resets _lock to 0."""
        resp429 = FakeResponse()
        resp429.status_code = 429
        resp429.headers = {"Retry-After": "1"}

        resp200 = FakeResponse()
        resp200.headers = mk_headers("Account", Account="3:5:60")

        self.session.set_last(resp429)
        with patch("time.sleep"):
            try:
                self.client.search({})
            except Exception:
                pass
        lock_after_429 = self.client._lock

        self.session.set_last(resp200)
        with patch("time.sleep"):
            self.client.search({})
        self.assertEqual(self.client._lock, 0.0)


if __name__ == "__main__":
    unittest.main()
