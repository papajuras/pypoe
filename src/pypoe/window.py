"""Lightweight subprocess that opens a webview window for the NiceGUI server."""

import logging
import socket
import time
from pathlib import Path

import webview as wv

_log = logging.getLogger("tray.window")
_log.setLevel(logging.DEBUG)
Path("log").mkdir(exist_ok=True)
_h = logging.FileHandler("log/tray.log", mode="a")
_h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
_log.addHandler(_h)


def open_window(port: int):
    _log.info("open_window started, waiting for port %d", port)
    while True:
        try:
            s = socket.socket()
            s.settimeout(1)
            s.connect(("127.0.0.1", port))
            s.close()
            _log.info("server ready on port %d", port)
            break
        except OSError:
            pass
        time.sleep(0.5)
    _log.info("creating webview window")
    win = wv.create_window("PoE Crafting Macro", f"http://127.0.0.1:{port}", width=1200, height=800)
    win.events.closed += win.destroy
    _log.info("starting webview")
    wv.start()
    _log.info("webview exited")
