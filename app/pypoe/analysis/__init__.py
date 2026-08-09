"""Market analysis — P(sell ≤ T) / P(pricedrop ≤ T) / P(stagnation | T) per flip.

Public entry: analyze_flip(flip_id, name, fast, flips).

Pipeline:
    mirror.snapshots() → engine.classify_events() → engine.exposure()
    → prior.resolve_prior() (pooled across flips in the group)
    → survival.item_posterior() → FIFO queue + downward-pressure corrections
    → EWMA decay → survival.compute_cif() for [1d, 3d, 7d].

The prior pool (all flips' events + group keys) is cached for POOL_TTL seconds;
it only changes when new snapshots sync in.
"""

from __future__ import annotations

import logging
import time

from pypoe.analysis import engine, mirror, prior, survival
from pypoe.analysis.prior import Prior
from pypoe.analysis.survival import HorizonResult

logger = logging.getLogger(__name__)

POOL_TTL = 600  # seconds the prior pool stays fresh

_pool: dict = {"at": 0.0, "events_by_flip": {}, "flip_keys": {}}


def item_type_of(name: str) -> str:
    """Base name (lowercased) from a flip name like 'royal plate 29'.

    Falls back to the raw name for manual flips with no base match.
    """
    base = name.rsplit(" ", 1)[0] if " " in name else name
    return base.lower().strip()


def _build_pool(flips: list[dict]) -> None:
    """Classify every flip's snapshots once and cache events + group keys."""
    now_ms = int(time.time() * 1000)
    events_by_flip: dict[str, list[engine.IntervalEvent]] = {}
    flip_keys: dict[str, tuple[str, ...]] = {}
    for f in flips:
        flip_id = f["id"]
        tier = "high" if f.get("fast") else "low"
        flip_keys[flip_id] = (item_type_of(f["name"]), tier)
        rows = mirror.snapshots(flip_id)
        events = engine.classify_events(flip_id, rows, now_ms)
        if events:
            events_by_flip[flip_id] = events
    _pool["at"] = time.time()
    _pool["events_by_flip"] = events_by_flip
    _pool["flip_keys"] = flip_keys


def _get_pool(flips: list[dict]) -> tuple[dict[str, list], dict[str, tuple[str, ...]]]:
    if time.time() - _pool["at"] > POOL_TTL:
        _build_pool(flips)
    return _pool["events_by_flip"], _pool["flip_keys"]


def analyze_flip(
    flip_id: str,
    name: str,
    fast: bool,
    flips: list[dict] | None = None,
) -> dict[int, HorizonResult] | None:
    """P(sell ≤ T) etc. for one flip. None when there's insufficient snapshot data.

    flips: the full flip list from the gatherer cache (for the prior pool).
    """
    rows = mirror.snapshots(flip_id)
    now_ms = int(time.time() * 1000)
    events = engine.classify_events(flip_id, rows, now_ms)
    if not events:
        return None

    item_type = item_type_of(name)
    tier = "high" if fast else "low"

    if flips is None:
        flips = []
    pool_events, flip_keys = _get_pool(flips)
    pool_events = dict(pool_events)
    pool_events[flip_id] = events  # ensure this flip is included
    flip_keys = dict(flip_keys)
    flip_keys[flip_id] = (item_type, tier)

    prior_sell: Prior
    prior_drop: Prior
    priors = prior.resolve_prior(pool_events, flip_keys, item_type, tier)
    prior_sell, prior_drop = priors["sell"], priors["drop"]

    exp = engine.exposure(events)
    lam_sell = survival.item_posterior(prior_sell, exp.k_sell_total, exp.t_exposure_hours)
    lam_drop = survival.item_posterior(prior_drop, exp.k_drop_total, exp.t_exposure_hours)

    # Structural corrections. Cheapest must come from the latest snapshot only —
    # a stale 7-day-old low price would skew queue position and pressure ratio.
    latest_ms = max(r["fetched_ms"] for r in rows)
    cheapest = min(r["amount"] for r in rows if r["fetched_ms"] == latest_ms)
    queue_pos = survival.my_queue_position(rows, cheapest)
    queue_confident = True  # we can always count the latest snapshot's offers
    lam_sell /= 1 + queue_pos
    lam_drop *= survival.downward_pressure_ratio(rows, cheapest)

    # EWMA decay toward the market prior (stale observation handling).
    last_ms = latest_ms
    lam_sell_final = survival.ewma_lambda(lam_sell, prior_sell.mean_rate, last_ms, now_ms)
    lam_drop_final = survival.ewma_lambda(lam_drop, prior_drop.mean_rate, last_ms, now_ms)

    return survival.compute_cif(
        events,
        lam_sell_final,
        lam_drop_final,
        last_snapshot_ms=last_ms,
        now_ms=now_ms,
        queue_confident=queue_confident,
    )


def _demo():
    """End-to-end on synthetic data: sold+pricedrop events, three horizons."""
    import tempfile
    from pathlib import Path

    import pypoe.analysis.mirror as m

    m._conn = None
    m._DB = Path(tempfile.mkdtemp()) / "listings.db"
    now = int(time.time() * 1000)
    base = now - 7 * 24 * 3600_000
    rows = []
    for i, fetched in enumerate([base + i * 24 * 3600_000 for i in range(8)]):
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
    # seller_a sells out after snapshot 0; seller_b relists below after snapshot 1
    rows = [r for r in rows if not (r["fetched_ms"] > base and r["seller"] == "seller_a")]
    rows = [r for r in rows if not (r["fetched_ms"] == base + 2 * 24 * 3600_000 and r["seller"] == "seller_b")]
    rows.append({"fetched_ms": base + 3 * 24 * 3600_000, "rank": 0, "seller": "seller_b", "amount": 9.0})

    m._connect().executemany(
        "INSERT OR IGNORE INTO listing_snapshots"
        " (flip_id, fetched_ms, rank, seller, amount, currency, indexed_ms, ilvl, rarity)"
        " VALUES (?, ?, ?, ?, ?, 'divine', 0, NULL, NULL)",
        [("f1", r["fetched_ms"], r["rank"], r["seller"], r["amount"]) for r in rows],
    )
    m._connect().commit()

    res = analyze_flip("f1", "royal plate 29", True, flips=[{"id": "f1", "name": "royal plate 29", "fast": True}])
    assert res is not None, "expected a result from 8 snapshots"
    assert set(res) == {1, 3, 7}
    for r in res.values():
        assert 0.0 <= r.p_sell <= 1.0, r
        assert abs(r.p_sell + r.p_drop + r.p_stagnation - 1.0) < 0.001, r
    assert res[7].p_sell >= res[1].p_sell, res
    print("analysis._demo OK:", {k: (v.p_sell, v.p_drop, v.p_stagnation, v.confidence) for k, v in res.items()})


if __name__ == "__main__":
    _demo()
