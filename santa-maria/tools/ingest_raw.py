#!/usr/bin/env python3
"""Phase 2 — Lossless raw SQLite snapshot of the Phase 1 download scope.

Input:  santa-maria/data/ (scope = data/manifest.json, authoritative) + Phase 1
        record semantics (analyze.classify, reused unchanged).
Output: santa-maria/cache/raw_records.db
        santa-maria/docs/phase2_raw_snapshot.md (validation report)

One raw record -> one raw_records row, using the natural top-level record
semantics established in Phase 1:
  - dict / dict-of-records / dict<scalar>: one top-level key -> one row
    (record_key = the key string, preserved verbatim).
  - list / list<string>: one top-level element -> one row (record_key = index).
  - single-record files (e.g. passive_skill_trees/Default.json,
    data-formats/*): whole file -> one row (record_key = '').
Nested structures (TradeSiteStats entries[], QueryMods mod-key/slot maps, gems
per_level, ...) are NOT split into separate rows; they stay inside the raw
record and are interpreted later during Node Extraction.

raw_json = json.dumps(parsed_record, ensure_ascii=False): semantically and
structurally lossless (complete record, no field selection/transformation),
but NOT byte-for-byte identical to the original source text (whitespace /
escaping may differ). data/ remains the authoritative byte-for-byte snapshot.

source_version is taken from data/manifest.json _meta.sources (per-repo commit
SHA; repoe@<sha> / pob@<sha>), never invented. One consistent ingested_at per
run.

Re-runnable: wipes and rebuilds raw_records / snapshot_meta (fresh
authoritative snapshot). Exactly-once guaranteed by the primary key.

Stops with a FAIL report if any validation check fails; does not proceed to
Node Extraction.
"""
import json, os, sqlite3, sys, time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import classify  # Phase 1 record semantics, reused unchanged

SANTA = Path(__file__).resolve().parents[1]
DATA = SANTA / 'data'
CACHE = SANTA / 'cache'
DOCS = SANTA / 'docs'
DB = CACHE / 'raw_records.db'
REPORT = DOCS / 'phase2_raw_snapshot.md'
META_KEY = '_meta'

SCHEMA = """
CREATE TABLE IF NOT EXISTS raw_records(
    source_file TEXT NOT NULL,
    record_key  TEXT NOT NULL,
    raw_json    TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    source_version TEXT NOT NULL,
    PRIMARY KEY (source_file, record_key)
);
CREATE TABLE IF NOT EXISTS snapshot_meta(
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


def repo_of(relpath):
    return 'repoe' if relpath.startswith('repoe/') else 'pob' if relpath.startswith('pob/') else None


def record_key(rkey):
    if rkey is None:
        return ''
    if isinstance(rkey, str):
        return rkey
    return str(rkey)


def main():
    t_start = time.time()
    manifest = json.load(open(DATA / 'manifest.json'))
    meta = manifest.get(META_KEY) or {}
    rels = sorted(r for r in manifest if r != META_KEY)
    sources = meta.get('sources') or {}
    versions = {}
    for repo, info in sources.items():
        if repo in ('repoe', 'pob') and info.get('commit'):
            versions[repo] = f"{repo}@{info['commit']}"
    if len(versions) != 2:
        print("FATAL: manifest _meta.sources lacks both repoe and pob commit SHAs")
        return 1
    ingested_at = datetime.now(timezone.utc).isoformat(timespec='seconds')

    # Phase 1 expected record counts (cross-check with analysis.json)
    analysis = json.load(open(CACHE / 'analysis.json'))
    phase1_counts = {r['relpath']: r['record_count'] for r in analysis if r.get('parse_ok')}

    CACHE.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript(SCHEMA)
    con.execute("DELETE FROM raw_records")
    con.execute("DELETE FROM snapshot_meta")

    expected_total = 0
    per_file_expected = {}
    t_ingest = time.time()
    inserted = 0
    try:
        for rel in rels:
            full = DATA / rel
            if not full.exists():
                raise RuntimeError(f"planned file missing on disk: {rel}")
            with open(full, encoding='utf-8') as f:
                data = json.load(f)
            shape, records, count, _semantics = classify(data)
            per_file_expected[rel] = count
            expected_total += count
            repo = repo_of(rel)
            version = versions[repo]
            rows = [(rel, record_key(rk), json.dumps(v, ensure_ascii=False), ingested_at, version)
                    for rk, v in records]
            con.executemany(
                "INSERT INTO raw_records(source_file, record_key, raw_json, ingested_at, source_version) "
                "VALUES (?,?,?,?,?)", rows)
            inserted += len(rows)
            if rel in phase1_counts and phase1_counts[rel] != count:
                raise RuntimeError(
                    f"record-count mismatch for {rel}: classify={count} phase1={phase1_counts[rel]}")
        con.commit()
    except Exception as e:
        con.rollback()
        print(f"FATAL during ingest: {e}")
        return 1
    t_ingest = time.time() - t_ingest

    # ---- validation ----
    issues = []

    def check(name, ok, detail=''):
        if not ok:
            issues.append((name, detail))
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ''))

    t_val = time.time()
    rows_total = con.execute("SELECT COUNT(*) FROM raw_records").fetchone()[0]
    check('raw_records row count == expected total',
          rows_total == expected_total, f"{rows_total} vs {expected_total}")

    # per-file counts + reconstruction (read back from DB)
    recon_mismatch = 0
    invalid_json = 0
    per_file_ok = True
    for rel in rels:
        full = DATA / rel
        with open(full, encoding='utf-8') as f:
            data = json.load(f)
        _shape, records, count, _sem = classify(data)
        if rows_total and rel in phase1_counts:
            pass
        n = con.execute("SELECT COUNT(*) FROM raw_records WHERE source_file=?", (rel,)).fetchone()[0]
        if n != count:
            per_file_ok = False
            issues.append(('per-file count', f"{rel}: db={n} expected={count}"))
        stored = {rk: raw for rk, raw in
                  con.execute("SELECT record_key, raw_json FROM raw_records WHERE source_file=?", (rel,))}
        for rk, v in records:
            key = record_key(rk)
            raw = stored.get(key)
            if raw is None:
                recon_mismatch += 1
                continue
            try:
                back = json.loads(raw)
            except Exception:
                invalid_json += 1
                continue
            if back != v:
                recon_mismatch += 1
    check('per-file row counts match expected', per_file_ok)
    check('every stored raw_json is valid JSON', invalid_json == 0, f"{invalid_json} invalid")
    check('stored raw_json reconstructs source record structure', recon_mismatch == 0, f"{recon_mismatch} mismatches")

    # unexpected files
    db_files = {r[0] for r in con.execute("SELECT DISTINCT source_file FROM raw_records")}
    empty_files = {rel for rel, c in per_file_expected.items() if c == 0}
    unexpected = db_files - set(rels)
    missing = (set(rels) - db_files) - empty_files
    check('no unexpected source files', not unexpected, f"{sorted(unexpected)[:5]}")
    check('every in-scope file represented (empty arrays carry no records)',
          not missing, f"{sorted(missing)[:5]}")

    # duplicates
    dups = con.execute(
        "SELECT COUNT(*) FROM (SELECT source_file, record_key, COUNT(*) c FROM raw_records "
        "GROUP BY source_file, record_key HAVING c > 1)").fetchone()[0]
    check('no duplicate records', dups == 0, f"{dups} duplicates")

    # ---- explicit spot checks ----
    def row(rel, key):
        r = con.execute("SELECT raw_json FROM raw_records WHERE source_file=? AND record_key=?",
                        (rel, key)).fetchone()
        return json.loads(r[0]) if r else None

    co = row('repoe/uniques.json', '168')
    check('Crown of Eyes (uniques key 168)',
          co and co.get('id') == 'Crown of Eyes'
          and (co.get('visual_identity') or {}).get('id') == 'UniqueHelmetInt7',
          str(co)[:80] if co else 'row missing')
    default = row('repoe/passive_skill_trees/Default.json', '')
    iw = (default or {}).get('passives', {}).get('50288')
    aof = (default or {}).get('passives', {}).get('44941')
    check('Iron Will (passives[50288])',
          iw and iw.get('name') == 'Iron Will' and iw.get('stats') == {'strong_casting': 1})
    check('Avatar of Fire (passives[44941])',
          aof and aof.get('name') == 'Avatar of Fire' and aof.get('stats') == {'keystone_avatar_of_fire': 1})
    ign = row('repoe/stats.json', 'base_chance_to_ignite_%')
    igni = row('repoe/stats.json', 'damage_+%_while_ignited')
    check('ignite vs ignited as separate stats',
          ign is not None and igni is not None and 'base_chance_to_ignite_%' != 'damage_+%_while_ignited')
    t_val = time.time() - t_val

    passed = not issues
    result = 'PASS' if passed else 'FAIL'

    # ---- report ----
    report = [
        "# Phase 2 — Raw Snapshot Validation Report",
        "",
        f"- **Database**: `cache/raw_records.db`",
        f"- **Ingested at**: `{ingested_at}`",
        f"- **Source versions**: `{versions['repoe']}` | `{versions['pob']}`",
        f"- **Source files expected**: `{len(rels)}`",
        f"- **Source records expected**: `{expected_total:,}`",
        f"- **raw_records rows inserted**: `{inserted:,}` (rows in db: `{rows_total:,}`)",
        f"- **Per-file count comparison**: {'PASS' if per_file_ok else 'FAIL'}"
        f" ({len([r for r in rels if con.execute('SELECT COUNT(*) FROM raw_records WHERE source_file=?',(r,)).fetchone()[0] == per_file_expected.get(r,-1)])}/{len(rels)} files match)",
        f"- **Duplicate records**: `{dups}`",
        f"- **Invalid raw_json**: `{invalid_json}`",
        f"- **Reconstruction mismatches**: `{recon_mismatch}`",
        f"- **Unexpected source files**: `{len(unexpected)}`",
        f"- **Missing source files**: `{len(missing)}`",
        f"- **Files with zero records (empty arrays, no rows by design)**: "
        f"{', '.join('`' + f + '`' for f in sorted(empty_files)) or 'none'}",
        f"- **Spot checks**: Crown of Eyes / Iron Will / Avatar of Fire / ignite-vs-ignited — "
        f"see check list above",
        f"- **Ingest time**: `{t_ingest:.1f}s` | **Validation time**: `{t_val:.1f}s` | "
        f"**Total**: `{time.time() - t_start:.1f}s`",
        f"- **Result**: **{result}**",
        "",
    ]
    if issues:
        report.append("### Failed checks")
        for name, detail in issues:
            report.append(f"- `{name}`: {detail}")
    DOCS.mkdir(parents=True, exist_ok=True)
    with open(REPORT, 'w') as f:
        f.write('\n'.join(report))

    # snapshot_meta
    con.execute("INSERT OR REPLACE INTO snapshot_meta VALUES ('ingested_at', ?)", (ingested_at,))
    con.execute("INSERT OR REPLACE INTO snapshot_meta VALUES ('source_version_repoe', ?)", (versions['repoe'],))
    con.execute("INSERT OR REPLACE INTO snapshot_meta VALUES ('source_version_pob', ?)", (versions['pob'],))
    con.execute("INSERT OR REPLACE INTO snapshot_meta VALUES ('expected_records', ?)", (str(expected_total),))
    con.execute("INSERT OR REPLACE INTO snapshot_meta VALUES ('inserted_records', ?)", (str(inserted),))
    con.execute("INSERT OR REPLACE INTO snapshot_meta VALUES ('result', ?)", (result,))
    con.commit()
    con.close()

    print(f"\nreport: {REPORT}")
    print(f"ingest {t_ingest:.1f}s | validation {t_val:.1f}s | total {time.time() - t_start:.1f}s")
    print(f"RESULT: {result}")
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
