"""Minimal static file server for the Vue 3 SPA."""

from __future__ import annotations

import logging
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

logger = logging.getLogger(__name__)

_STATIC_DIR = Path(__file__).resolve().parent / "static"


def start_static(port: int = 8766) -> None:
    _STATIC_DIR.mkdir(parents=True, exist_ok=True)
    handler = lambda *args, **kw: SimpleHTTPRequestHandler(*args, directory=str(_STATIC_DIR), **kw)
    server = HTTPServer(("127.0.0.1", port), handler)
    logger.info("Static server on http://127.0.0.1:%d", port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
