"""Pure policy: which flips to queue and when. No I/O.

Rules live here so they can be tested without a DB or the trade API
(gatherer/tests/test_scheduler.py).
"""

from __future__ import annotations

from dataclasses import dataclass

TARGET_QUEUE = 10

HOT_ROI = 1.0          # ROI >= 100% → hottest cadence
HOT_COOLDOWN = 45 * 60
LOSS_ROI = -0.5        # ROI <= -50% → slowest cadence
LOSS_COOLDOWN = 4 * 3600
ILLIQUID_COOLDOWN = 2 * 3600   # priced but no listings (no signal)
SLOW_COOLDOWN = 4 * 3600       # manual fast=False override
NEAR_LO = -0.25        # near-break-even band edges
NEAR_HI = 0.25
NEAR_COOLDOWN = 60 * 60        # 1h inside the band — catch trend reversals


@dataclass
class FlipState:
    id: str
    priced: bool                # False = never priced → queue ASAP
    roi: float | None           # None = illiquid / no signal
    updated_at: float
    fast: bool = True


def roi(source_avg: float, target_avg: float, multiplier: float, cost: float) -> float | None:
    total = source_avg + cost
    if source_avg <= 0 or total <= 0:
        return None
    return (target_avg * multiplier - total) / total


def cooldown(state: FlipState) -> float:
    if not state.priced:
        return 0.0
    if not state.fast:
        return SLOW_COOLDOWN
    if state.roi is None:
        return ILLIQUID_COOLDOWN
    if state.roi <= LOSS_ROI:
        return LOSS_COOLDOWN
    if state.roi >= HOT_ROI:
        return HOT_COOLDOWN
    # Piecewise-linear between the near-break-even band and the two caps.
    if state.roi >= NEAR_HI:
        t = (state.roi - NEAR_HI) / (HOT_ROI - NEAR_HI)
        return NEAR_COOLDOWN + t * (HOT_COOLDOWN - NEAR_COOLDOWN)
    if state.roi <= NEAR_LO:
        t = (NEAR_LO - state.roi) / (NEAR_LO - LOSS_ROI)
        return NEAR_COOLDOWN + t * (LOSS_COOLDOWN - NEAR_COOLDOWN)
    return NEAR_COOLDOWN


def select(flips, now: float, limit: int) -> list[str]:
    due = [f for f in flips if now - f.updated_at >= cooldown(f)]
    # Most-overdue first — a hard fairness bound so no flip starves forever.
    # ROI only breaks ties between flips that are equally overdue.
    due.sort(key=lambda f: (
        -(now - f.updated_at),
        0 if not f.priced else 1,
        -(f.roi if f.roi is not None else -1e9),
    ))
    return [f.id for f in due[:limit]]
