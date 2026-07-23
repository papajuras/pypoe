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
