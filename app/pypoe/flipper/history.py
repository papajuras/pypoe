"""Local mirror of the gatherer's price history.

Syncs new rows from GET /api/history?since=<ms> into a local SQLite store
(dedup via INSERT OR IGNORE on the (flip_id, fetched_ms) primary key) and
prunes to HISTORY_DAYS.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path

from pypoe.flipper.gatherer_client import GathererClient

_DB = Path(__file__).resolve().parent.parent / "data" / "history.db"
HISTORY_DAYS = 60   # mirror the gatherer's retention

_lock = threading.Lock()
_conn: sqlite3.Connection | None = None


def _connect() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _DB.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(_DB, check_same_thread=False)
        _conn.execute(
            """
            CREATE TABLE IF NOT EXISTS price_history (
                flip_id TEXT NOT NULL,
                fetched_ms INTEGER NOT NULL,
                source_avg REAL NOT NULL,
                target_avg REAL NOT NULL,
                source_total INTEGER NOT NULL DEFAULT 0,
                target_total INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (flip_id, fetched_ms)
            )
            """
        )
    return _conn


def max_ms() -> int:
    with _lock:
        row = _connect().execute("SELECT MAX(fetched_ms) FROM price_history").fetchone()
        return row[0] or 0


def sync(client: GathererClient) -> int:
    """Pull rows newer than the local watermark, insert new ones, prune. Returns rows added."""
    since = max_ms()
    data = client.history(since)
    rows = data.get("rows", [])
    with _lock:
        conn = _connect()
        added = 0
        for r in rows:
            cur = conn.execute(
                "INSERT OR IGNORE INTO price_history"
                " (flip_id, fetched_ms, source_avg, target_avg, source_total, target_total)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (r["flip_id"], r["fetched_ms"], r["source_avg"], r["target_avg"],
                 r.get("source_total", 0), r.get("target_total", 0)),
            )
            added += cur.rowcount
        cutoff_ms = int((time.time() - HISTORY_DAYS * 86400) * 1000)
        conn.execute("DELETE FROM price_history WHERE fetched_ms < ?", (cutoff_ms,))
        conn.commit()
    return added


def _demo():
    """Self-check: sync dedups and advances the watermark."""
    import tempfile

    global _conn, _DB
    _conn = None
    _DB = Path(tempfile.mkdtemp()) / "hist.db"
    base = int(time.time() * 1000)

    class FakeClient:
        def __init__(self, rows):
            self.rows = rows

        def history(self, since_ms):
            return {"rows": [r for r in self.rows if r["fetched_ms"] > since_ms]}

    rows = [
        {"flip_id": "f1", "fetched_ms": base + 1000, "source_avg": 1.0, "target_avg": 2.0,
         "source_total": 5, "target_total": 7},
        {"flip_id": "f1", "fetched_ms": base + 2000, "source_avg": 1.0, "target_avg": 2.0,
         "source_total": 5, "target_total": 7},
    ]
    assert sync(FakeClient(rows)) == 2, "two rows added"
    assert sync(FakeClient(rows)) == 0, "dedup: no rows re-added"
    assert max_ms() == base + 2000, max_ms()
    print("history._demo OK")


if __name__ == "__main__":
    _demo()
