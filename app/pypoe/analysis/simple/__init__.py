"""Common-sense target-side analysis: two trends, four categories.

Only the flip's target-side listing snapshots are observed. For each snapshot
moment we take the minimum listing price and the number of listings, then fit
a least-squares line over time (statistics.linear_regression, works with any
number of points >= 2). The sign of each slope gives a binary trend, and the
two trends combine into one of four named categories with a score.

Category = min-price trend x stock trend:

    min up / stock down -> drying up   (supply shrinks, price climbs)  9
    min up / stock up   -> bidding up  (demand pulls in new supply)    7
    min down / stock down -> clearing  (price drops, stock drains)     5
    min down / stock up -> flooding    (undercut war, stock piles up)  3
"""

from __future__ import annotations

import statistics

MIN_SNAPSHOTS = 2
TURNOVER_REAPPEAR_MS = 48 * 3600_000   # a relist within 48h is an undercut, not a sale

SCORES = {
    "drying_up": 9,
    "bidding_up": 7,
    "clearing": 5,
    "flooding": 3,
}


def turnover_per_day(rows: list[dict]) -> float | None:
    """Cheapest-offer sell rate: offers gone from the then-cheapest per day.

    Counts offers that were at a moment's cheapest price and are missing from
    the next moment, excluding same-seller relists at <= that price within
    48h. None when fewer than 2 snapshot moments or a zero/negative window.
    """
    by_ms: dict[int, set[tuple[str, float]]] = {}
    for r in rows:
        by_ms.setdefault(r["fetched_ms"], set()).add((r["seller"], r["amount"]))
    moments = sorted(by_ms.items())
    if len(moments) < MIN_SNAPSHOTS:
        return None
    window_days = (moments[-1][0] - moments[0][0]) / 86400_000
    if window_days <= 0:
        return None
    sold = 0
    for i in range(len(moments) - 1):
        ms_prev, offers_prev = moments[i]
        ms_next, offers_next = moments[i + 1]
        cheapest = min(a for _s, a in offers_prev)
        for seller, amount in offers_prev:
            if amount != cheapest or (seller, amount) in offers_next:
                continue
            relist_deadline = ms_next + TURNOVER_REAPPEAR_MS
            relisted = any(
                s == seller and a <= amount
                for ms, offers in moments[i + 1:]
                if ms <= relist_deadline
                for s, a in offers
            )
            if not relisted:
                sold += 1
    return round(sold / window_days, 2)


def _snapshot_series(rows: list[dict]) -> tuple[list[float], list[float], list[float]]:
    """(times_ms, min_prices, stock_counts) one entry per snapshot moment."""
    by_ms: dict[int, list[float]] = {}
    for r in rows:
        by_ms.setdefault(r["fetched_ms"], []).append(r["amount"])
    times: list[float] = []
    prices: list[float] = []
    stocks: list[float] = []
    for ms in sorted(by_ms):
        amounts = by_ms[ms]
        times.append(float(ms))
        prices.append(min(amounts))
        stocks.append(float(len(amounts)))
    return times, prices, stocks


def _trend(xs: list[float], ys: list[float]) -> str:
    if len(set(xs)) < 2 or len(set(ys)) < 2:
        return "down"
    slope = statistics.linear_regression(xs, ys).slope
    return "up" if slope >= 0 else "down"


def analyze(rows: list[dict]) -> dict:
    """Two trends -> one category. None-worthy data -> insufficient_data."""
    if not rows or len({r["fetched_ms"] for r in rows}) < MIN_SNAPSHOTS:
        return {"status": "insufficient_data"}
    times, prices, stocks = _snapshot_series(rows)
    min_trend = _trend(times, prices)
    stock_trend = _trend(times, stocks)
    if min_trend == "up":
        category = "drying_up" if stock_trend == "down" else "bidding_up"
    else:
        category = "clearing" if stock_trend == "down" else "flooding"
    return {
        "status": "ok",
        "score": SCORES[category],
        "category": category,
        "min_trend": min_trend,
        "stock_trend": stock_trend,
        "turnover": turnover_per_day(rows),
    }


def _demo():
    """Trend directions and the four category/score combinations."""
    base = 1_800_000_000_000
    def snap(ms, prices):
        return [{"fetched_ms": ms, "rank": i, "seller": f"s{i}", "amount": a}
                for i, a in enumerate(prices)]

    # flat series (no variance) must not crash -> defaults
    r = analyze(snap(base, [10.0, 11.0]))
    assert r["status"] == "insufficient_data", r  # only one moment

    up = snap(base, [10.0])
    down = snap(base + 3600_000, [9.0])
    assert analyze(up + down)["min_trend"] == "down"

    def verdict(min_trend, stock_trend):
        rows: list[dict] = []
        for i in range(4):
            ms = base + i * 3600_000
            price = 10.0 + i * (1.0 if min_trend == "up" else -1.0)
            count = 5 + i * (1 if stock_trend == "up" else -1)
            rows += snap(ms, [price] * max(1, count))
        return analyze(rows)

    assert verdict("up", "down")["score"] == 9 and verdict("up", "down")["category"] == "drying_up"
    assert verdict("up", "up")["score"] == 7
    assert verdict("down", "down")["score"] == 5
    assert verdict("down", "up")["score"] == 3

    # ── turnover: cheapest-offer sell rate ──
    d = 86400_000
    assert turnover_per_day(snap(base, [10.0])) is None  # 1 moment
    # zero movement: cheap offer persists
    assert turnover_per_day(snap(base, [10.0, 11.0]) + snap(base + d, [10.0, 11.0])) == 0.0
    # one sale over 1 day
    assert turnover_per_day(snap(base, [10.0, 11.0]) + snap(base + d, [11.0])) == 1.0
    # relist within 48h = undercut, not a sale
    rows = snap(base, [10.0, 11.0]) + snap(base + d, [11.0]) + snap(base + 2 * d, [9.0, 11.0])
    assert turnover_per_day(rows) == 0.0
    # non-cheapest vanish ignored
    assert turnover_per_day(snap(base, [10.0, 11.0]) + snap(base + d, [10.0])) == 0.0
    # 2 cheap offers vanish over 48h -> 1.0/day
    assert turnover_per_day(snap(base, [10.0, 10.0, 11.0]) + snap(base + 2 * d, [11.0])) == 1.0
    # cheapest drops mid-window: old 10-offer no longer "at cheapest" -> not counted
    drop = snap(base, [10.0, 11.0]) + snap(base + d, [9.0, 10.0, 11.0]) + snap(base + 2 * d, [9.0, 11.0])
    assert turnover_per_day(drop) == 0.0

    print("simple._demo OK:", verdict("down", "up"))


if __name__ == "__main__":
    _demo()
