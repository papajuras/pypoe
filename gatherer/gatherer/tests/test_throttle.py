"""Tests for TradeClient rate limiting.

Run: uv run python -m gatherer.tests.test_throttle
"""

import time
import unittest
import unittest.mock
from unittest.mock import patch, MagicMock
from gatherer.client import TradeClient


class FakeResponse:
    status_code = 200
    headers = {}
    _json = {"result": [], "total": 0}
    text = ""

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
        if k.endswith("State"):
            k = k[:-5] + "-State"
        h[f"X-Rate-Limit-{k}"] = v
    return h


class ControlledClock:
    """Fake time source that advances on sleep, no wall-clock waiting."""

    def __init__(self, start: float = 1000.0):
        self._now = start

    def time(self) -> float:
        return self._now

    def sleep(self, s: float) -> None:
        assert s >= 0
        self._now += s


class TestStagger(unittest.TestCase):
    def setUp(self):
        self.session = FakeSession()
        self.client = TradeClient("test/0.1.0")
        self.client.session = self.session  # type: ignore
        self.client._jitter_fn = lambda: 0.0

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
        """Account: 3:5:60, no state → _delay = 5/3 × 0.2 + 0.5 = 0.83."""
        resp = FakeResponse()
        resp.headers = mk_headers("Account", Account="3:5:60")
        self.session.set_last(resp)
        self.client.search({})
        self.assertAlmostEqual(self.client._delay, 5 / 3 * 0.2 + 0.5, places=2)
        self.assertEqual(self.client._min_gap, 0.0)

    # ── 3. multi_tier_picks_restrictive ─────────────────────────

    def test_multi_tier_picks_restrictive(self):
        """Ip: 8:10:60,15:60:120,60:300:1800, no state → _delay = 300/60 × 0.2 + 0.5 = 1.5."""
        resp = FakeResponse()
        resp.headers = mk_headers("Ip", Ip="8:10:60,15:60:120,60:300:1800")
        self.session.set_last(resp)
        self.client.search({})
        self.assertAlmostEqual(self.client._delay, 300 / 60 * 0.2 + 0.5, places=2)

    # ── 4. multiple_rules_takes_max ─────────────────────────────

    def test_multiple_rules_takes_max(self):
        """Account: 3:5:60 + Ip: 60:300:1800, no state → _delay = max(1.667×0.2, 5.0×0.2) + 0.5 = 1.5."""
        resp = FakeResponse()
        resp.headers = mk_headers("Account,Ip", Account="3:5:60", Ip="60:300:1800")
        self.session.set_last(resp)
        self.client.search({})
        self.assertAlmostEqual(self.client._delay, max(5 / 3 * 0.2, 300 / 60 * 0.2) + 0.5, places=2)

    # ── 5. delay_only_increases ─────────────────────────────────

    def test_delay_updates_regardless_of_previous(self):
        """Delay is always recomputed from current headers, not the max of old and new."""
        resp1 = FakeResponse()
        resp1.headers = mk_headers("Ip", Ip="60:300:1800", IpState="30:300:0")  # 50% usage → 5.5
        resp2 = FakeResponse()
        resp2.headers = mk_headers("Ip", Ip="60:300:1800", IpState="3:300:0")   # 5% usage → 2.58

        self.session.set_last(resp1)
        self.client.search({})
        d1 = self.client._delay

        self.session.set_last(resp2)
        self.client.search({})
        d2 = self.client._delay

        self.assertGreater(d1, d2, "delay should decrease when usage drops")

    # ── 6. lock_overrides_stagger ───────────────────────────────

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
        """Header 1:1:1, no state → delay = 1/1 × 0.2 + 0.5 = 0.7."""
        resp = FakeResponse()
        resp.headers = mk_headers("Account", Account="1:1:1")
        self.session.set_last(resp)
        self.client.search({})
        self.assertAlmostEqual(self.client._delay, 0.7, places=2)

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

    # ── 12. 429_poe_exits ───────────────────────────────────────

    def test_429_poe_exits(self):
        """PoE API 429 (X-Rate-Limit-Rules present) → os._exit(1)."""
        resp = FakeResponse()
        resp.status_code = 429
        resp.headers = mk_headers("Account", Account="1:5:60")

        self.client._last = time.time() - 10
        self.session.set_last(resp)
        with patch("gatherer.client.os._exit", side_effect=SystemExit(1)) as mock_exit:
            with self.assertRaises(SystemExit):
                self.client.search({})
            mock_exit.assert_called_once_with(1)
        self.assertEqual(self.client._lock, 0.0)

    # ── 13. 429_cloudflare_continues ────────────────────────────

    def test_429_cloudflare_continues(self):
        """Cloudflare 429 (no rate-limit headers) → HTTPError, no exit, no lock."""
        resp = FakeResponse()
        resp.status_code = 429
        resp.headers = {"Server": "cloudflare"}

        self.client._last = time.time() - 10
        self.session.set_last(resp)
        with patch("gatherer.client.os._exit") as mock_exit:
            t0 = time.monotonic()
            with self.assertRaises(Exception):
                self.client.search({})
            elapsed = time.monotonic() - t0
            mock_exit.assert_not_called()

        self.assertLess(elapsed, 0.5)
        self.assertEqual(self.client._lock, 0.0)


    # ── 13. delay_adapts_across_sequence ──────────────────────────

    def test_delay_adapts_across_sequence(self):
        """6 requests: gaps [3.0, 3.0, 2.83, 2.83, 3.5] with dynamic delay."""
        clock = ControlledClock()

        with (patch('gatherer.client.time.time', clock.time),
              patch('gatherer.client.time.sleep', clock.sleep)):

            self.client._jitter_fn = lambda: 2.0

            # Req 1: prime, no headers. _last far back so no sleep.
            self.session.set_last(FakeResponse())
            self.client._last = clock.time() - 10
            self.client.search({})
            times = [clock.time()]

            # Req 2: no headers → min_gap + jitter = 3.0
            self.session.set_last(FakeResponse())
            self.client.search({})
            times.append(clock.time())

            # Req 3: response has Account=3:5:60 (no state) → _delay=0.83 after response, but _enforce still uses min_gap
            resp = FakeResponse()
            resp.headers = mk_headers("Account", Account="3:5:60")
            self.session.set_last(resp)
            self.client.search({})
            times.append(clock.time())

            # Req 4: _delay=0.83 takes effect → gap = 0.83 + 2.0 = 2.83
            resp = FakeResponse()
            resp.headers = mk_headers("Account", Account="3:5:60")
            self.session.set_last(resp)
            self.client.search({})
            times.append(clock.time())

            # Req 5: _delay=0.83 → gap = 2.83
            #        response sets Ip=60:300:1800 (no state) → _delay=1.5
            resp = FakeResponse()
            resp.headers = mk_headers("Ip", Ip="60:300:1800")
            self.session.set_last(resp)
            self.client.search({})
            times.append(clock.time())

            # Req 6: _delay=1.5 takes effect → gap = 1.5 + 2.0 = 3.5
            resp = FakeResponse()
            resp.headers = mk_headers("Ip", Ip="60:300:1800")
            self.session.set_last(resp)
            self.client.search({})
            times.append(clock.time())

        gaps = [round(times[i] - times[i - 1], 2) for i in range(1, len(times))]
        expected = [3.0, 3.0, 2.83, 2.83, 3.5]

        print(f"\n  Sequence gaps: {gaps}")

        for i, (actual, exp) in enumerate(zip(gaps, expected)):
            self.assertAlmostEqual(actual, exp, delta=0.02,
                msg=f"gap[{i}]: expected {exp}, got {actual}")

        self.assertAlmostEqual(self.client._delay, 300 / 60 * 0.2 + 0.5, places=1)
        self.assertEqual(self.client._min_gap, 0.0)


    # ── dynamic delay formula tests ──────────────────────────────

    def test_empty_state_low_delay(self):
        """No state data → 0.2x multiplier → _delay = 5.0 × 0.2 + 0.5 = 1.5."""
        resp = FakeResponse()
        resp.headers = mk_headers("Ip", Ip="60:300:1800")
        self.session.set_last(resp)
        self.client.search({})
        self.assertAlmostEqual(self.client._delay, 300 / 60 * 0.2 + 0.5, places=2)

    def test_low_usage_ten_percent(self):
        """10% usage → _delay = 5.0 × (0.35 + 0.1 × 1.3) + 0.5 = 2.9."""
        resp = FakeResponse()
        resp.headers = mk_headers("Ip", Ip="60:300:1800", IpState="6:300:0")
        self.session.set_last(resp)
        self.client.search({})
        expected = 300 / 60 * (0.35 + 6 / 60 * 1.3) + 0.5
        self.assertAlmostEqual(self.client._delay, expected, places=2)

    def test_high_usage_ninety_percent(self):
        """90% usage → _delay = 5.0 × (0.35 + 0.9 × 1.3) + 0.5 = 8.1."""
        resp = FakeResponse()
        resp.headers = mk_headers("Ip", Ip="60:300:1800", IpState="54:300:0")
        self.session.set_last(resp)
        self.client.search({})
        expected = 300 / 60 * (0.35 + 54 / 60 * 1.3) + 0.5
        self.assertAlmostEqual(self.client._delay, expected, places=2)

    def test_multi_tier_state_takes_max(self):
        """Two tiers with state, max determines delay."""
        resp = FakeResponse()
        # Account 3:5:60, state 2:5:0 (67% usage)
        # Ip 15:60:120, state 3:60:0 (20% usage)
        resp.headers = mk_headers("Account,Ip",
                                  Account="3:5:60", AccountState="2:5:0",
                                  Ip="15:60:120", IpState="3:60:0")
        self.session.set_last(resp)
        self.client.search({})
        # Account: 5/3 × (0.35 + 0.667 × 1.3) = 1.667 × 1.217 = 2.03
        # Ip: 60/15 × (0.35 + 0.2 × 1.3) = 4.0 × 0.61 = 2.44
        # max = 2.44, + 0.5 = 2.94
        expected = 2.94
        self.assertAlmostEqual(self.client._delay, expected, places=1)


    # ── 14. DNS failure rebuilds session ────────────────────────

    def test_dns_error_rebuilds_session_and_retries(self):
        """A transient DNS failure rebuilds the curl session and the request still succeeds."""
        from curl_cffi.requests.exceptions import DNSError

        class FlakySession(FakeSession):
            def __init__(self):
                super().__init__()
                self.n_calls = 0

            def post(self, url, **kw):
                self.n_calls += 1
                if self.n_calls == 1:
                    raise DNSError("Could not resolve host")
                return self._last_resp

        self.client._last = time.time() - 10
        self.client.session = FlakySession()
        with patch.object(self.client._sync, "_rebuild_session") as rebuild:
            self.client.search({})   # no exception
            rebuild.assert_called_once()
        self.assertEqual(self.client.session.n_calls, 2)  # failed once, retried on same session


if __name__ == "__main__":
    unittest.main()
