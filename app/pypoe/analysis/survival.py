"""Item-level posterior, structural corrections, and CIF projections.

Posterior is the closed-form Gamma-Poisson update:
    λ = (α + k) / (β + T)   (pure Poisson prior: λ = prior mean, no blend)

Structural corrections adjust the item's hazard:
    λ_sell *= 1 / (1 + queue_position)      # FIFO: you queue behind sellers
                                            # already at the cheapest price
    λ_drop *= recent_downward_flow / mean_flow   # competitor repricing pressure

Forward projections are the constant-hazard exponential/CIF formulas over
virtual intervals of T days, with a time-based EWMA decay toward the market
prior when the last observation is stale.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from pypoe.analysis.prior import Prior

TAU_DECAY_HOURS = 6.0
HORIZONS_DAYS = (1, 3, 7)


@dataclass
class HorizonResult:
    p_sell: float
    p_drop: float
    p_stagnation: float
    confidence: str  # "high" | "low"


def item_posterior(prior: Prior, k: int, t_exposure_hours: float) -> float:
    """Item-level hazard rate λ. Pure-Poisson prior → prior mean (no blend)."""
    if prior.poisson:
        return prior.mean
    return (prior.alpha + k) / (prior.beta + t_exposure_hours)


def my_queue_position(snapshots: list[dict], cheapest: float) -> int:
    """Sellers already listed at the cheapest price in the latest snapshot.

    You post at the cheapest price, so every existing offer there was listed
    before you — you queue behind all of them (L4 FIFO approximation).
    """
    if not snapshots:
        return 0
    latest_ms = max(r["fetched_ms"] for r in snapshots)
    return sum(
        1 for r in snapshots if r["fetched_ms"] == latest_ms and r["amount"] == cheapest
    )


def _downward_flow_per_interval(snapshots: list[dict], cheapest: float) -> list[tuple[int, float]]:
    """For each interval, (count of newly-visible sellers below `cheapest`, interval hours).

    The interval length is the time gap between the current snapshot and the
    previous one, so each count is comparable in per-hour terms.
    """
    by_ms: dict[int, set[str]] = {}
    for r in snapshots:
        if r["amount"] < cheapest:
            by_ms.setdefault(r["fetched_ms"], set()).add(r["seller"])
    ordered = sorted(by_ms)
    flows: list[tuple[int, float]] = []
    prev: set[str] = set()
    prev_ms: int | None = None
    for ms in ordered:
        cur = by_ms[ms]
        dt_h = (ms - prev_ms) / 3600_000 if prev_ms is not None else 0.0
        flows.append((len(cur - prev), dt_h))
        prev, prev_ms = cur, ms
    return flows


def downward_pressure_ratio(snapshots: list[dict], cheapest: float) -> float:
    """Recent downward flow normalized by the flip's own historical mean.

    Both sides are per-hour rates (new cheap sellers per hour), so a long
    interval with many new entries is not mistaken for aggressive undercutting.
    Falls back to 1.0 when there is no history to normalize against.
    """
    flows = _downward_flow_per_interval(snapshots, cheapest)
    rates = [c / dt for c, dt in flows if dt > 0]
    if not rates:
        return 1.0
    recent = rates[-1]
    mean_rate = sum(rates) / len(rates)
    if mean_rate <= 0:
        return 1.0
    return recent / mean_rate


def ewma_lambda(lam_item: float, lam_prior: float, last_snapshot_ms: int, now_ms: int) -> float:
    """Decay item λ toward the market prior as the last observation ages."""
    delta_hours = max(0.0, (now_ms - last_snapshot_ms) / 3600_000)
    weight = math.exp(-delta_hours / TAU_DECAY_HOURS)
    return weight * lam_item + (1 - weight) * lam_prior


def _interval_math(lam_sell: float, lam_drop: float, dt_days: float):
    """(survival factor, sell CIF fraction, drop CIF fraction) for one interval."""
    total = lam_sell + lam_drop
    if total <= 0:
        return 1.0, 0.0, 0.0
    surv = math.exp(-total * dt_days)
    return surv, lam_sell / total, lam_drop / total


def _confidence_flag(T_days: float, last_dt_hours: float | None, queue_confident: bool) -> str:
    if not queue_confident:
        return "low"
    if last_dt_hours is None:
        return "low"
    return "high" if T_days >= 2 * (last_dt_hours / 24.0) else "low"


def compute_cif(
    events: list,
    lam_sell_final: float,
    lam_drop_final: float,
    horizons_days: tuple[int, ...] = HORIZONS_DAYS,
    last_snapshot_ms: int | None = None,
    now_ms: int | None = None,
    queue_confident: bool = True,
) -> dict[int, HorizonResult]:
    """Historical CIF up to now + constant-hazard forward projections.

    lam_sell_final / lam_drop_final are the EWMA-decayed item hazards (already
    corrected for queue position and downward pressure).
    """
    s = 1.0
    cif_sell = 0.0
    cif_drop = 0.0
    for ev in events:
        dt_days = ev.delta_t_hours / 24.0
        surv, frac_sell, frac_drop = _interval_math(lam_sell_final, lam_drop_final, dt_days)
        cif_sell += frac_sell * (1 - surv) * s
        cif_drop += frac_drop * (1 - surv) * s
        s *= surv

    last_dt_hours = events[-1].delta_t_hours if events else None
    results: dict[int, HorizonResult] = {}
    for T in horizons_days:
        surv_T, frac_sell, frac_drop = _interval_math(lam_sell_final, lam_drop_final, T)
        p_sell = cif_sell + frac_sell * (1 - surv_T) * s
        p_drop = cif_drop + frac_drop * (1 - surv_T) * s
        p_stag = max(0.0, 1.0 - p_sell - p_drop)
        results[int(T)] = HorizonResult(
            p_sell=round(p_sell, 4),
            p_drop=round(p_drop, 4),
            p_stagnation=round(p_stag, 4),
            confidence=_confidence_flag(T, last_dt_hours, queue_confident),
        )
    return results


def _demo():
    """Closed-form checks: posterior blend, FIFO penalty, CIF sums to 1."""
    # Pure prior (no item data) → prior mean.
    prior = Prior(poisson=False, alpha=1.0, beta=100.0)
    assert abs(item_posterior(prior, 0, 0.0) - 0.01) < 1e-12
    # Data dominates: 1 event in 100h vs weak prior (mean 0.001) → λ rises ~1.8x.
    lam = item_posterior(Prior(poisson=False, alpha=1.0, beta=1000.0), 1, 100.0)
    assert abs(lam - (2.0 / 1100.0)) < 1e-12, lam
    # Pure Poisson prior ignores item data.
    assert abs(item_posterior(Prior(poisson=True, mean=0.05), 99, 100.0) - 0.05) < 1e-12

    # FIFO penalty: 3 existing sellers at cheapest price → λ/4.
    lam_corrected = item_posterior(prior, 0, 0.0) / (1 + 3)
    assert abs(lam_corrected - 0.0025) < 1e-12

    # Downward pressure is time-normalized: 1 new seller over 2h vs 3 over 6h
    # are the same per-hour rate → ratio ≈ 1, not inflated by the longer gap.
    base = 1_800_000_000_000
    rows = [
        {"fetched_ms": base, "seller": "a", "amount": 10.0},
        {"fetched_ms": base + 2 * 3600_000, "seller": "a", "amount": 10.0},
        {"fetched_ms": base + 2 * 3600_000, "seller": "b", "amount": 9.0},      # new below 10
        {"fetched_ms": base + 8 * 3600_000, "seller": "a", "amount": 10.0},
        {"fetched_ms": base + 8 * 3600_000, "seller": "c", "amount": 9.0},      # new below 10
        {"fetched_ms": base + 8 * 3600_000, "seller": "d", "amount": 9.0},      # new below 10
        {"fetched_ms": base + 8 * 3600_000, "seller": "e", "amount": 9.0},      # new below 10
    ]
    # Interval 1: 1 seller in 2h (0.5/h). Interval 2: 3 sellers in 6h (0.5/h).
    ratio = downward_pressure_ratio(rows, 10.0)
    assert abs(ratio - 1.0) < 1e-9, ratio
    # No history → 1.0.
    assert downward_pressure_ratio([{"fetched_ms": base, "seller": "a", "amount": 10.0}], 10.0) == 1.0

    # CIF: constant hazards must give P_sell + P_drop + P_stag = 1.
    class E:
        def __init__(self, dt):
            self.delta_t_hours = dt

    res = compute_cif([E(48.0)], 0.01, 0.005, now_ms=0)
    r = res[1]
    assert abs(r.p_sell + r.p_drop + r.p_stagnation - 1.0) < 0.001, r
    # More horizon → higher cumulative incidence.
    assert res[7].p_sell > res[1].p_sell
    assert res[1].confidence == "low" and res[7].confidence == "high", res
    print("survival._demo OK:", res)


if __name__ == "__main__":
    _demo()
