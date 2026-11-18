"""poe.ninja backoff: 429 sets a client-wide cooldown, stale-serves, resets on success."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/

from ninja.ninja import BACKOFF_MAX, BACKOFF_MIN, NinjaClient
import requests


class FakeResp:
    def __init__(self, status, headers=None):
        self.status_code = status
        self.headers = headers or {}

    def json(self):
        return {"lines": [{"id": "divine", "primaryValue": 200.0}]}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:  # type: ignore[no-any-override]  # deliberate duck-typed fake
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, headers=None, timeout=None, **_):
        self.calls.append(url)
        return self.responses.pop(0)


def make(*responses):
    c = NinjaClient()
    c._session = FakeSession(*responses)  # type: ignore[assignment]
    return c


# 1: 429 with no cache -> raises AND sets client-wide cooldown; a second
#    overview() for a DIFFERENT type key must not hit HTTP while cooling down.
c = make(FakeResp(429))
try:
    c.overview("Currency", "Allflame")
    raise AssertionError("expected RuntimeError on 429 with no cache")
except RuntimeError:
    pass
assert c._cooldown_until > time.time(), "429 must set cooldown"
try:
    c.overview("DivinationCard", "Allflame")
    raise AssertionError("expected cooldown to block other type keys too")
except RuntimeError:
    pass
calls = c._session.calls  # type: ignore[attr-defined]
assert len(calls) == 1, f"cooldown must suppress HTTP calls, got {len(calls)}"

# 2: 429 with cached data -> stale-served, no raise, no HTTP call.
c = make(FakeResp(200), FakeResp(429))
first = c.overview("Currency", "Allflame")
c._cache["Allflame:Currency"]["expires"] = 0
c._cache["Allflame:Currency"]["stale_ok"] = 0  # force _fetch path
stale = c.overview("Currency", "Allflame")
assert stale is first, "429 with cache must serve stale data"
assert len(calls) == 1

# 3: backoff grows 5 -> 10 -> capped at 120.
c = make(*(FakeResp(429) for _ in range(12)))
try:
    c.overview("Currency", "Allflame")  # raises, sets 5s
except RuntimeError:
    pass
try:
    c.overview("DivinationCard", "Allflame")
except RuntimeError:
    pass
assert c._backoff == BACKOFF_MIN * 2, f"expected 10, got {c._backoff}"
for _ in range(10):
    c._cooldown_until = 0.0
    try:
        c.overview("Currency", "Allflame")
    except RuntimeError:
        pass
assert c._backoff == BACKOFF_MAX, f"expected cap {BACKOFF_MAX}, got {c._backoff}"

# 4: Retry-After wins over local backoff.
c = make(FakeResp(429, {"Retry-After": "90"}))
try:
    c.overview("Currency", "Allflame")
except RuntimeError:
    pass
assert c._cooldown_until - time.time() > 80, "Retry-After must be honored"

# 5: success resets backoff and cooldown.
c = make(FakeResp(429), FakeResp(200))
try:
    c.overview("Currency", "Allflame")
except RuntimeError:
    pass
c._cooldown_until = time.time() - 1  # expire cooldown
rate = c.divine_rate("Allflame")
assert rate == 200.0
assert c._cooldown_until == 0.0 and c._backoff == BACKOFF_MIN, "success must reset backoff state"

# 6: singleton — same instance across get_client() calls.
from ninja import get_client

assert get_client() is get_client()

print("ninja backoff demo OK")
