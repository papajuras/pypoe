"""Local mirror of the gatherer's target-side listing snapshots.

Syncs new rows from GET /api/listings?since=<ms> into a local SQLite store
(dedup via INSERT OR IGNORE on the (flip_id, fetched_ms, rank) primary key),
prunes to HISTORY_DAYS, and exposes the snapshot history the market analysis
consumes.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path

from pypoe.flipper.gatherer_client import GathererClient

_DB = Path(__file__).resolve().parent.parent / "data" / "listings.db"
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
            CREATE TABLE IF NOT EXISTS listing_snapshots (
                flip_id    TEXT    NOT NULL,
                fetched_ms INTEGER NOT NULL,
                rank       INTEGER NOT NULL,
                seller     TEXT    NOT NULL,
                amount     REAL    NOT NULL,
                currency   TEXT    NOT NULL,
                indexed_ms INTEGER NOT NULL,
                ilvl       INTEGER,
                rarity     TEXT,
                PRIMARY KEY (flip_id, fetched_ms, rank)
            )
            """
        )
    return _conn


def max_ms() -> int:
    with _lock:
        row = _connect().execute("SELECT MAX(fetched_ms) FROM listing_snapshots").fetchone()
        return row[0] or 0


def sync(client: GathererClient) -> int:
    """Pull rows newer than the local watermark, insert new ones, prune. Returns rows added."""
    since = max_ms()
    data = client.listings(since)
    rows = data.get("rows", [])
    with _lock:
        conn = _connect()
        added = 0
        for r in rows:
            cur = conn.execute(
                "INSERT OR IGNORE INTO listing_snapshots"
                " (flip_id, fetched_ms, rank, seller, amount, currency, indexed_ms, ilvl, rarity)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (r["flip_id"], r["fetched_ms"], r["rank"], r["seller"],
                 r["amount"], r["currency"], r["indexed_ms"],
                 r.get("ilvl"), r.get("rarity")),
            )
            added += cur.rowcount
        cutoff_ms = int((time.time() - HISTORY_DAYS * 86400) * 1000)
        conn.execute("DELETE FROM listing_snapshots WHERE fetched_ms < ?", (cutoff_ms,))
        conn.commit()
    return added


def snapshots(flip_id: str, hours: int = 7 * 24) -> list[dict]:
    """All snapshot rows for one flip within the window, oldest first."""
    cutoff_ms = int((time.time() - hours * 3600) * 1000)
    with _lock:
        rows = _connect().execute(
            "SELECT fetched_ms, rank, seller, amount, currency, indexed_ms, ilvl, rarity"
            " FROM listing_snapshots"
            " WHERE flip_id = ? AND fetched_ms >= ?"
            " ORDER BY fetched_ms, rank",
            (flip_id, cutoff_ms),
        ).fetchall()
    return [
        {
            "fetched_ms": r[0], "rank": r[1], "seller": r[2], "amount": r[3],
            "currency": r[4], "indexed_ms": r[5], "ilvl": r[6], "rarity": r[7],
        }
        for r in rows
    ]
