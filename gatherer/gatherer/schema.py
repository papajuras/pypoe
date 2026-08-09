SCHEMA = {
    1: [
        "CREATE TABLE IF NOT EXISTS flips (id TEXT PRIMARY KEY, data TEXT, created_at TEXT, updated_at TEXT)",
    ],
    2: [
        "CREATE TABLE IF NOT EXISTS prices (flip_id TEXT PRIMARY KEY, source_avg REAL, source_count INTEGER, target_avg REAL, target_count INTEGER, fetched_at TEXT)",
        "CREATE TABLE IF NOT EXISTS price_history (id INTEGER PRIMARY KEY AUTOINCREMENT, flip_id TEXT, source_avg REAL, source_count INTEGER, target_avg REAL, target_count INTEGER, fetched_at TEXT)",
        "CREATE INDEX IF NOT EXISTS idx_flips_updated ON flips(updated_at)",
        "CREATE INDEX IF NOT EXISTS idx_price_history_flip ON price_history(flip_id)",
        "CREATE INDEX IF NOT EXISTS idx_price_history_time ON price_history(fetched_at)",
    ],
    3: [
        "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)",
    ],
    4: [
        "ALTER TABLE flips ADD COLUMN uuid TEXT",
    ],
    5: [
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_flips_uuid ON flips(uuid)",
    ],
    6: [
        "ALTER TABLE prices ADD COLUMN source_total INTEGER DEFAULT 0",
        "ALTER TABLE prices ADD COLUMN target_total INTEGER DEFAULT 0",
        "ALTER TABLE prices ADD COLUMN fetched_ms INTEGER DEFAULT 0",
        "ALTER TABLE price_history ADD COLUMN source_total INTEGER DEFAULT 0",
        "ALTER TABLE price_history ADD COLUMN target_total INTEGER DEFAULT 0",
        "ALTER TABLE price_history ADD COLUMN fetched_ms INTEGER DEFAULT 0",
        "UPDATE prices SET fetched_ms = CAST(strftime('%s', fetched_at) AS INTEGER) * 1000",
        "UPDATE price_history SET fetched_ms = CAST(strftime('%s', fetched_at) AS INTEGER) * 1000",
        "CREATE INDEX IF NOT EXISTS idx_price_history_ms ON price_history(fetched_ms)",
    ],
    7: [
        "CREATE TABLE IF NOT EXISTS listing_snapshots ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "flip_id TEXT NOT NULL,"
        "fetched_ms INTEGER NOT NULL,"
        "rank INTEGER NOT NULL,"
        "seller TEXT NOT NULL,"
        "amount REAL NOT NULL,"
        "currency TEXT NOT NULL,"
        "indexed_ms INTEGER NOT NULL,"
        "ilvl INTEGER,"
        "rarity TEXT)",
        "CREATE INDEX IF NOT EXISTS idx_listings_flip ON listing_snapshots(flip_id, fetched_ms)",
        "CREATE INDEX IF NOT EXISTS idx_listings_ms ON listing_snapshots(fetched_ms)",
    ],
    8: [
        "ALTER TABLE prices ADD COLUMN source_chaos_avg REAL DEFAULT 0",
        "ALTER TABLE prices ADD COLUMN source_chaos_count INTEGER DEFAULT 0",
        "ALTER TABLE price_history ADD COLUMN source_chaos_avg REAL DEFAULT 0",
        "ALTER TABLE price_history ADD COLUMN source_chaos_count INTEGER DEFAULT 0",
    ],
}


def apply(conn):
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY, applied_at TEXT)"
    )
    current = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] or 0
    for version, stmts in sorted(SCHEMA.items()):
        if version > current:
            for stmt in stmts:
                conn.execute(stmt)
            conn.execute(
                "INSERT INTO schema_version (version, applied_at) VALUES (?, datetime('now'))",
                (version,),
            )
    conn.commit()
