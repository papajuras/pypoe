from __future__ import annotations

import json
import re
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from db.schema import apply as migrate

DB = Path("db/flips.db")


def _extract_query(raw: str) -> tuple[str, str]:
    raw = raw.strip()
    league = "Mirage"
    if raw.startswith("curl "):
        m = re.search(r"curl\s+'[^']*/search/(\w+)", raw)
        if m:
            league = m.group(1)
        m = re.search(r"--data-raw\s+'([^']*)'|--data-raw\s+\"([^\"]*)\"|--data-raw\s+([^\s]+)", raw)
        raw = (m.group(1) or m.group(2) or m.group(3) or raw) if m else raw
    if raw.startswith("{"):
        json.loads(raw)
    return raw, league


@dataclass
class Flip:
    name: str = ""
    league: str = "Mirage"
    source_queries: list[str] = field(default_factory=list)
    target_queries: list[str] = field(default_factory=list)
    multiplier: float = 1.0
    cost: int = 0
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class Store:
    def __init__(self, db: str | Path = DB):
        self._conn = sqlite3.connect(str(db), check_same_thread=False)
        migrate(self._conn)

    def _row(self, flip: Flip) -> tuple[str, str, str, str]:
        return (
            flip.id,
            json.dumps(
                {
                    "name": flip.name,
                    "league": flip.league,
                    "source_queries": flip.source_queries,
                    "target_queries": flip.target_queries,
                    "multiplier": flip.multiplier,
                    "cost": flip.cost,
                }
            ),
            str(flip.created_at),
            str(flip.updated_at),
        )

    def _flip(self, row: tuple[str, str, str, str]) -> Flip:
        data = json.loads(row[1])
        return Flip(
            id=row[0],
            name=data.get("name", "Unnamed"),
            league=data.get("league", "Mirage"),
            source_queries=data.get("source_queries") or data.get("source_urls", []),
            target_queries=data.get("target_queries") or data.get("target_urls", []),
            multiplier=data["multiplier"],
            cost=data.get("cost", 0),
            created_at=float(row[2]),
            updated_at=float(row[3]),
        )

    def put(self, flip: Flip):
        flip.updated_at = time.time()
        self._conn.execute(
            "INSERT OR REPLACE INTO flips (id, data, created_at, updated_at) VALUES (?, ?, ?, ?)",
            self._row(flip),
        )
        self._conn.commit()

    def get(self, flip_id: str) -> Flip | None:
        row = self._conn.execute(
            "SELECT id, data, created_at, updated_at FROM flips WHERE id = ?", (flip_id,)
        ).fetchone()
        return self._flip(row) if row else None

    def list(self) -> list[Flip]:
        rows = self._conn.execute(
            "SELECT id, data, created_at, updated_at FROM flips ORDER BY updated_at DESC"
        ).fetchall()
        return [self._flip(r) for r in rows]

    def delete(self, flip_id: str):
        self._conn.execute("DELETE FROM flips WHERE id = ?", (flip_id,))
        self._conn.commit()

    # ── prices ─────────────────────────────────────────────────

    PRUNE_AFTER = 60 * 60 * 24 * 60  # 2 months in seconds

    def save_price(self, flip_id: str, source_avg: float, source_count: int, target_avg: float, target_count: int):
        old = self._conn.execute(
            "SELECT flip_id, source_avg, source_count, target_avg, target_count, fetched_at FROM prices WHERE flip_id = ?",
            (flip_id,),
        ).fetchone()
        if old:
            self._conn.execute(
                "INSERT INTO price_history (flip_id, source_avg, source_count, target_avg, target_count, fetched_at) VALUES (?, ?, ?, ?, ?, ?)",
                old,
            )
        self._conn.execute(
            "INSERT OR REPLACE INTO prices (flip_id, source_avg, source_count, target_avg, target_count, fetched_at) VALUES (?, ?, ?, ?, ?, datetime('now'))",
            (flip_id, source_avg, source_count, target_avg, target_count),
        )
        self._prune_history()
        self._conn.commit()

    def get_price(self, flip_id: str) -> dict | None:
        row = self._conn.execute(
            "SELECT source_avg, source_count, target_avg, target_count, fetched_at FROM prices WHERE flip_id = ?",
            (flip_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "source_avg": row[0],
            "source_count": row[1],
            "target_avg": row[2],
            "target_count": row[3],
            "fetched_at": row[4],
        }

    def stale_flip_ids(self, max_age: float) -> list[str]:
        cutoff = time.time() - max_age
        rows = self._conn.execute(
            "SELECT id FROM flips WHERE CAST(updated_at AS REAL) < ?", (cutoff,)
        ).fetchall()
        return [r[0] for r in rows]

    def _prune_history(self):
        self._conn.execute(
            "DELETE FROM price_history WHERE fetched_at < datetime('now', '-60 days')"
        )
