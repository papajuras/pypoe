"""Tests for gatherer.scheduler — pure queue-selection policy.

Run: uv run python -m gatherer.tests.test_scheduler
"""

import unittest

from gatherer.scheduler import FlipState, cooldown, roi, select


def fs(id_, roi_, updated_at, priced=True, fast=True):
    return FlipState(id=id_, priced=priced, roi=roi_, updated_at=updated_at, fast=fast)


NOW = 1_000_000.0


def age(hours):
    return NOW - hours * 3600


class TestCooldown(unittest.TestCase):
    def test_never_priced_queued_immediately(self):
        self.assertEqual(cooldown(fs("x", None, NOW, priced=False)), 0.0)

    def test_loss_floor_4h(self):
        self.assertEqual(cooldown(fs("x", -0.8, NOW)), 4 * 3600)
        self.assertEqual(cooldown(fs("x", -0.5, NOW)), 4 * 3600)
        self.assertLess(cooldown(fs("x", -0.49, NOW)), 4 * 3600)

    def test_hot_cap_45min(self):
        self.assertEqual(cooldown(fs("x", 1.0, NOW)), 45 * 60)
        self.assertEqual(cooldown(fs("x", 1.4, NOW)), 45 * 60)

    def test_break_even_band_1h(self):
        # Inside [-25%, +25%] the cadence is a flat 1h so trend reversals
        # near break-even get caught quickly.
        for roi in (-0.25, 0.0, 0.25):
            self.assertEqual(cooldown(fs("x", roi, NOW)), 60 * 60)

    def test_gradual_between(self):
        zero = cooldown(fs("x", 0.0, NOW))
        hot = cooldown(fs("x", 0.5, NOW))
        self.assertEqual(zero, 60 * 60)
        self.assertGreater(zero, hot)
        self.assertGreaterEqual(hot, 45 * 60)
        self.assertLess(hot, 60 * 60)
        lossy = cooldown(fs("x", -0.3, NOW))
        self.assertGreater(lossy, 60 * 60)
        self.assertLess(lossy, 4 * 3600)

    def test_illiquid_2h(self):
        self.assertEqual(cooldown(fs("x", None, NOW)), 2 * 3600)

    def test_fast_false_forced_4h(self):
        self.assertEqual(cooldown(fs("x", 1.0, NOW, fast=False)), 4 * 3600)
        self.assertEqual(cooldown(fs("x", -0.8, NOW, fast=False)), 4 * 3600)


class TestSelect(unittest.TestCase):
    def test_most_overdue_first(self):
        # Fairness: the flip overdue the longest wins, regardless of ROI,
        # so a starved loser beats a freshly-due hot flip.
        fids = select(
            [fs("loser", -0.8, age(20)), fs("hot", 0.5, age(1))],
            NOW, 10,
        )
        self.assertEqual(fids, ["loser", "hot"])

    def test_roi_breaks_ties_on_equal_overdue(self):
        fids = select(
            [fs("loser", -0.8, age(25)), fs("hot", 0.5, age(25))],
            NOW, 10,
        )
        self.assertEqual(fids, ["hot", "loser"])

    def test_never_priced_first_when_equally_overdue(self):
        fids = select(
            [fs("priced", 0.5, age(25)), fs("fresh", None, age(25), priced=False)],
            NOW, 10,
        )
        self.assertEqual(fids, ["fresh", "priced"])

    def test_loser_not_due_until_4h(self):
        fids = select([fs("loser", -0.8, age(3))], NOW, 10)
        self.assertEqual(fids, [])
        fids = select([fs("loser", -0.8, age(5))], NOW, 10)
        self.assertEqual(fids, ["loser"])

    def test_illiquid_due_at_2h_not_1h(self):
        self.assertEqual(select([fs("ill", None, age(1))], NOW, 10), [])
        self.assertEqual(select([fs("ill", None, age(3))], NOW, 10), ["ill"])

    def test_break_even_due_after_1h(self):
        self.assertEqual(select([fs("n", 0.0, age(0.5))], NOW, 10), [])
        self.assertEqual(select([fs("n", 0.0, age(2))], NOW, 10), ["n"])

    def test_hot_cap_due_just_after_45min(self):
        self.assertEqual(select([fs("h", 1.0, age(0.7))], NOW, 10), [])
        self.assertEqual(select([fs("h", 1.0, age(0.8))], NOW, 10), ["h"])

    def test_limit_respected_with_overdue_order(self):
        flips = [
            fs("never", None, age(2), priced=False),
            fs("mid", 0.0, age(25)),
            fs("hot", 0.5, age(10)),
            fs("ill", None, age(5)),
        ]
        self.assertEqual(select(flips, NOW, 2), ["mid", "hot"])
        self.assertEqual(select(flips, NOW, 4), ["mid", "hot", "ill", "never"])


class TestRoi(unittest.TestCase):
    def test_matches_ui_formula(self):
        # UI: cost = src + craft cost, rev = tgt*mult, roi = (rev-cost)/cost
        r = roi(5.0, 8.0, 1.5, 1.0)
        assert r is not None
        self.assertAlmostEqual(r, 1.0)

    def test_none_when_no_cost(self):
        self.assertIsNone(roi(0.0, 5.0, 1.0, 0.0))
        self.assertIsNone(roi(5.0, 5.0, 1.0, -5.0))


if __name__ == "__main__":
    unittest.main()
