"""HTTP client for the remote data gatherer."""

from __future__ import annotations

import requests


class GathererClient:
    def __init__(self, base_url: str):
        self._base = base_url.rstrip("/")

    def list_flips(self, since: float = 0.0) -> dict:
        resp = requests.get(f"{self._base}/api/flips", params={"since": since}, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def status(self) -> dict:
        resp = requests.get(f"{self._base}/api/status", timeout=10)
        resp.raise_for_status()
        return resp.json()

    def league(self) -> dict:
        resp = requests.get(f"{self._base}/api/league", timeout=10)
        resp.raise_for_status()
        return resp.json()

    def refresh(self, flip_id: str) -> dict:
        resp = requests.post(f"{self._base}/api/flips/{flip_id}/refresh", timeout=15)
        resp.raise_for_status()
        return resp.json()

    def set_fast(self, flip_id: str, fast: bool) -> dict:
        resp = requests.post(f"{self._base}/api/flips/{flip_id}/fast", json={"fast": fast}, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def delete(self, flip_id: str) -> dict:
        resp = requests.delete(f"{self._base}/api/flips/{flip_id}", timeout=15)
        resp.raise_for_status()
        return resp.json()

    def seed(self, flips: list[dict]) -> dict:
        resp = requests.post(f"{self._base}/api/flips", json={"flips": flips}, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_settings(self) -> dict:
        resp = requests.get(f"{self._base}/api/settings", timeout=10)
        resp.raise_for_status()
        return resp.json()

    def put_settings(self, settings: dict) -> dict:
        resp = requests.put(f"{self._base}/api/settings", json=settings, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def history(self, since_ms: int = 0) -> dict:
        resp = requests.get(f"{self._base}/api/history", params={"since": since_ms}, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def listings(self, since_ms: int = 0) -> dict:
        resp = requests.get(f"{self._base}/api/listings", params={"since": since_ms}, timeout=30)
        resp.raise_for_status()
        return resp.json()
