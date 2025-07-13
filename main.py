import threading
import time

import pyautogui
import pyperclip
from pynput import keyboard

# Internal - do not change
regal_counter = 0

# Configurable
use_regal = True
use_aug = True
both_required = True
count_to_regal = 2


# reservation
prefixes = ["Pulsing", "Powerful", "Introspection"]
suffixes = ["of the Philosopher", "of the Gorilla", "of the Heavens"]

# spell damage
# prefixes = ["Glowing", "Powerful"]
# suffixes = ["of Expertise", "the Meteor", "of the Prodigy"]

# suffixes = ["(4-5) to Intelligence", "(6-8) to Intelligence"]
# suffixes = ["Gain an Endurance, Frenzy or Power charge when you Block"]
# suffixes = [" of Energy Shield when you Block"]

# 3 screens
alt_orb_position = [2064, 361]
item_position =[2352, 620]
aug_orb_position = [2213, 453]
scour_orb_position = [2477, 688]
regal_orb_position = [2486, 368]
transmute_orb_position = [1986, 381]
# 2 screens
# alt_orb_position = [163, 299]
# item_position =[357, 471]
# aug_orb_position = [262, 347]
# scour_orb_position = [474, 523]


# ###############################################################

previous_cpd = ""

def any_of_list_in_string(s, patterns):
    s = s.lower()
    return any(p.lower() in s for p in patterns)

def count_patterns_in_string(s, patterns):
    s = s.lower()
    return sum(1 for p in patterns if p.lower() in s)

def capture_clipboard():

    kbd = keyboard.Controller()
    kbd.press(keyboard.Key.ctrl)
    time.sleep(0.05)
    kbd.press(keyboard.Key.alt)
    time.sleep(0.05)
    kbd.press('c')
    time.sleep(0.2)
    kbd.release('c')
    kbd.release(keyboard.Key.alt)
    kbd.release(keyboard.Key.ctrl)

    return pyperclip.paste()

def spam_key(key='e'):
    global spamming
    spamming = not spamming
    while spamming:
        pyautogui.keyDown(key)
        time.sleep(0.03)
    pyautogui.keyUp(key)

def alt_spam():
    global previous_cpd
    counter = 0
    while counter < 1000:
        move_to(alt_orb_position)
        time.sleep(0.15)
        pyautogui.click(button='right')
        time.sleep(0.15)

        move_to(item_position)
        pyautogui.click()
        time.sleep(0.15)

        cpd = capture_clipboard().lower()
        if cpd == previous_cpd:
            counter += 1
            time.sleep(0.5)
            continue

        previous_cpd = cpd
        match_found = False
        if both_required:
            match_found = any_of_list_in_string(cpd, prefixes) and any_of_list_in_string(cpd, suffixes)
        else:
            match_found = any_of_list_in_string(cpd, prefixes) or any_of_list_in_string(cpd, suffixes)
        if match_found:
            pyautogui.keyUp('shift')

            if ('suffix' not in cpd or 'prefix' not in cpd) and use_aug:
                use_aug_orb()
            if use_regal:
                check_regal()
            else:
                return

        elif (any_of_list_in_string(cpd, prefixes) or both_required == False) and 'suffix' not in cpd and use_aug:
            use_aug_orb()
        elif (any_of_list_in_string(cpd, suffixes) or both_required == False) and 'prefix' not in cpd and use_aug:
            use_aug_orb()

        cpd = capture_clipboard()
        if both_required:
            match_found = any_of_list_in_string(cpd, prefixes) and any_of_list_in_string(cpd, suffixes)
        else:
            match_found = any_of_list_in_string(cpd, prefixes) or any_of_list_in_string(cpd, suffixes)
        if match_found:
            print("Match after augment (prefix)")
            pyautogui.keyUp('shift')

            if use_regal:
                check_regal()
            else:
                return

        counter += 1
    pyautogui.keyUp('shift')
    exit()


def check_regal():
    cpd = capture_clipboard().lower()

    prefixes_match = count_patterns_in_string(cpd, prefixes)
    suffixes_match = count_patterns_in_string(cpd, suffixes)
    if use_regal and (prefixes_match + suffixes_match) >= count_to_regal:
        print("Regalling!")
        regal_slam()
        global regal_counter
        regal_counter = regal_counter + 1
        print(f"Regal no: {regal_counter}")

        cpd = capture_clipboard().lower()

        prefixes_match = count_patterns_in_string(cpd, prefixes)
        suffixes_match = count_patterns_in_string(cpd, suffixes)

        print(f"{(prefixes_match + suffixes_match)} matches")
        if prefixes_match + suffixes_match == count_to_regal + 1:
            print(f"{count_to_regal + 1} MODS MATCH FOUND!")
            exit()
        else:
            scour()
            transmute()


def transmute():
    move_to(transmute_orb_position)
    time.sleep(0.15)
    pyautogui.click(button='right')
    time.sleep(0.15)
    move_to(item_position)
    pyautogui.click()
    time.sleep(0.15)


def scour():
    move_to(scour_orb_position)
    time.sleep(0.15)
    pyautogui.click(button='right')
    time.sleep(0.15)
    move_to(item_position)
    pyautogui.click()
    time.sleep(0.15)


def regal_slam():
    move_to(regal_orb_position)
    time.sleep(0.15)
    pyautogui.click(button='right')
    time.sleep(0.15)
    move_to(item_position)
    pyautogui.click()
    time.sleep(0.15)


def use_aug_orb():
    move_to(aug_orb_position)
    time.sleep(0.05)
    pyautogui.click(button='right')
    time.sleep(0.05)
    move_to(item_position)
    time.sleep(0.05)
    pyautogui.click()
    time.sleep(0.05)


def move_to(target_position):
    pyautogui.moveTo(target_position[0], target_position[1])

print("dupa")
# === Keyboard listener ===
pressed_keys = set()
is_running = False
def on_press(key):
    try:
        if key == keyboard.Key.esc:
            print("ESC pressed. Exiting.")
            return False
        elif key.char:
            pressed_keys.add(key.char.lower())
    except AttributeError:
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            pressed_keys.add('ctrl')
        elif key == keyboard.Key.esc:
            print("ESC pressed. Exiting.")
            return False

    global is_running
    if is_running:
        return None
    # Check for Ctrl + J
    if 'ctrl' in pressed_keys and 'j' in pressed_keys:
        is_running = True
        print("Ctrl + J was pressed!")
        time.sleep(1)
        spam_thread = threading.Thread(target=alt_spam)
        spam_thread.start()
        is_running = False
        return None
    # Check for Ctrl + K
    if 'ctrl' in pressed_keys and 'k' in pressed_keys:
        is_running = True
        x, y = pyautogui.position()
        print(f"Mouse at X: {x}, Y: {y}")
        clp = capture_clipboard()
        print(clp)
        is_running = False
        return None
    return None


def on_release(key):
    try:
        if key.char:
            pressed_keys.discard(key.char.lower())
    except AttributeError:
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            pressed_keys.discard('ctrl')

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
