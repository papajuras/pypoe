import json
from pathlib import Path

_PATH = Path(__file__).resolve().parent.parent.parent / "pypoe.json"


def read_league() -> str:
    return json.loads(_PATH.read_text()).get("league", "Standard")
