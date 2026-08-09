from __future__ import annotations

import json
import re
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from .config import data_path
from .schema import apply as migrate
from .scheduler import FlipState, roi as scheduler_roi, select as scheduler_select
from .uuid7 import uuid7

DB = data_path("flips.db")


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
    source_search_ids: list[str] = field(default_factory=list)
    source_ninja_item: str = ""
    source_ninja_type: str = "DivinationCard"
    target_type: str = "query"
    target_queries: list[str] = field(default_factory=list)
    target_search_ids: list[str] = field(default_factory=list)
    target_ninja_item: str = ""
    target_ninja_type: str = "DivinationCard"
    multiplier: float = 1.0
    cost: int = 0
    enabled: bool = True
    fast: bool = True
    notes: str = ""
    uuid: str = field(default_factory=uuid7)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class Store:
    def __init__(self, db: str | Path = DB):
        self._conn = sqlite3.connect(str(db), check_same_thread=False)
        migrate(self._conn)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._backfill_uuids()

    def _backfill_uuids(self):
        rows = self._conn.execute(
            "SELECT id, data, uuid FROM flips"
        ).fetchall()
        updated = 0
        for flip_id, data_blob, uuid_col in rows:
            data = json.loads(data_blob)
            uuid_val = uuid_col or data.get("uuid")
            if not uuid_val:
                uuid_val = uuid7()
                data["uuid"] = uuid_val
                self._conn.execute(
                    "UPDATE flips SET data = ?, uuid = ? WHERE id = ?",
                    (json.dumps(data), uuid_val, flip_id),
                )
                updated += 1
            elif not uuid_col:
                self._conn.execute(
                    "UPDATE flips SET uuid = ? WHERE id = ?",
                    (uuid_val, flip_id),
                )
                updated += 1
        if updated:
            self._conn.commit()

    def _row(self, flip: Flip) -> tuple[str, str, str, str, str]:
        return (
            flip.id,
            json.dumps(
                {
                    "name": flip.name,

                    "source_type": flip.source_type,
                    "source_queries": flip.source_queries,
                    "source_search_ids": flip.source_search_ids,
                    "source_ninja_item": flip.source_ninja_item,
                    "source_ninja_type": flip.source_ninja_type,
                    "target_type": flip.target_type,
                    "target_queries": flip.target_queries,
                    "target_search_ids": flip.target_search_ids,
                    "target_ninja_item": flip.target_ninja_item,
                    "target_ninja_type": flip.target_ninja_type,
                    "multiplier": flip.multiplier,
                    "cost": flip.cost,
                    "enabled": flip.enabled,
                    "fast": flip.fast,
                    "notes": flip.notes,
                }
            ),
            str(flip.created_at),
            str(flip.updated_at),
            flip.uuid,
        )

    def _flip(self, row: tuple[str, str, str, str, str]) -> Flip:
        data = json.loads(row[1])
        return Flip(
            id=row[0],
            name=data.get("name", "Unnamed"),

            source_type=data.get("source_type", "query"),
            source_queries=data.get("source_queries") or data.get("source_urls", []),
            source_search_ids=data.get("source_search_ids", []),
            source_ninja_item=data.get("source_ninja_item", ""),
            source_ninja_type=data.get("source_ninja_type", "DivinationCard"),
            target_type=data.get("target_type", "query"),
            target_queries=data.get("target_queries") or data.get("target_urls", []),
            target_search_ids=data.get("target_search_ids", []),
            target_ninja_item=data.get("target_ninja_item", ""),
            target_ninja_type=data.get("target_ninja_type", "DivinationCard"),
            multiplier=data["multiplier"],
            cost=data.get("cost", 0),
            enabled=data.get("enabled", True),
            fast=data.get("fast", True),
            notes=data.get("notes", ""),
            uuid=row[4] or data.get("uuid", ""),
            created_at=float(row[2]),
            updated_at=float(row[3]),
        )

    def put(self, flip: Flip):
        flip.updated_at = time.time()
        self._conn.execute(
            "INSERT OR REPLACE INTO flips (id, data, created_at, updated_at, uuid) VALUES (?, ?, ?, ?, ?)",
            self._row(flip),
        )
        self._conn.commit()

    def get(self, flip_id: str) -> Flip | None:
        row = self._conn.execute(
            "SELECT id, data, created_at, updated_at, uuid FROM flips WHERE id = ?", (flip_id,)
        ).fetchone()
        return self._flip(row) if row else None

    def list(self) -> list[Flip]:
        rows = self._conn.execute(
            "SELECT id, data, created_at, updated_at, uuid FROM flips ORDER BY updated_at DESC"
        ).fetchall()
        return [self._flip(r) for r in rows]

    def delete(self, flip_id: str):
        self._conn.execute("DELETE FROM flips WHERE id = ?", (flip_id,))
        self._conn.commit()

    def recently_priced(self, limit: int = 5) -> list[dict]:
        rows = self._conn.execute(
            "SELECT id, data, updated_at, uuid FROM flips ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        out = []
        for rid, rdata, updated_at, uuid_str in rows:
            name = ""
            try:
                name = json.loads(rdata).get("name", "")
            except (ValueError, TypeError):
                pass
            item = {"id": rid, "uuid": uuid_str, "name": name, "updated_at": updated_at}
            price = self.get_price(rid)
            if price:
                item["fetched_at"] = price["fetched_at"]
                item["source_avg"] = price["source_avg"]
                item["target_avg"] = price["target_avg"]
            out.append(item)
        return out

    def set_timestamps(self, flip_id: str, created_at: float, updated_at: float):
        self._conn.execute(
            "UPDATE flips SET created_at = ?, updated_at = ? WHERE id = ?",
            (str(created_at), str(updated_at), flip_id),
        )
        self._conn.commit()

    def set_fast(self, flip_id: str, fast: bool) -> bool:
        row = self._conn.execute("SELECT data FROM flips WHERE id = ?", (flip_id,)).fetchone()
        if row is None:
            return False
        data = json.loads(row[0])
        data["fast"] = bool(fast)
        self._conn.execute(
            "UPDATE flips SET data = ? WHERE id = ?", (json.dumps(data), flip_id)
        )
        self._conn.commit()
        return True

    # ── meta (key-value settings in DB) ─────────────────────────

    def get_meta(self, key: str, default=None):
        row = self._conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set_meta(self, key: str, value) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
            (key, json.dumps(value)),
        )
        self._conn.commit()

    def disabled_qualities(self) -> set[int]:
        return {q for q in (27, 28, 29, 30) if not self.get_meta(f"flipper_quality_{q}", True)}

    # ── prices ─────────────────────────────────────────────────

    PRUNE_AFTER = 60 * 60 * 24 * 60  # 2 months in seconds

    def save_price(self, flip_id: str, source_avg: float, source_count: int, target_avg: float, target_count: int,
                   source_total: int = 0, target_total: int = 0,
                   source_chaos_avg: float = 0.0, source_chaos_count: int = 0):
        old = self._conn.execute(
            "SELECT flip_id, source_avg, source_count, target_avg, target_count, fetched_at, source_total, target_total, fetched_ms, source_chaos_avg, source_chaos_count FROM prices WHERE flip_id = ?",
            (flip_id,),
        ).fetchone()
        if old:
            self._conn.execute(
                "INSERT INTO price_history (flip_id, source_avg, source_count, target_avg, target_count, fetched_at, source_total, target_total, fetched_ms, source_chaos_avg, source_chaos_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                old,
            )
        self._conn.execute(
            "INSERT OR REPLACE INTO prices (flip_id, source_avg, source_count, target_avg, target_count, fetched_at, source_total, target_total, fetched_ms, source_chaos_avg, source_chaos_count) VALUES (?, ?, ?, ?, ?, datetime('now'), ?, ?, ?, ?, ?)",
            (flip_id, source_avg, source_count, target_avg, target_count, source_total, target_total, int(time.time() * 1000), source_chaos_avg, source_chaos_count),
        )
        self._prune_history()
        self._conn.commit()

    def get_price(self, flip_id: str) -> dict | None:
        row = self._conn.execute(
            "SELECT source_avg, source_count, target_avg, target_count, fetched_at, source_chaos_avg, source_chaos_count FROM prices WHERE flip_id = ?",
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
            "source_chaos_avg": row[5],
            "source_chaos_count": row[6],
        }

    def history(self, since_ms: int = 0) -> list[dict]:
        """All price rows (current + historical) with fetched_ms > since_ms.

        Returns a complete ordered series: the current `prices` row plus every
        `price_history` row newer than the cursor.
        """
        history = self._conn.execute(
            "SELECT flip_id, source_avg, target_avg, source_total, target_total, fetched_ms"
            " FROM price_history WHERE fetched_ms > ?",
            (since_ms,),
        ).fetchall()
        current = self._conn.execute(
            "SELECT flip_id, source_avg, target_avg, source_total, target_total, fetched_ms"
            " FROM prices WHERE fetched_ms > ?",
            (since_ms,),
        ).fetchall()
        rows = [
            {
                "flip_id": r[0],
                "source_avg": r[1],
                "target_avg": r[2],
                "source_total": r[3],
                "target_total": r[4],
                "fetched_ms": r[5],
            }
            for r in history + current
        ]
        rows.sort(key=lambda r: (r["fetched_ms"], r["flip_id"]))
        return rows

    def next_to_price(self, limit: int) -> list[str]:
        import logging
        _log = logging.getLogger(__name__)
        disabled = self.disabled_qualities()
        price_rows = {
            r[0]: r
            for r in self._conn.execute(
                "SELECT flip_id, source_avg, source_count, target_avg, target_count FROM prices"
            )
        }
        states = []
        for rid, rdata, updated_at in self._conn.execute(
            "SELECT id, data, CAST(updated_at AS REAL) FROM flips"
        ):
            data = json.loads(rdata)
            name = data.get("name", "")
            if disabled and any(f" {q} " in f" {name} " for q in disabled):
                continue
            p = price_rows.get(rid)
            if p is None:
                states.append(FlipState(id=rid, priced=False, roi=None, updated_at=updated_at))
            else:
                src, sc, tgt, tc = p[1], p[2], p[3], p[4]
                r = scheduler_roi(src, tgt, data.get("multiplier", 1.0), data.get("cost", 0)) if sc and tc else None
                states.append(FlipState(
                    id=rid, priced=True, roi=r, updated_at=updated_at,
                    fast=data.get("fast", True),
                ))
        fids = scheduler_select(states, time.time(), limit)
        if fids:
            _log.info("next_to_price: %d due", len(fids))
        return fids

    def clear_prices(self):
        import logging
        _log = logging.getLogger(__name__)
        self._conn.execute("DELETE FROM prices")
        self._conn.execute("DELETE FROM price_history")
        affected = self._conn.execute("SELECT COUNT(*) FROM flips").fetchone()[0]
        self._conn.execute("UPDATE flips SET updated_at = 0")
        self._conn.commit()
        _log.info("clear_prices: wiped prices/history, reset updated_at for %d flips", affected)

    def _prune_history(self):
        self._conn.execute(
            "DELETE FROM price_history WHERE fetched_at < datetime('now', '-60 days')"
        )
        self.prune_listings(60)

    # ── listing snapshots (target-side offer log) ──────────────

    def save_listings(self, flip_id: str, fetched_ms: int, rows: list[dict]):
        """Persist up to 10 target listings for one fetch. rows = [{rank, seller, amount, currency, indexed_ms, ilvl, rarity}]."""
        if not rows:
            return
        self._conn.executemany(
            "INSERT INTO listing_snapshots"
            " (flip_id, fetched_ms, rank, seller, amount, currency, indexed_ms, ilvl, rarity)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(flip_id, fetched_ms, r["rank"], r["seller"], r["amount"], r["currency"],
              r["indexed_ms"], r.get("ilvl"), r.get("rarity")) for r in rows],
        )
        self._conn.commit()

    def prune_listings(self, ttl_days: int = 60):
        cutoff_ms = int((time.time() - ttl_days * 86400) * 1000)
        self._conn.execute("DELETE FROM listing_snapshots WHERE fetched_ms < ?", (cutoff_ms,))
        self._conn.commit()

    def listings_since(self, since_ms: int = 0) -> list[dict]:
        """Target-side listing snapshot rows with fetched_ms > since_ms, oldest first."""
        rows = self._conn.execute(
            "SELECT flip_id, fetched_ms, rank, seller, amount, currency, indexed_ms, ilvl, rarity"
            " FROM listing_snapshots WHERE fetched_ms > ?"
            " ORDER BY fetched_ms",
            (since_ms,),
        ).fetchall()
        return [
            {
                "flip_id": r[0], "fetched_ms": r[1], "rank": r[2],
                "seller": r[3], "amount": r[4], "currency": r[5],
                "indexed_ms": r[6], "ilvl": r[7], "rarity": r[8],
            }
            for r in rows
        ]

    def db_size_bytes(self) -> int:
        """Real physical size on disk: main DB + WAL (ls -l style)."""
        total = 0
        for suffix in ("", "-wal", "-shm"):
            p = Path(str(DB) + suffix)
            if p.exists():
                total += p.stat().st_size
        return total
