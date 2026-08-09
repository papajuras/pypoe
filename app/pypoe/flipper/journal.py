"""Personal flip journal — SQLite store behind the Journal tab.

Records one manual flip: definition (base + quality), cost paid, gross income
(NULL while the item is still unsold). Filling income marks it sold.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path

from pypoe.db.bases import GROUPS, QUALITIES

_DB = Path(__file__).resolve().parent.parent / "data" / "journal.db"
_LEGACY = Path(__file__).resolve().parent.parent.parent.parent / "ignore" / "flips"

_lock = threading.Lock()
_conn: sqlite3.Connection | None = None


def _connect() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _DB.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(_DB, check_same_thread=False)
        _conn.execute(
            """
            CREATE TABLE IF NOT EXISTS journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                league TEXT NOT NULL,
                base TEXT NOT NULL,
                quality INTEGER NOT NULL,
                cost REAL,
                income REAL,
                note TEXT NOT NULL DEFAULT '',
                created_at INTEGER NOT NULL,
                sold_at INTEGER
            )
            """
        )
    return _conn


def definitions() -> list[dict]:
    out = []
    for group in GROUPS:
        for base, _, _ in group["bases"]:
            for q in QUALITIES:
                out.append({"label": f"{base.lower()} {q}", "base": base, "quality": q, "group": group["name"]})
    return out


def _row(r) -> dict:
    return {
        "id": r[0],
        "league": r[1],
        "base": r[2],
        "quality": r[3],
        "cost": r[4],
        "income": r[5],
        "note": r[6],
        "created_at": r[7],
        "sold_at": r[8],
        "net": (r[5] - r[4]) if r[5] is not None else None,
    }


def list_all() -> list[dict]:
    with _lock:
        _maybe_import_legacy()
        rows = _connect().execute("SELECT * FROM journal ORDER BY id DESC").fetchall()
        return [_row(r) for r in rows]


def add(league: str, base: str, quality: int, cost: float | None, income: float | None = None, note: str = "") -> int:
    now = int(time.time())
    with _lock:
        cur = _connect().execute(
            "INSERT INTO journal (league, base, quality, cost, income, note, created_at, sold_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (league, base, quality, cost, income, note, now, now if income is not None else None),
        )
        _connect().commit()
        return cur.lastrowid or 0


_MISSING = object()


def update(rid: int, cost=_MISSING, income=_MISSING, note=_MISSING) -> bool:
    with _lock:
        conn = _connect()
        row = conn.execute("SELECT cost, income, note FROM journal WHERE id = ?", (rid,)).fetchone()
        if row is None:
            return False
        new_income = row[1] if income is _MISSING else income
        new_cost = row[0] if cost is _MISSING else cost
        new_note = row[2] if note is _MISSING else note
        sold_at = int(time.time()) if new_income is not None else None
        conn.execute(
            "UPDATE journal SET cost = ?, income = ?, note = ?, sold_at = ? WHERE id = ?",
            (new_cost, new_income, new_note, sold_at, rid),
        )
        conn.commit()
        return True


def delete(rid: int) -> bool:
    with _lock:
        cur = _connect().execute("DELETE FROM journal WHERE id = ?", (rid,))
        _connect().commit()
        return cur.rowcount > 0


def _maybe_import_legacy() -> None:
    conn = _connect()
    if conn.execute("SELECT COUNT(*) FROM journal").fetchone()[0]:
        return
    if not _LEGACY.exists():
        return
    try:
        lines = [l for l in _LEGACY.read_text().splitlines() if l.strip()]
    except OSError:
        return
    canon = {base[0].lower(): base[0] for g in GROUPS for base in g["bases"]}
    now = int(time.time())
    for line in lines:
        tokens = line.split()
        qidx = next((i for i, t in enumerate(tokens) if t.isdigit()), None)
        if qidx is None or qidx == 0:
            continue
        base = " ".join(tokens[:qidx]).strip("'")
        base = canon.get(base.lower(), base)
        quality = int(tokens[qidx])
        nums = [int(t) for t in tokens[qidx + 1:]]
        cost = -sum(n for n in nums if n < 0) or None
        income = sum(n for n in nums if n > 0) or None
        conn.execute(
            "INSERT INTO journal (league, base, quality, cost, income, note, created_at, sold_at)"
            " VALUES ('Standard', ?, ?, ?, ?, '', ?, ?)",
            (base, quality, cost, income, now, now if income is not None else None),
        )
    conn.commit()
