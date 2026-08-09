"""Gamma-Poisson market priors via method-of-moments fit.

Fits a Gamma prior over event rate λ from per-interval observed rates,
with numeric guards and a conservative hardcoded default for the cold-start /
insufficient-data case.

Units are per-hour. Posterior update (Phase 5):  λ = (α + k) / (β + T_exposure).
"""

from __future__ import annotations

import logging
import math
import statistics
from dataclasses import dataclass

logger = logging.getLogger(__name__)

EPSILON_REL = 1e-4
VAR_FLOOR = 1e-6

# Conservative warm-start prior, used only when fewer than MIN_INTERVALS
# intervals exist (see engine.MIN_INTERVALS). alpha is a pseudo-event count,
# beta a pseudo-exposure in hours. alpha=0.25 ≈ 1 sale per ~4 days; the prior
# evaporates quickly once real observations arrive.
DEFAULT_PRIOR = {
    "sell": {"alpha": 0.25, "beta": 600.0},
    "drop": {"alpha": 0.1, "beta": 600.0},
}


@dataclass
class GammaParams:
    alpha: float
    beta: float


@dataclass
class Prior:
    """Gamma-Poisson prior. poisson=True → degenerate pure-Poisson (mean rate)."""
    poisson: bool
    alpha: float = 0.0
    beta: float = 0.0
    mean: float = 0.0

    @property
    def mean_rate(self) -> float:
        return self.mean if self.poisson else self.alpha / self.beta


def _fit_gamma(rates: list[float]) -> GammaParams | None:
    """Method-of-moments Gamma fit. Returns None when the data can't support a fit."""
    if len(rates) < 2:
        return None
    mean_rate = statistics.mean(rates)
    if mean_rate <= 0:
        return None
    try:
        var_rate = statistics.variance(rates)
    except statistics.StatisticsError:
        return None

    var_safe = max(var_rate, EPSILON_REL * mean_rate**2, VAR_FLOOR)
    if var_safe <= mean_rate:
        # underdispersed / Poisson-like → pure Poisson fallback, no shrinkage
        return None
    return GammaParams(alpha=mean_rate**2 / var_safe, beta=mean_rate / var_safe)


def _prior_from(rates: list[float]) -> Prior:
    """Gamma fit; underdispersed / sparse rates degrade to pure Poisson."""
    gamma = _fit_gamma(rates)
    if gamma is not None:
        return Prior(poisson=False, alpha=gamma.alpha, beta=gamma.beta)
    if rates:
        return Prior(poisson=True, mean=statistics.mean(rates))
    return Prior(poisson=True, mean=0.0)


def fit_prior(rates_sell: list[float], rates_drop: list[float]) -> dict[str, Prior]:
    """Fit sell + drop priors from collected rates. Always returns both entries.

    A category whose pooled rate is zero (all-zero intervals — enough data but
    no events yet) is floored at DEFAULT_PRIOR instead of 0: an unobserved
    event is not proof it never happens.
    """
    return {
        "sell": _floor_zero(_prior_from(rates_sell), "sell"),
        "drop": _floor_zero(_prior_from(rates_drop), "drop"),
    }


def _floor_zero(prior: Prior, key: str) -> Prior:
    if prior.mean_rate <= 0.0:
        logger.info("fit_prior: %s rate is zero — using DEFAULT_PRIOR floor", key)
        return Prior(poisson=False, alpha=DEFAULT_PRIOR[key]["alpha"],
                     beta=DEFAULT_PRIOR[key]["beta"])
    return prior


def resolve_prior(
    events_by_flip: dict[str, list],
    flip_keys: dict[str, tuple[str, ...]],
    item_type: str,
    refresh_tier: str,
) -> dict[str, Prior]:
    """Fallback chain: (type, tier) → (type,) → global → DEFAULT_PRIOR.

    events_by_flip: flip_id -> list[IntervalEvent]; flip_keys: flip_id -> group key.
    Returns {"sell": Prior, "drop": Prior}.
    """
    from pypoe.analysis.engine import MIN_INTERVALS, collect_rates

    def try_key(key: tuple[str, ...]):
        rates_sell, rates_drop, n = collect_rates(events_by_flip, key, flip_keys)
        if n < MIN_INTERVALS:
            return None
        return fit_prior(rates_sell, rates_drop)

    for key in [(item_type, refresh_tier), (item_type,), ("global",)]:
        prior = try_key(key)
        if prior is not None:
            return prior

    logger.info("resolve_prior: insufficient data — using DEFAULT_PRIOR")
    return {
        "sell": Prior(poisson=False, alpha=DEFAULT_PRIOR["sell"]["alpha"],
                      beta=DEFAULT_PRIOR["sell"]["beta"]),
        "drop": Prior(poisson=False, alpha=DEFAULT_PRIOR["drop"]["alpha"],
                      beta=DEFAULT_PRIOR["drop"]["beta"]),
    }


def _demo():
    """Verify method-of-moments fit recovers the generating mean."""
    import random

    random.seed(7)
    # Heterogeneous items (lognormal, wide spread) → var > mean → Gamma fits.
    rates = [random.lognormvariate(-3.9, 2.0) for _ in range(200)]
    p = _prior_from(rates)
    assert not p.poisson and p.alpha > 0 and p.beta > 0
    mean = statistics.mean(rates)
    assert 0.5 * mean < p.mean_rate < 1.5 * mean, (p, mean)

    assert _prior_from([0.5]).poisson  # too few points → Poisson mean
    assert _prior_from([0.0, 0.0]).mean == 0.0  # raw all-zero → zero mean

    # underdispersion (constant rate) → Poisson fallback, no Gamma fit
    q = _prior_from([0.02] * 50)
    assert q.poisson and abs(q.mean - 0.02) < 1e-12, q

    # Fix 2: a group with intervals but zero events floors at DEFAULT_PRIOR, not 0.
    fp = fit_prior([0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0])
    assert fp["sell"].mean_rate == DEFAULT_PRIOR["sell"]["alpha"] / DEFAULT_PRIOR["sell"]["beta"], fp
    assert fp["drop"].mean_rate == DEFAULT_PRIOR["drop"]["alpha"] / DEFAULT_PRIOR["drop"]["beta"], fp
    # Fix 1: pooled rate includes zero intervals — 1 sale in 2h across 4 intervals
    # (2h each) is 0.125/h, not 0.5/h.
    fp2 = fit_prior([0.0, 0.0, 0.0, 0.5], [0.0] * 4)
    assert abs(fp2["sell"].mean_rate - 0.125) < 1e-9, fp2
    print("prior._demo OK:", p)


if __name__ == "__main__":
    _demo()
