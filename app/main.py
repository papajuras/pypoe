import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import os
import signal
import threading
import time

import logging
_log = logging.getLogger(__name__)

import ctypes
ctypes.CDLL("libX11.so.6").XInitThreads()

import pyautogui
from pynput import keyboard

from pypoe.crafting import controller
from pypoe.db.affixes import download as download_affixes, is_cached
from pypoe.flipper import start_api, start_static

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05

pressed_keys: set[str] = set()

if not is_cached():
    download_affixes(force=True)


def on_press(key):
    try:
        if key == keyboard.Key.esc:
            controller.stop()
        elif key.char:
            pressed_keys.add(key.char.lower())
    except AttributeError:
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            pressed_keys.add("ctrl")
        elif key == keyboard.Key.esc:
            controller.stop()
    if "ctrl" in pressed_keys and "j" in pressed_keys:
        controller.start()
    elif "ctrl" in pressed_keys and "k" in pressed_keys:
        x, y = pyautogui.position()
        _log.info("Mouse: %d, %d", x, y)
    elif "ctrl" in pressed_keys and "l" in pressed_keys:
        _log.info("Deleting beasts...")
        controller.delete_beasts()


def on_release(key):
    try:
        if key.char:
            pressed_keys.discard(key.char.lower())
    except AttributeError:
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            pressed_keys.discard("ctrl")


def main():
    signal.signal(signal.SIGINT, lambda *_: os._exit(0))

    Path("log").mkdir(exist_ok=True)
    _fh = logging.FileHandler("log/app.log")
    _fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[_fh])

    threading.Thread(target=start_api, kwargs={"port": 8765}, daemon=True).start()
    threading.Thread(target=start_static, kwargs={"port": 8766}, daemon=True).start()

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.daemon = True
    listener.start()

    _log.info("BFF: http://127.0.0.1:8765")
    _log.info("FE:  http://127.0.0.1:8766")
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
