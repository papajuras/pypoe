import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import re
import os
import threading

import pyautogui
from nicegui import ui
from pynput import keyboard

from pypoe.crafting import CraftingSession, Positions, Settings, capture_clipboard
from pypoe.db.affixes import (
    download as download_affixes,
    get_item_type_names,
    is_cached,
    load_affixes,
)
from pypoe.db.config import (
    delete_profile,
    get_meta,
    get_profile_settings,
    list_profile_names,
    put_profile_settings,
    set_meta,
)
from pypoe.flipper.ui import FlipperPanel
from pypoe.tray import create as create_tray, stop as stop_tray, update_tooltip

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05

import ctypes
ctypes.CDLL("libX11.so.6").XInitThreads()

POSITIONS_3SCREENS = Positions(
    alt=[2073, 386],
    item=[2352, 620],
    aug=[2213, 453],
    regal=[2486, 368],
    exalt=[2306, 381],
    scour=[2489, 551],
    transmute=[1986, 381],
    delete_beasts=[2033, 340],
)

POSITIONS_2SCREENS = Positions(
    alt=[2071, 289],
    item=[2263, 477],
    aug=[2176, 346],
    regal=[2378, 287],
    exalt=[2249, 291],
    scour=[2385, 415],
    transmute=[2016, 279],
    delete_beasts=[2044, 258],
)

SCREEN_MODES = {"3 screens": POSITIONS_3SCREENS, "2 screens": POSITIONS_2SCREENS}
screen_mode = get_meta("screen_mode", "3 screens")
positions = SCREEN_MODES[screen_mode]
session: CraftingSession | None = None
pressed_keys = set()

if is_cached():
    download_affixes()
else:
    download_affixes(force=True)
profile_names = list_profile_names()
if not profile_names:
    put_profile_settings("Default", {})
    profile_names = list_profile_names()
last = get_meta("selected")
profile_name = last if last in profile_names else profile_names[0]


def _load_profile(name: str) -> dict:
    return get_profile_settings(name)


cfg = _load_profile(profile_name)
settings = Settings(
    use_regal=cfg["use_regal"],
    exalt_after_regal=cfg["exalt_after_regal"],
)
item_type = cfg.get("item_type", "Ring")
selected_prefixes: list[str] = []
selected_suffixes: list[str] = []
prefix_entries: dict[str, dict] = {}
suffix_entries: dict[str, dict] = {}
all_prefixes: list[dict] = []
all_suffixes: list[dict] = []


def _refresh_profile_list():
    profile_select.options = list_profile_names()


def _sort_key(a: dict) -> int:
    nums = re.findall(r"\d+", " ".join(a["stats"]))
    return -(max(int(n) for n in nums)) if nums else 0


def _sort_affixes(affixes: list[dict]) -> list[dict]:
    return sorted(affixes, key=_sort_key)


def _fmt(name: str, game_text: str, influence: str | None = None) -> str:
    tag = f"[{influence}] " if influence else ""
    return f"{tag}{name} — {game_text}" if game_text else f"{tag}{name}"


def _build_options(affixes: list[dict]) -> dict[str, str]:
    return {a["mod_id"]: _fmt(a["name"], a.get("game_text", ""), a.get("influence")) for a in affixes}


def _chip_label(mid: str, entries: dict[str, dict]) -> str:
    e = entries.get(mid)
    if not e:
        return mid
    return e.get("game_text", "") if e.get("influence") else e["name"]


def _save_text(mid: str, entries: dict[str, dict]) -> str:
    e = entries.get(mid)
    if not e:
        return mid
    return e.get("search_text", e.get("game_text", "")) if e.get("influence") else e["name"]


def _reload_affixes(it: str) -> None:
    global all_prefixes, all_suffixes, prefix_entries, suffix_entries
    all_prefixes, all_suffixes = load_affixes(it)
    prefix_entries = {a["mod_id"]: a for a in all_prefixes}
    suffix_entries = {a["mod_id"]: a for a in all_suffixes}


def _rebuild_selected_chips() -> None:
    sel_p_container.clear()
    with sel_p_container:
        for mid in selected_prefixes:
            ui.chip(_chip_label(mid, prefix_entries), icon="filter_alt").props("removable").on("click:remove",
                lambda mid=mid: _remove_selected("prefix", mid))
    sel_s_container.clear()
    with sel_s_container:
        for mid in selected_suffixes:
            ui.chip(_chip_label(mid, suffix_entries), icon="filter_alt").props("removable").on("click:remove",
                lambda mid=mid: _remove_selected("suffix", mid))


def _remove_selected(side: str, mid: str) -> None:
    if side == "prefix":
        selected_prefixes.remove(mid)
        prefix_select.value = selected_prefixes[:]
    else:
        selected_suffixes.remove(mid)
        suffix_select.value = selected_suffixes[:]
    _rebuild_selected_chips()
    _save_current_settings()


def _save_current_settings() -> None:
    put_profile_settings(profile_name, {
        "prefixes": [_save_text(mid, prefix_entries) for mid in selected_prefixes],
        "suffixes": [_save_text(mid, suffix_entries) for mid in selected_suffixes],
        "item_type": item_type,
        "use_regal": settings.use_regal,
        "exalt_after_regal": settings.exalt_after_regal,
    })


def _set_screen_mode(mode: str):
    global positions, screen_mode
    screen_mode = mode
    positions = SCREEN_MODES[mode]
    set_meta("screen_mode", mode)


def _change_item_type(it: str) -> None:
    global item_type
    item_type = it
    _reload_affixes(it)
    prefix_select.options = _build_options(_sort_affixes(all_prefixes))
    suffix_select.options = _build_options(_sort_affixes(all_suffixes))
    prefix_select.value = []
    suffix_select.value = []
    selected_prefixes.clear()
    selected_suffixes.clear()
    prefix_select.update()
    suffix_select.update()
    _rebuild_selected_chips()
    _save_current_settings()


def _on_side_select(side: str, values: list[str]) -> None:
    if side == "prefix":
        selected_prefixes.clear()
        selected_prefixes.extend(values or [])
    else:
        selected_suffixes.clear()
        selected_suffixes.extend(values or [])
    _rebuild_selected_chips()
    _save_current_settings()


def _start_spam():
    global session
    status_label.set_text("Spamming... ESC to stop")
    session = CraftingSession(
        prefixes=[_save_text(mid, prefix_entries) for mid in selected_prefixes] or [" "],
        suffixes=[_save_text(mid, suffix_entries) for mid in selected_suffixes] or [" "],
        positions=positions,
        settings=settings,
    )
    threading.Thread(target=session.run, daemon=True).start()


def on_press(key):
    global session

    try:
        if key == keyboard.Key.esc:
            if session:
                session.stop()
        elif key.char:
            pressed_keys.add(key.char.lower())
    except AttributeError:
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            pressed_keys.add("ctrl")
        elif key == keyboard.Key.esc:
            if session:
                session.stop()

    if "ctrl" in pressed_keys and "j" in pressed_keys:
        _start_spam()

    elif "ctrl" in pressed_keys and "k" in pressed_keys:
        x, y = pyautogui.position()
        status_label.set_text(f"Mouse: {x}, {y}")
        clp = capture_clipboard()
        print(clp)

    elif "ctrl" in pressed_keys and "l" in pressed_keys:
        status_label.set_text("Deleting beasts...")
        session = CraftingSession(prefixes=[" "], suffixes=[" "], positions=positions)
        threading.Thread(target=session.delete_beasts_loop, daemon=True).start()


def on_release(key):
    try:
        if key.char:
            pressed_keys.discard(key.char.lower())
    except AttributeError:
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            pressed_keys.discard("ctrl")


def update_profile(name_or_event):
    global item_type, profile_name, settings, selected_prefixes, selected_suffixes
    name = name_or_event.value if hasattr(name_or_event, "value") else name_or_event
    profile_name = name
    set_meta("selected", name)
    cfg = _load_profile(name)
    item_type = cfg.get("item_type", "Ring")
    settings.use_regal = cfg["use_regal"]
    settings.exalt_after_regal = cfg["exalt_after_regal"]
    regal_switch.value = settings.use_regal
    exalt_switch.value = settings.exalt_after_regal

    _reload_affixes(item_type)
    selected_prefixes = []
    selected_suffixes = []
    for p in cfg.get("prefixes", []):
        for a in all_prefixes:
            if _save_text(a["mod_id"], prefix_entries) == p or a["name"] == p:
                selected_prefixes.append(a["mod_id"])
                break
    for s in cfg.get("suffixes", []):
        for a in all_suffixes:
            if _save_text(a["mod_id"], suffix_entries) == s or a["name"] == s:
                selected_suffixes.append(a["mod_id"])
                break
    prefix_select.options = _build_options(_sort_affixes(all_prefixes))
    suffix_select.options = _build_options(_sort_affixes(all_suffixes))
    prefix_select.value = selected_prefixes[:]
    suffix_select.value = selected_suffixes[:]
    item_type_select.value = item_type
    _rebuild_selected_chips()


def save_orb_settings():
    settings.use_regal = regal_switch.value
    settings.exalt_after_regal = exalt_switch.value
    _save_current_settings()


def start():
    update_profile(profile_select.value)
    _start_spam()
    stop_btn.props(remove="disable")
    status_label.classes("text-positive")


def stop():
    global session
    if session:
        session.stop()
    status_label.set_text("Stopped")
    status_label.classes("text-negative")


def show_delete_confirmation():
    with ui.dialog() as dialog, ui.card():
        ui.label(f"Delete '{profile_name}'?").classes("text-h6")
        ui.label("This cannot be undone.").classes("text-caption text-grey-6")
        with ui.row().classes("gap-2 mt-2"):
            ui.button("Delete", on_click=lambda: _delete_profile(dialog)).props("unelevated color=negative")
            ui.button("Cancel", on_click=dialog.close).props("flat")
    dialog.open()


def _delete_profile(dialog):
    global profile_name
    delete_profile(profile_name)
    _refresh_profile_list()
    remaining = list_profile_names()
    if remaining:
        profile_name = remaining[0]
    profile_select.value = profile_name
    update_profile(profile_name)
    dialog.close()


def show_builder():
    with ui.dialog() as dialog, ui.card():
        ui.label("New profile").classes("text-h6")
        name_input = ui.input("Profile name").classes("w-64")
        type_select = ui.select(get_item_type_names(), value="Ring", label="Item type")
        with ui.row().classes("gap-2 mt-2"):
            ui.button("Create", on_click=lambda: _create_profile(name_input.value, type_select.value, dialog)).props("unelevated color=positive")
            ui.button("Cancel", on_click=dialog.close).props("flat")
    dialog.open()


def _create_profile(name: str, it: str, dialog):
    name = name.strip()
    if not name:
        return
    put_profile_settings(name, {"item_type": it})
    _refresh_profile_list()
    profile_select.value = name
    update_profile(name)
    dialog.close()


def _show_debug():
    prefixes = [_save_text(mid, prefix_entries) for mid in selected_prefixes] or [" "]
    suffixes = [_save_text(mid, suffix_entries) for mid in selected_suffixes] or [" "]
    debug_label.set_text(
        f"prefixes: {prefixes}\n"
        f"suffixes: {suffixes}"
    )


ui.dark_mode().enable()


_reload_affixes(item_type)

with ui.row().classes("w-full h-screen max-w-7xl mx-auto gap-4 p-4"):
    with ui.card().classes("w-[49%] p-4 overflow-y-auto"):
        with ui.column().classes("gap-5"):
            ui.label("PoE Crafting Macro").classes("text-h5 text-weight-bold")

            with ui.row().classes("items-center gap-4"):
                ui.label("Profile:").classes("text-weight-medium")
                with ui.row().classes("items-center gap-2"):
                    profile_select = ui.select(
                        profile_names,
                        value=profile_name,
                        on_change=update_profile,
                    ).classes("min-w-[200px]")
                    ui.button(icon="delete", on_click=show_delete_confirmation).props("flat dense")
                    ui.button(icon="auto_awesome", on_click=show_builder).props("flat dense")
                ui.label("").classes("flex-1")
                ui.label("Screens:").classes("text-weight-medium")
                ui.select(
                    list(SCREEN_MODES.keys()),
                    value=screen_mode,
                    on_change=lambda e: _set_screen_mode(e.value),
                ).classes("min-w-[120px]")

            with ui.card().classes("w-full p-4 border border-grey-6"):
                ui.label("Orb behaviour (saved instantly)").classes("text-weight-medium text-caption text-grey-5")
                with ui.column().classes("gap-3 mt-2"):
                    with ui.row().classes("items-center gap-4"):
                        regal_switch = ui.switch("Regal", value=settings.use_regal, on_change=save_orb_settings)
                        exalt_switch = ui.switch("Exalt on failed regal", value=settings.exalt_after_regal, on_change=save_orb_settings)

            with ui.row().classes("items-center gap-4 w-full"):
                ui.label("Item type:").classes("text-weight-medium")
                item_type_select = ui.select(
                    get_item_type_names(),
                    value=item_type,
                    on_change=lambda e: _change_item_type(e.value),
                ).classes("min-w-[180px]")

            with ui.row().classes("gap-4 w-full"):
                with ui.card().classes("flex-1 p-3 overflow-hidden"):
                    ui.label("Prefixes").classes("text-weight-medium text-caption text-grey-5")
                    prefix_select = ui.select(
                        label="Search...",
                        options=_build_options(_sort_affixes(all_prefixes)),
                        multiple=True,
                        with_input=True,
                        on_change=lambda e: _on_side_select("prefix", e.value),
                    ).classes("w-full").props('hide-selected')

                with ui.card().classes("flex-1 p-3 overflow-hidden"):
                    ui.label("Suffixes").classes("text-weight-medium text-caption text-grey-5")
                    suffix_select = ui.select(
                        label="Search...",
                        options=_build_options(_sort_affixes(all_suffixes)),
                        multiple=True,
                        with_input=True,
                        on_change=lambda e: _on_side_select("suffix", e.value),
                    ).classes("w-full").props('hide-selected')

            with ui.card().classes("w-full p-2"):
                ui.label("Selected:").classes("text-caption text-grey-5")
                with ui.row().classes("gap-2 w-full"):
                    sel_p_container = ui.column().classes("gap-1 flex-1")
                    sel_s_container = ui.column().classes("gap-1 flex-1")

            with ui.row().classes("gap-4"):
                start_btn = ui.button("Start", icon="play_arrow", on_click=start).props("unelevated color=positive")
                stop_btn = ui.button("Stop", icon="stop", on_click=stop).props("unelevated color=negative disable")

            status_label = ui.label(f"Ready — {screen_mode}").classes("text-caption")

            ui.separator()
            with ui.row().classes("items-center gap-4"):
                with ui.column().classes("text-caption text-grey-7 gap-1"):
                    ui.label("ESC → Stop spamming")
                    ui.label("Ctrl + K → Inspect item under mouse")
                    ui.label("Ctrl + L → Delete beasts")
                ui.label("").classes("flex-1")
                ui.button("Debug match arrays", icon="bug_report", on_click=_show_debug).props("flat dense text-grey-6")
            debug_label = ui.label("").classes("text-caption text-grey-6 font-mono")

    with ui.card().classes("w-[49%] p-4 overflow-y-auto"):
        FlipperPanel()

for p in cfg.get("prefixes", []):
    for a in all_prefixes:
        if _save_text(a["mod_id"], prefix_entries) == p or a["name"] == p:
            selected_prefixes.append(a["mod_id"])
            break
for s in cfg.get("suffixes", []):
    for a in all_suffixes:
        if _save_text(a["mod_id"], suffix_entries) == s or a["name"] == s:
            selected_suffixes.append(a["mod_id"])
            break
prefix_select.value = selected_prefixes[:]
suffix_select.value = selected_suffixes[:]
_rebuild_selected_chips()

listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.daemon = True
listener.start()

def main():
    import os
    import signal
    import time

    TRAY_ONLY = "--tray-only" in sys.argv

    from nicegui import core
    IS_FIRST = not core.app.is_started
    if IS_FIRST:
        _real_stop_and_exit = core.stop_and_exit
        core.stop_and_exit = lambda: None

        signal.signal(signal.SIGINT, lambda *_: os._exit(0))

        def _find_free_port() -> int:
            import socket
            s = socket.socket()
            s.bind(("", 0))
            port = s.getsockname()[1]
            s.close()
            return port

        PORT = _find_free_port()
        _window_proc = [None]

        import logging as _logging
        _tray_log = _logging.getLogger("tray")
        _tray_log.setLevel(_logging.DEBUG)
        from pathlib import Path as _Path
        _Path("log").mkdir(exist_ok=True)
        _h = _logging.FileHandler("log/tray.log", mode="w")
        _h.setFormatter(_logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        _tray_log.addHandler(_h)

        def _tray_show():
            _p = lambda *a, **kw: print(*a, file=__import__("sys").stderr, flush=True, **kw)
            _p("tray: Show clicked")
            if not TRAY_ONLY:
                try:
                    from nicegui.native import WindowProxy
                    _p("tray: WindowProxy restoring...")
                    WindowProxy().show()
                    WindowProxy().restore()
                    _p("tray: WindowProxy OK")
                except Exception as e:
                    _p("tray: WindowProxy failed:", e)
                    import traceback
                    traceback.print_exc(file=__import__("sys").stderr)
            proc = _window_proc[0]
            _p("tray: existing proc=%s alive=%s" % (proc, proc and proc.is_alive()))
            if proc and not proc.is_alive():
                _p("tray: proc dead, clearing")
                _window_proc[0] = None
            if not _window_proc[0]:
                _p("tray: spawning subprocess on port %d" % PORT)
                import multiprocessing as mp
                from pypoe.window import open_window
                p = mp.get_context("spawn").Process(target=open_window, args=(PORT,), daemon=True)
                p.start()
                _p("tray: subprocess started pid=%s" % p.pid)
                _window_proc[0] = p

        def _tray_quit():
            _real_stop_and_exit()

        threading.Thread(target=create_tray, args=(_tray_quit, _tray_show), daemon=True).start()

        def _poll_queue():
            while True:
                try:
                    from pypoe.flipper.ui import _pricer
                    q = _pricer.queue_size if _pricer else "?"
                    update_tooltip(f"PoE Crafting Macro — queue: {q}")
                except Exception:
                    pass
                time.sleep(2)

        threading.Thread(target=_poll_queue, daemon=True).start()

    ui.run(port=PORT if IS_FIRST else None, native=not TRAY_ONLY, show=not TRAY_ONLY, reload=False)

    if IS_FIRST:
        while True:
            time.sleep(60)


if __name__ == "__main__":
    main()
