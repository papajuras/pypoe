"""App config — local BFF/UI settings, stored in app/pypoe/config.json."""

from __future__ import annotations

import json
from pathlib import Path

_PATH = Path(__file__).resolve().parent / "config.json"


def _read() -> dict:
    try:
        return json.loads(_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def _write(data: dict) -> None:
    _PATH.write_text(json.dumps(data, indent=2))


def read_gatherer_url() -> str:
    return _read().get("gatherer", "http://127.0.0.1:23467")


def read_screen_mode() -> str:
    return str(_read().get("screen_mode", "3 screens"))


def set_screen_mode(mode: str) -> None:
    data = _read()
    data["screen_mode"] = mode
    _write(data)


def read_selected() -> str:
    return str(_read().get("selected", ""))


def set_selected(name: str) -> None:
    data = _read()
    data["selected"] = name
    _write(data)
