#!/usr/bin/env bash
# Full santa-maria pipeline runner.
#
# RePoE/PoB download -> analysis caches -> raw_records.db -> nodes.db ->
# semantic_markers.json -> edges.db -> semantic binding edges (Phase 5S) ->
# semantic candidate discovery (Phase 5D) ->
# semantic candidate validation (Phase 5V)
#
# Rerunnable by design. Re-downloading is OPTIONAL and DISABLED by default: if
# santa-maria/data/ already has downloaded files, the download step is skipped
# (existing files are never re-checked for age). The analysis step is likewise
# skipped when cache/analysis.json already exists (reused as-is).
#
# Usage: tools/run_pipeline.sh [--force-download] [--force-analysis] [--help]
#   --force-download   force the RePoE/PoB download step (re-plan + fetch missing)
#   --force-analysis   force phase1 vocab + analyze (rebuild cache/analysis.json)
#
# Each pipeline stage is a separate tool; any failure stops the run (set -e).
set -euo pipefail

SANTA="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLS="$SANTA/tools"
CACHE="$SANTA/cache"
DATA="$SANTA/data"

# prefer the repo venv python (has sqlite3); fall back to python3
PY="$(command -v python3)"
if [ -x "$SANTA/../.venv/bin/python3" ]; then
  PY="$SANTA/../.venv/bin/python3"
fi

FORCE_DOWNLOAD=0
FORCE_ANALYSIS=0
for a in "$@"; do
  case "$a" in
    --force-download) FORCE_DOWNLOAD=1 ;;
    --force-analysis) FORCE_ANALYSIS=1 ;;
    -h|--help) sed -n '1,20p' "$0"; exit 0 ;;
    *) echo "unknown argument: $a (try --help)"; exit 2 ;;
  esac
done

# ---- 1. download (optional, off by default) ----
did_download=0
if [ "$FORCE_DOWNLOAD" = 1 ]; then
  echo "== [1/9] download (forced) =="
  "$PY" "$TOOLS/phase1_download.py"
  did_download=1
elif [ -n "$(find "$DATA" -maxdepth 1 -type d | head -1)" ] \
     && [ -n "$(find "$DATA" -name '*.json' ! -name 'manifest.json' 2>/dev/null | head -1)" ]; then
  echo "== [1/9] download SKIPPED (data/ present; use --force-download to redownload) =="
else
  echo "== [1/9] download =="
  "$PY" "$TOOLS/phase1_download.py"
  did_download=1
fi

# ---- 2. phase1 vocab + analyze (needed by ingest; skip when cached) ----
needs_analysis=0
[ -f "$CACHE/analysis.json" ] || needs_analysis=1
[ "$FORCE_ANALYSIS" = 1 ] && needs_analysis=1
[ "$did_download" = 1 ] && needs_analysis=1
if [ "$needs_analysis" = 1 ]; then
  echo "== [2/9] vocab =="
  "$PY" "$TOOLS/phase1_vocab.py"
  echo "== [2/9] analyze =="
  "$PY" "$TOOLS/phase1_analyze.py"
else
  echo "== [2/9] analysis SKIPPED (cache/analysis.json present; use --force-analysis) =="
fi

# ---- 3. ingest raw snapshot ----
echo "== [3/9] ingest raw =="
"$PY" "$TOOLS/phase2_ingest_raw.py"

# ---- 4. node extraction ----
echo "== [4/9] nodes =="
"$PY" "$TOOLS/extract_nodes.py" --verify

# ---- 5. opaque-marker semantic extraction (Phase 4M) ----
echo "== [5/9] semantic markers =="
"$PY" "$TOOLS/phase4_markers_extract.py" --report

# ---- 6. edge extraction + validation ----
echo "== [6/9] edges =="
"$PY" "$TOOLS/phase5_extract_edges.py" --verify --regress --report

# ---- 7. semantic binding edges (Phase 5S, after structural edges) ----
echo "== [7/9] semantic binding =="
"$PY" "$TOOLS/phase5s_semantic_bind.py" --report

# ---- 8. semantic candidate discovery (Phase 5D, read-only over edges.db) ----
echo "== [8/9] semantic candidates =="
"$PY" "$TOOLS/phase5d_candidates.py" --report

# ---- 9. semantic candidate validation (Phase 5V, read-only) ----
echo "== [9/9] semantic validation =="
"$PY" "$TOOLS/phase5v_validate.py" --report

echo
echo "== pipeline complete =="
for db in raw_records nodes edges; do
  if [ -f "$CACHE/$db.db" ]; then
    printf "  %-12s %8s bytes\n" "$db.db" "$(stat -c%s "$CACHE/$db.db")"
  fi
done
