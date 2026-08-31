#!/usr/bin/env bash
# RePoE + PoB data inventory pipeline. Re-runnable: download.py skips existing files.
# Usage: tools/run.sh [download|vocab|analyze|investigate|report|audit|all]
# Default: all. Cache outputs land in santa-maria/cache/, report in santa-maria/docs/.
# Exhaustive by design: schema / cross-reference / conversion scans cover 100%
# of every file; only displayed examples are sampled.
set -euo pipefail

SANTA="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLS="$SANTA/tools"
STEP="${1:-all}"

run() {
  case "$STEP" in
    all|download) echo "== download =="; python3 "$TOOLS/download.py" ;;
  esac
  case "$STEP" in
    all|vocab) echo "== vocab =="; python3 "$TOOLS/vocab.py" ;;
  esac
  case "$STEP" in
    all|analyze) echo "== analyze =="; python3 "$TOOLS/analyze.py" ;;
  esac
  case "$STEP" in
    all|investigate) echo "== investigate =="; python3 "$TOOLS/investigate.py" ;;
  esac
  case "$STEP" in
    all|report) echo "== report =="; python3 "$TOOLS/report.py" ;;
  esac
  case "$STEP" in
    all|audit) echo "== audit =="; python3 "$TOOLS/audit.py" ;;
  esac
}

run
echo "done ($STEP)"
