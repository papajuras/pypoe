import logging
import time
from pathlib import Path

import pyautogui
import pyperclip
from pynput import keyboard

logger = logging.getLogger(__name__)

_LOG_FILE = Path(__file__).resolve().parents[3] / "log" / "automation.log"


def file_logger() -> logging.Logger:
    """File-only logger for automation diagnostics (never the console)."""
    log = logging.getLogger("pypoe.automation")
    if not log.handlers:
        log.setLevel(logging.INFO)
        log.propagate = False
        _LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        h = logging.FileHandler(_LOG_FILE)
        h.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s"))
        log.addHandler(h)
    return log


def move_to(target_position: list[int]) -> None:
    _log = file_logger()
    _log.info("move_to target=%s", target_position)
    x, y = pyautogui.position()
    tx, ty = target_position
    dx = tx - x
    dy = ty - y
    pyautogui.moveRel(dx, dy, duration=0.1)
    _log.info("move_to done at %s", pyautogui.position())


def click_orb(orb_position: list[int], item_position: list[int]) -> None:
    move_to(orb_position)
    time.sleep(0.15)
    pyautogui.click(button="right")
    time.sleep(0.15)
    move_to(item_position)
    pyautogui.click()
    time.sleep(0.15)


def use_alt(alt_position: list[int], item_position: list[int]) -> None:
    click_orb(alt_position, item_position)


def use_aug(aug_position: list[int], item_position: list[int]) -> None:
    move_to(aug_position)
    time.sleep(0.05)
    pyautogui.click(button="right")
    time.sleep(0.05)
    move_to(item_position)
    time.sleep(0.05)
    pyautogui.click()
    time.sleep(0.05)


def use_regal(regal_position: list[int], item_position: list[int]) -> None:
    click_orb(regal_position, item_position)


def use_exalt(exalt_position: list[int], item_position: list[int]) -> None:
    click_orb(exalt_position, item_position)


def use_scour(scour_position: list[int], item_position: list[int]) -> None:
    click_orb(scour_position, item_position)


def use_transmute(transmute_position: list[int], item_position: list[int]) -> None:
    click_orb(transmute_position, item_position)


def delete_beast(delete_position: list[int]) -> None:
    logger.info("delete_beast -> %s (mouse at %s)", delete_position, pyautogui.position())
    try:
        move_to(delete_position)
        time.sleep(0.15)
        kbd = keyboard.Controller()
        kbd.press(keyboard.Key.ctrl)
        time.sleep(0.15)
        pyautogui.click(button="left")
        time.sleep(0.15)
        pyautogui.click(button="left")
        time.sleep(0.15)
        kbd.release(keyboard.Key.ctrl)
    except Exception:
        logger.exception("delete_beast crashed")
        raise


def capture_clipboard() -> str:
    kbd = keyboard.Controller()
    kbd.press(keyboard.Key.ctrl)
    time.sleep(0.05)
    kbd.press(keyboard.Key.alt)
    time.sleep(0.05)
    kbd.press("c")
    time.sleep(0.2)
    kbd.release("c")
    kbd.release(keyboard.Key.alt)
    kbd.release(keyboard.Key.ctrl)
    return pyperclip.paste().lower()
