"""Tests for Store.next_to_price — DB wiring of the scheduler policy."""

import json
import time
import unittest
from pathlib import Path

from gatherer.store import Flip, Store

DB = Path("/tmp/test_next_to_price.db")


class TestNextToPrice(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if DB.exists():
            DB.unlink()

    def setUp(self):
        if DB.exists():
            DB.unlink()
        self.store = Store(DB)
        for q in (27, 28, 29, 30):
            self.store.set_meta(f"flipper_quality_{q}", True)

    def _age(self, flip: Flip, hours: float):
        flip.updated_at = time.time() - hours * 3600
        self.store._conn.execute(
            "UPDATE flips SET updated_at = ? WHERE id = ?",
            (str(flip.updated_at), flip.id),
        )
        self.store._conn.commit()

    def _flip(self, name="royal plate 28 split", multiplier=1.0, cost=0, fast=True) -> Flip:
        f = Flip(name=name, source_queries=["{}"], target_queries=["{}"],
                 multiplier=multiplier, cost=cost, fast=fast)
        self.store.put(f)
        return f

    def _price(self, flip: Flip, src=5.0, sc=5, tgt=8.0, tc=5):
        self.store.save_price(flip.id, src, sc, tgt, tc)

    def test_never_priced_picked_first(self):
        hot = self._flip("royal plate 28 split")
        self._price(hot, src=5.0, tgt=10.0)   # roi=+100%
        fresh = self._flip("brand new 27")
        fids = self.store.next_to_price(10)
        self.assertEqual(fids, [fresh.id])

    def test_hot_due_before_loser_at_same_age(self):
        hot = self._flip("royal plate 28 split")
        self._price(hot, src=5.0, tgt=12.5)    # roi=+150%
        loser = self._flip("lich's circlet 27")
        self._price(loser, src=10.0, tgt=2.0)  # roi=-80%
        self._age(hot, 25)
        self._age(loser, 25)
        fids = self.store.next_to_price(10)
        self.assertEqual(fids, [hot.id, loser.id])

    def test_quality_filter_applies(self):
        q27 = self._flip("royal plate 27 split")
        self._price(q27, src=5.0, tgt=12.5)
        self._age(q27, 25)
        self.store.set_meta("flipper_quality_27", False)
        self.assertEqual(self.store.next_to_price(10), [])

    def test_illiquid_due_at_6h(self):
        ill = self._flip("two-toned boots 29")
        self.store.save_price(ill.id, 0.0, 0, 0.0, 0)  # zero counts → illiquid
        self._age(ill, 5)
        self.assertEqual(self.store.next_to_price(10), [])
        self._age(ill, 7)
        self.assertEqual(self.store.next_to_price(10), [ill.id])

    def test_history_returns_current_and_historical_rows(self):
        f = self._flip("royal plate 28")
        self.store.save_price(f.id, 5.0, 5, 8.0, 5, source_total=100, target_total=40)
        self.store.save_price(f.id, 6.0, 5, 9.0, 5, source_total=90, target_total=30)
        rows = self.store.history(0)
        self.assertEqual(len(rows), 2)
        self.assertEqual([r["target_avg"] for r in rows], [8.0, 9.0])
        self.assertEqual(rows[-1]["target_total"], 30)
        self.assertEqual(rows[-1]["source_total"], 90)

    def test_history_since_filters_by_ms(self):
        f = self._flip("royal plate 28")
        self.store.save_price(f.id, 5.0, 5, 8.0, 5)
        rows = self.store.history(0)
        self.assertEqual(len(rows), 1)
        since = rows[0]["fetched_ms"] - 1
        self.assertEqual(self.store.history(since), [rows[0]])
        self.assertEqual(self.store.history(rows[0]["fetched_ms"] + 1), [])

    def test_save_listings_persists_and_prunes(self):
        f = self._flip("royal plate 28")
        rows = [
            {"rank": i, "seller": f"seller{i}", "amount": 10 + i, "currency": "divine",
             "indexed_ms": 1786000000000 + i, "ilvl": 86, "rarity": "Rare"}
            for i in range(10)
        ]
        self.store.save_listings(f.id, 1786100000000, rows)
        got = self.store._conn.execute(
            "SELECT COUNT(*) FROM listing_snapshots WHERE flip_id = ?", (f.id,)
        ).fetchone()[0]
        self.assertEqual(got, 10)
        # old rows pruned
        self.store.save_listings(f.id, 1000000, rows[:1])  # 1970 ms
        self.store.prune_listings(60)
        got = self.store._conn.execute(
            "SELECT COUNT(*) FROM listing_snapshots WHERE flip_id = ?", (f.id,)
        ).fetchone()[0]
        self.assertEqual(got, 10)  # only the recent batch survived

    def test_db_size_bytes_reports_real_file(self):
        size = self.store.db_size_bytes()
        self.assertGreater(size, 0)


if __name__ == "__main__":
    unittest.main()
