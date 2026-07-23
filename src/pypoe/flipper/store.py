from __future__ import annotations

import json
import re
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from pypoe.db.schema import apply as migrate

DB = Path("db/flips.db")


def _extract_query(raw: str) -> tuple[str, str]:
    raw = raw.strip()
    league = "Standard"
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

    source_type: str = "query"
    source_queries: list[str] = field(default_factory=list)
    source_ninja_item: str = ""
    source_ninja_type: str = "DivinationCard"
    target_type: str = "query"
    target_queries: list[str] = field(default_factory=list)
    target_ninja_item: str = ""
    target_ninja_type: str = "DivinationCard"
    multiplier: float = 1.0
    cost: int = 0
    enabled: bool = True
    notes: str = ""
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

                    "source_type": flip.source_type,
                    "source_queries": flip.source_queries,
                    "source_ninja_item": flip.source_ninja_item,
                    "source_ninja_type": flip.source_ninja_type,
                    "target_type": flip.target_type,
                    "target_queries": flip.target_queries,
                    "target_ninja_item": flip.target_ninja_item,
                    "target_ninja_type": flip.target_ninja_type,
                    "multiplier": flip.multiplier,
                    "cost": flip.cost,
                    "enabled": flip.enabled,
                    "notes": flip.notes,
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

            source_type=data.get("source_type", "query"),
            source_queries=data.get("source_queries") or data.get("source_urls", []),
            source_ninja_item=data.get("source_ninja_item", ""),
            source_ninja_type=data.get("source_ninja_type", "DivinationCard"),
            target_type=data.get("target_type", "query"),
            target_queries=data.get("target_queries") or data.get("target_urls", []),
            target_ninja_item=data.get("target_ninja_item", ""),
            target_ninja_type=data.get("target_ninja_type", "DivinationCard"),
            multiplier=data["multiplier"],
            cost=data.get("cost", 0),
            enabled=data.get("enabled", True),
            notes=data.get("notes", ""),
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
        from pypoe.db.config import get_meta
        disabled = {q for q in (27, 28, 29, 30) if not get_meta(f"flipper_quality_{q}", True)}
        cutoff = time.time() - max_age
        rows = self._conn.execute(
            "SELECT id, data FROM flips WHERE CAST(updated_at AS REAL) < ?", (cutoff,)
        ).fetchall()
        if not disabled:
            return [r[0] for r in rows]
        result = []
        for rid, rdata in rows:
            name = json.loads(rdata).get("name", "")
            for q in disabled:
                if f" {q} " in f" {name} ":
                    break
            else:
                result.append(rid)
        return result

    def oldest_unpriced(self, limit: int) -> list[str]:
        import logging
        _log = logging.getLogger(__name__)
        rows = self._conn.execute(
            "SELECT id, CAST(updated_at AS REAL) FROM flips ORDER BY CAST(updated_at AS REAL) ASC LIMIT ?",
            (limit,),
        ).fetchall()
        fids = [r[0] for r in rows]
        if fids:
            _log.info("oldest_unpriced: %d flips (oldest=%.0f newest_in_batch=%.0f)",
                      len(fids), rows[0][1], rows[-1][1])
        return fids

    def _prune_history(self):
        self._conn.execute(
            "DELETE FROM price_history WHERE fetched_at < datetime('now', '-60 days')"
        )
