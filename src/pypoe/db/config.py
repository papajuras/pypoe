import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent.parent / "db" / "crafting.json"

DEFAULT_SETTINGS = {
    "prefixes": [],
    "suffixes": [],
    "item_type": "Ring",
    "cluster_implicit_type": "",
    "use_regal": False,
    "exalt_after_regal": False,
}


def _ensure_wildcard(entries: list[str]) -> list[str]:
    return entries if entries else [" "]


def load() -> dict[str, dict]:
    if not CONFIG_PATH.exists():
        return {}
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save(data: dict[str, dict]) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)


def _migrate(profile_config: dict) -> dict:
    profile_config.pop("count_to_regal", None)
    profile_config.pop("both_required", None)
    profile_config.pop("use_exalt", None)
    profile_config.pop("count_to_exalt", None)
    return profile_config


def get_meta(key: str, default=None):
    return load().get(f"_{key}", default)


def set_meta(key: str, value) -> None:
    stored = load()
    stored[f"_{key}"] = value
    save(stored)


def get_profile_settings(profile_name: str) -> dict:
    stored = load()
    profile_config = _migrate(stored.get(profile_name, {}))
    merged = {**DEFAULT_SETTINGS, **profile_config}
    merged["prefixes"] = _ensure_wildcard(merged["prefixes"])
    merged["suffixes"] = _ensure_wildcard(merged["suffixes"])
    return merged


def put_profile_settings(profile_name: str, settings: dict) -> None:
    stored = load()
    stored[profile_name] = {k: v for k, v in settings.items() if k in DEFAULT_SETTINGS}
    stored[profile_name]["prefixes"] = _ensure_wildcard(stored[profile_name].get("prefixes", []))
    stored[profile_name]["suffixes"] = _ensure_wildcard(stored[profile_name].get("suffixes", []))
    save(stored)


def delete_profile(profile_name: str) -> None:
    stored = load()
    stored.pop(profile_name, None)
    save(stored)


def list_profile_names() -> list[str]:
    return [k for k in load().keys() if not k.startswith("_")]
