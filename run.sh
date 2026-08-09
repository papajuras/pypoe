#!/bin/bash
cd "$(dirname "$0")"

pkill -f "app/main.py" 2>/dev/null || true
sleep 1

# NEVER start the gatherer locally — it runs on the Pi (see AGENTS.md).
# The app connects to it via the URL in app/pypoe/config.json.
PYTHONPATH=app .venv/bin/python3 app/main.py "$@" &
MAIN_PID=$!

cleanup() {
    kill "$MAIN_PID" 2>/dev/null
}
trap cleanup EXIT INT TERM

wait
