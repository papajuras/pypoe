"""Tests for Store stale_flip_ids — time-based staleness only."""

import json
import time
import unittest
from pathlib import Path

from pypoe.db.config import set_meta
from pypoe.flipper.store import Flip, Store

DB = Path("/tmp/test_stale_flips.db")


class TestStaleFlips(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if DB.exists():
            DB.unlink()

    def setUp(self):
        if DB.exists():
            DB.unlink()
        for q in (27, 28, 29, 30):
            set_meta(f"flipper_quality_{q}", True)
        self.store = Store(DB)
        for name in (
            "royal plate 30",
            "royal plate 27",
            "kingmaker",
        ):
            f = Flip(name=name, source_queries=["{}"], target_queries=["{}"])
            self.store.put(f)

    def test_old_flips_are_stale(self):
        past = str(time.time() - 999999)
        self.store._conn.execute("UPDATE flips SET updated_at = ?", (past,))
        self.store._conn.commit()
        stale = self.store.stale_flip_ids(3600)
        self.assertEqual(len(stale), 3)

    def test_recent_flips_not_stale(self):
        stale = self.store.stale_flip_ids(3600)
        self.assertEqual(len(stale), 0)


if __name__ == "__main__":
    unittest.main()
