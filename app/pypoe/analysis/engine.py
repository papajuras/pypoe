"""Event classification over target-side listing snapshots.

For each interval between consecutive snapshots of a flip, classify what
happened to offers that were visible at the flip's cheapest price and then
disappeared: SOLD, PRICEDROP (same seller relisted within 48h at or below
that price), or CENSORED (the top-10 visibility cutoff dropped, so the offer
may still be on the market but out of view).

Per explicit decision: an offer that disappeared within the last 48h of the
window is treated as SOLD (the market moves slowly; it is unlikely to return).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

RECENT_SELL_MS = 48 * 3600_000   # last 48h of the window → treat disappearance as SOLD
REAPPEAR_WINDOW_MS = 48 * 3600_000
MIN_INTERVALS = 20


@dataclass
class IntervalEvent:
    delta_t_hours: float
    k_sell: int = 0
    k_drop: int = 0
    censored: bool = False


@dataclass
class Exposure:
    k_sell_total: int = 0
    k_drop_total: int = 0
    t_exposure_hours: float = 0.0


def _snapshot_moments(rows: list[dict]) -> list[tuple[int, float | None, set[tuple[str, float]]]]:
    """Group rows by fetched_ms → (fetched_ms, threshold_price, offers).

    threshold is the price at rank 9 (position 10, 0-indexed); None when the
    snapshot has fewer than 10 listings (no visibility cutoff to speak of).
    offers is the set of (seller, amount) pairs visible in that snapshot.
    """
    moments: list[tuple[int, float | None, set[tuple[str, float]]]] = []
    for fetched_ms, group in _groupby(rows, key=lambda r: r["fetched_ms"]):
        offers = {(r["seller"], r["amount"]) for r in group}
        by_rank = {r["rank"]: r["amount"] for r in group}
        threshold = by_rank.get(9) if len(group) >= 10 else None
        moments.append((fetched_ms, threshold, offers))
    return moments


def _groupby(rows, key):
    """Stable group-by on already-sorted rows, preserving order."""
    result = []
    cur_key, cur = None, []
    for r in rows:
        k = key(r)
        if k != cur_key:
            if cur:
                result.append((cur_key, cur))
            cur_key, cur = k, []
        cur.append(r)
    if cur:
        result.append((cur_key, cur))
    return result


def _seller_reappears(
    moments: list[tuple[int, float | None, set[tuple[str, float]]]],
    from_idx: int,
    seller: str,
    price_cap: float,
) -> bool:
    """Did `seller` relist at <= price_cap within 48h of moment[from_idx]?"""
    window_end = moments[from_idx][0] + REAPPEAR_WINDOW_MS
    for t, _thresh, offers in moments[from_idx + 1:]:
        if t > window_end:
            break
        if any(s == seller and a <= price_cap for s, a in offers):
            return True
    return False


def classify_events(
    flip_id: str,
    rows: list[dict],
    now_ms: int,
) -> list[IntervalEvent]:
    """Classify one flip's snapshot history into per-interval events.

    rows: all snapshots for the flip, sorted by fetched_ms (see mirror.snapshots).
    Returns [] when fewer than 2 snapshot moments exist.
    """
    moments = _snapshot_moments(rows)
    if len(moments) < 2:
        return []

    events: list[IntervalEvent] = []
    for i in range(1, len(moments)):
        t_prev, thresh_prev, offers_prev = moments[i - 1]
        t_i, thresh_i, offers_i = moments[i]
        delta_h = (t_i - t_prev) / 3600_000.0
        if delta_h <= 0:
            continue

        if not offers_prev:
            events.append(IntervalEvent(delta_t_hours=delta_h))
            continue

        cheapest = min(a for _s, a in offers_prev)
        cutoff_dropped = (
            thresh_prev is not None and thresh_i is not None and thresh_i < thresh_prev
        )
        k_sell = k_drop = 0
        censored = False
        for offer in offers_prev:
            seller, amount = offer
            if amount > cheapest or offer in offers_i:
                continue
            if cutoff_dropped:
                censored = True
                continue
            if t_i >= now_ms - RECENT_SELL_MS:
                k_sell += 1
                continue
            if _seller_reappears(moments, i, seller, cheapest):
                k_drop += 1
            else:
                k_sell += 1
        events.append(
            IntervalEvent(delta_t_hours=delta_h, k_sell=k_sell, k_drop=k_drop, censored=censored)
        )
    return events


def exposure(events: list[IntervalEvent]) -> Exposure:
    """Per-flip own totals — feeds the item-level posterior."""
    return Exposure(
        k_sell_total=sum(e.k_sell for e in events),
        k_drop_total=sum(e.k_drop for e in events),
        t_exposure_hours=sum(e.delta_t_hours for e in events),
    )


def collect_rates(
    events_by_flip: dict[str, list[IntervalEvent]],
    group_key: tuple[str, ...],
    flip_keys: dict[str, tuple[str, ...]],
) -> tuple[list[float], list[float], int]:
    """Per-interval event rates for a group key, zero-event intervals included.

    Returns (rates_sell, rates_drop, interval_count). Every interval with
    Δt > 0 contributes k/Δt (0.0 when nothing happened), so the pooled mean is
    the true events-per-hour rate. Skipping zero intervals would inflate the
    rate when events are rare.
    """
    rates_sell: list[float] = []
    rates_drop: list[float] = []
    interval_count = 0
    for flip_id, events in events_by_flip.items():
        if flip_keys.get(flip_id) != group_key:
            continue
        for ev in events:
            interval_count += 1
            if ev.delta_t_hours > 0:
                rates_sell.append(ev.k_sell / ev.delta_t_hours)
                rates_drop.append(ev.k_drop / ev.delta_t_hours)
    return rates_sell, rates_drop, interval_count


def _demo():
    """Synthetic: 4 snapshots, one SOLD, one PRICEDROP, one censored."""
    base = 1_800_000_000_000  # fixed epoch to keep the 48h rules deterministic
    rows = []
    for i, fetched in enumerate([base, base + 2 * 3600_000, base + 4 * 3600_000, base + 6 * 3600_000]):
        rows += [
            {"fetched_ms": fetched, "rank": r, "seller": s, "amount": a}
            for r, s, a in [
                (0, "seller_a", 10.0), (1, "seller_b", 10.0),
                (2, "seller_c", 11.0), (3, "seller_d", 12.0),
                (4, "seller_e", 13.0), (5, "seller_f", 14.0),
                (6, "seller_g", 15.0), (7, "seller_h", 16.0),
                (8, "seller_i", 17.0), (9, "seller_j", 18.0),
            ]
        ]
    # seller_a disappears after t0 (SOLD — never reappears)
    rows = [r for r in rows if not (r["fetched_ms"] > base and r["seller"] == "seller_a")]
    # seller_b disappears at t2 but reappears at t3 below cheapest → PRICEDROP
    rows = [r for r in rows if not (r["fetched_ms"] == base + 4 * 3600_000 and r["seller"] == "seller_b")]
    rows.append({"fetched_ms": base + 6 * 3600_000, "rank": 0, "seller": "seller_b", "amount": 9.0})
    # all fetched_ms < now-48h so no recent-SOLD shortcut fires
    now = base + 6 * 3600_000 + 49 * 3600_000
    events = classify_events("demo", sorted(rows, key=lambda r: r["fetched_ms"]), now)
    assert len(events) == 3, events
    assert events[0].k_sell == 1 and events[0].k_drop == 0, events[0]
    assert events[1].k_drop == 1 and events[1].k_sell == 0, events[1]
    assert events[2].k_sell == 0 and events[2].k_drop == 0, events[2]
    exp = exposure(events)
    assert exp.k_sell_total == 1 and exp.k_drop_total == 1, exp
    assert abs(exp.t_exposure_hours - 6.0) < 1e-9, exp
    print("engine._demo OK:", events)


if __name__ == "__main__":
    _demo()
