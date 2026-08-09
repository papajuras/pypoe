"""Divination card -> reward mapping from poedb, cached to disk.

poe.ninja's exchange overview gives card prices but not what each card
produces. poedb.tw/us/Divination_Cards lists every card with its stack size and
reward on one page. Fetched once, parsed, cached to
app/pypoe/data/cache/div_cards.json (gitignored data dir).
"""

from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path

import requests

URL = "https://poedb.tw/us/Divination_Cards"
CACHE = Path(__file__).resolve().parent.parent / "pypoe" / "data" / "cache" / "div_cards.json"
UA = {"User-Agent": "pypoe/0.1.0 (div-card scanner; one-time data fetch)"}

# Each card is a block: <div class="col"><div class="d-flex border-top rounded">
# containing the icon link, the name link
#   <a class="divination DivinationCard" ... href="The_Doctor">The Doctor</a>
# then <div><div class="property">Stack Size: <span class='colourDefault'>1 / 8</span>
# ... <div class="explicitMod"><span class="uniqueitem">Headhunter</span></div>
_CARD = re.compile(
    r'<a class="divination DivinationCard"[^>]*href="([A-Za-z0-9_-]+)">([^<]+)</a>', re.S)
_STACK = re.compile(r"Stack Size:\s*<span[^>]*>\s*(\d+)\s*/\s*(\d+)")
_EXPLICIT = re.compile(r'<div class="explicitMod">(.*?)</div>', re.S)


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def fetch(refresh: bool = False) -> dict[str, dict]:
    """Return {card_name: {stack, reward, corrupted}}. Cache-first."""
    if not refresh and CACHE.exists():
        return json.loads(CACHE.read_text())

    resp = requests.get(URL, headers=UA, timeout=60)
    resp.raise_for_status()
    html = resp.text

    cards: dict[str, dict] = {}
    for chunk in html.split('<div class="col"><div class="d-flex border-top rounded">')[1:]:
        m = _CARD.search(chunk)
        if not m:
            continue
        name = _clean(m.group(2))
        stack_m = _STACK.search(chunk)
        if not stack_m:
            continue
        stack = int(stack_m.group(2))
        exp = _EXPLICIT.search(chunk)
        reward = _clean(exp.group(1)) if exp else ""
        if not name or not stack or not reward:
            continue
        corrupted = "corrupted" in reward.lower()
        cards[name] = {"stack": stack, "reward": reward, "corrupted": corrupted}

    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cards, indent=2))
    print(f"cached {len(cards)} cards -> {CACHE}")
    return cards
