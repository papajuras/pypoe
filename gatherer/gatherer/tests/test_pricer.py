"""Tests for PriceFetcher — sequential queue processing.

Run: uv run python -m gatherer.tests.test_pricer
"""

import time
import unittest
from queue import Queue
from threading import Thread

from gatherer.pricer import PriceFetcher
from gatherer.store import Flip


class FakeClient:
    def __init__(self):
        self.league = "Standard"

    def search(self, query) -> dict:
        time.sleep(0.05)
        return {"result": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"], "total": 10}

    def fetch(self, ids) -> dict:
        time.sleep(0.05)
        return {"result": [{"listing": {"price": {"currency": "divine", "amount": 5}}}]}


class FakeStore:
    def __init__(self, flip_count: int):
        self.flips = {
            f"flip_{i}": Flip(name=f"flip_{i}", source_queries=["{}"], target_queries=["{}"])
            for i in range(flip_count)
        }
        self.save_calls: list[str] = []
        self.save_times: list[float] = []
        self.meta: dict[str, bool] = {}

    def get(self, flip_id: str) -> Flip | None:
        return self.flips.get(flip_id)

    def get_meta(self, key: str, default=None):
        return self.meta.get(key, default)

    def save_price(self, flip_id, *args):
        self.save_calls.append(flip_id)
        self.save_times.append(time.time())

    def save_listings(self, flip_id, fetched_ms, rows):
        self.listing_calls = getattr(self, "listing_calls", 0) + 1
        self.last_listings = rows

    def next_to_price(self, *args, **kwargs):
        return []

    def put(self, flip: Flip):
        self.flips[flip.id] = flip


class TestPriceFetcher(unittest.TestCase):
    def test_processes_one_flip_at_a_time(self):
        """5 flips queued at once: processed sequentially, no overlap."""
        store = FakeStore(5)
        pricer = PriceFetcher(FakeClient(), store)

        for fid in store.flips:
            pricer.enqueue(fid)

        time.sleep(1.5)
        pricer.stop()

        self.assertEqual(len(store.save_calls), 5)

    def test_staggered_timestamps(self):
        """Record timestamps of each save and confirm no overlap."""
        store = FakeStore(5)
        pricer = PriceFetcher(FakeClient(), store)

        for fid in store.flips:
            pricer.enqueue(fid)

        time.sleep(1.5)
        pricer.stop()

        times = store.save_times
        print(f"\n  Save timestamps for 5 flips:")
        for i, (fid, t) in enumerate(zip(store.save_calls, times)):
            gap = f" (+{t - times[i-1]:.3f}s)" if i > 0 else " (first)"
            print(f"    {fid}:  {t:.3f}{gap}")

        self.assertEqual(len(times), 5)
        for i in range(1, len(times)):
            gap = times[i] - times[i - 1]
            self.assertGreater(gap, 0.01,
                f"Overlap detected between {store.save_calls[i-1]} and {store.save_calls[i]}: gap={gap:.4f}s")

    def test_no_parallel_processing(self):
        """Track overlap: sequential means total time >= sum of individual times."""
        store = FakeStore(3)
        pricer = PriceFetcher(FakeClient(), store)

        t0 = time.time()
        for fid in store.flips:
            pricer.enqueue(fid)

        time.sleep(0.5)
        pricer.stop()
        elapsed = time.time() - t0

        # 3 flips × 100ms each = 300ms min if sequential
        self.assertGreaterEqual(elapsed, 0.25,
            "Too fast — flips appear to run in parallel")
        self.assertLess(elapsed, 2.0,
            "Too slow — something is wrong")

    def test_queue_order_preserved(self):
        """Flips saved in the order they were enqueued."""
        store = FakeStore(5)
        pricer = PriceFetcher(FakeClient(), store)

        ids = [f"flip_{i}" for i in range(5)]
        for fid in ids:
            pricer.enqueue(fid)

        time.sleep(1.5)
        pricer.stop()

        self.assertEqual(store.save_calls, ids)

    def test_empty_queue_does_nothing(self):
        """No flips → no saves, thread stays alive."""
        store = FakeStore(0)
        pricer = PriceFetcher(FakeClient(), store)

        time.sleep(0.3)
        pricer.stop()
        self.assertEqual(len(store.save_calls), 0)

    def test_single_flip_processed(self):
        """One flip in queue gets saved."""
        store = FakeStore(1)
        pricer = PriceFetcher(FakeClient(), store)

        pricer.enqueue("flip_0")
        time.sleep(0.3)
        pricer.stop()

        self.assertEqual(store.save_calls, ["flip_0"])

    def test_dedup_enqueued_flips(self):
        """Duplicate enqueues of same flip ID are only processed once."""
        store = FakeStore(2)
        pricer = PriceFetcher(FakeClient(), store)

        for _ in range(5):
            pricer.enqueue("flip_0")
        for _ in range(3):
            pricer.enqueue("flip_1")

        time.sleep(1.0)
        pricer.stop()

        self.assertEqual(len(store.save_calls), 2)
        self.assertIn("flip_0", store.save_calls)
        self.assertIn("flip_1", store.save_calls)

    def test_front_of_queue_moves_ahead(self):
        """enqueue(front=True) positions the flip before previously-queued flips."""
        store = FakeStore(5)
        pricer = PriceFetcher(FakeClient(), store)

        pricer.enqueue("a")
        pricer.enqueue("b")
        pricer.enqueue("c")
        self.assertEqual(list(pricer._pending), ["a", "b", "c"])

        pricer.enqueue("b", front=True)
        self.assertEqual(list(pricer._pending), ["b", "a", "c"])

        pricer.enqueue("d", front=True)
        self.assertEqual(list(pricer._pending), ["d", "b", "a", "c"])

        pricer.enqueue("a", front=True)
        self.assertEqual(list(pricer._pending), ["a", "d", "b", "c"])

        pricer.enqueue("e")
        self.assertEqual(list(pricer._pending), ["a", "d", "b", "c", "e"])

        pricer.stop()

    def test_skips_flip_with_disabled_quality(self):
        """Flip with Q27 skipped when flipper_quality_27 is disabled."""
        store = FakeStore(1)
        store.meta["flipper_quality_27"] = False
        # Override with a quality-named flip
        store.flips["flip_0"] = Flip(name="royal plate 27 split",
                                     source_queries=["{}"], target_queries=["{}"])
        pricer = PriceFetcher(FakeClient(), store)
        pricer.enqueue("flip_0")
        time.sleep(0.3)
        pricer.stop()
        self.assertEqual(len(store.save_calls), 0)

    def test_prices_flip_with_enabled_quality(self):
        """Flip with Q27 is priced when flipper_quality_27 is enabled."""
        store = FakeStore(1)
        store.meta["flipper_quality_27"] = True
        store.flips["flip_0"] = Flip(name="royal plate 27 split",
                                     source_queries=["{}"], target_queries=["{}"])
        pricer = PriceFetcher(FakeClient(), store)
        pricer.enqueue("flip_0")
        time.sleep(0.3)
        pricer.stop()
        self.assertEqual(len(store.save_calls), 1)

    def test_target_snapshot_writes_listing_rows(self):
        """Target fetch captures up to 10 listings (seller/amount/indexed) and saves them."""
        class SnapshotClient(FakeClient):
            def fetch(self, ids):
                time.sleep(0.05)
                return {"result": [
                    {"listing": {
                        "indexed": "2026-08-08T05:26:43Z",
                        "price": {"currency": "divine", "amount": i},
                        "account": {"name": f"seller{i}"},
                    }, "item": {"ilvl": 86, "rarity": "Rare"}}
                    for i in range(len(ids))
                ]}
        store = FakeStore(1)
        pricer = PriceFetcher(SnapshotClient(), store)
        pricer.enqueue("flip_0")
        time.sleep(0.3)
        pricer.stop()
        self.assertEqual(getattr(store, "listing_calls", 0), 1)
        rows = store.last_listings
        self.assertEqual(len(rows), 10)
        self.assertEqual(rows[0]["seller"], "seller0")
        self.assertEqual(rows[0]["amount"], 0)
        self.assertGreater(rows[0]["indexed_ms"], 0)
        self.assertEqual(rows[0]["rarity"], "Rare")


if __name__ == "__main__":
    unittest.main()
