"""Gatherer config — league + quality flags.

league comes from config.json (ships with the module, overwritten on deploy).
Quality flags live in the flips.db meta table (set via GET/PUT /api/settings).
"""

from __future__ import annotations

import json
from pathlib import Path

_CONFIG = Path(__file__).resolve().parent / "config.json"
DATA_DIR = Path(__file__).resolve().parent / "data"


def read_league() -> str:
    try:
        return json.loads(_CONFIG.read_text()).get("league", "Standard")
    except (OSError, json.JSONDecodeError):
        return "Standard"


def data_path(name: str) -> Path:
    return DATA_DIR / name
