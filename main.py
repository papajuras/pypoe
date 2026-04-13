import threading
import time

import pyautogui
import pyperclip
from pynput import keyboard
import os

pyautogui.FAILSAFE = False

# Configurable
use_exalt = False
use_regal = False
use_aug = True
count_to_regal = 2
count_to_exalt = 2

# wand
# prefixes = [" "]
# suffixes = ["increased Strength"]

# reservation
# prefixes = ["Pulsing", "Powerful", "Introspection"]
# suffixes = ["of the Philosopher", "of the Gorilla", "of the Heavens"]


# life small passive zenith
# prefixes = ["Powerful", "Stout"]
# suffixes = ["of the Gorilla", "of the Heavens"]

# large spell passive zenith
# prefixes = ["Powerful"]
# suffixes = ["of the Bear"]

# prefixes = ["Endurance Charge on Melee Stun"]
# prefixes = ["1% increased Spell Damage per 10 Strength"]
# prefixes = ["20% more Attack Damage"]
# suffixes = [" "]

# spell damage
# prefixes = ["Powerful", "Glowing"]
# suffixes = ["the Meteor", "of the Prodigy"]

# chaos damage
# prefixes = ["lming Malice"]
# suffixes = ["Unspeakable Gifts"]
# suffixes = [" "]

# max life
# prefixes = [" "]
# suffixes = ["of the Philosopher"]

# max life
prefixes = [" "]
suffixes = [" of Life when you Block"]

# quiver
# prefixes = [" "]
# suffixes = ["additional arrow"] #, "of Tzteosh", "Haast", "Ephij"

# heavy strike helmet
# prefixes = [" "]
# suffixes = ["Nearby Enemies have"] #, "of Tzteosh", "Haast", "Ephij"
# suffixes = ["Gain Accuracy Rating equal to your Strength"] #, "of Tzteosh", "Haast", "Ephij"

# phrecia light res amall
# prefixes = [" "]
# suffixes = ["of the Panther"]


pyautogui.PAUSE = 0.05 # Instead of the default 0.1
import ctypes
ctypes.CDLL('libX11.so.6').XInitThreads()
# 3 screens
alt_orb_position = [2073, 386]
item_position =[2352, 620]
aug_orb_position = [2213, 453]
scour_orb_position = [2489, 551]
regal_orb_position = [2486, 368]
exalt_orb_position = [2306, 381]
transmute_orb_position = [1986, 381]
delete_besats_position = [2033, 340]
# 2 screens
# alt_orb_position = [2071, 289]
# item_position =[2263, 477]
# aug_orb_position = [2176, 346]
# scour_orb_position = [2385, 415]
# regal_orb_position = [2378, 287]
# exalt_orb_position = [2249, 291]
# transmute_orb_position = [2016, 279]
# delete_besats_position = [2044, 258]

# ###############################################################
# Internal - do not change
regal_counter = 0
exalt_counter = 0
both_required = count_to_regal == 2
should_stop = False
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

    return pyperclip.paste().lower()

def delete_beasts():
    while not should_stop:
        delete_beast()

def delete_beast():
    move_to(delete_besats_position)
    time.sleep(0.15)
    kbd = keyboard.Controller()
    kbd.press(keyboard.Key.ctrl)
    time.sleep(0.15)
    pyautogui.click(button='left')
    time.sleep(0.15)
    pyautogui.click(button='left')
    time.sleep(0.15)
    kbd.release(keyboard.Key.ctrl)

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
    while counter < 1000 and not should_stop:
        move_to(alt_orb_position)
        time.sleep(0.15)
        pyautogui.click(button='right')
        time.sleep(0.15)

        move_to(item_position)
        pyautogui.click()
        time.sleep(0.15)

        cpd = capture_clipboard()

        previous_cpd = cpd
        aug_used = False
        if both_required:
            match_found = any_of_list_in_string(cpd, prefixes) and any_of_list_in_string(cpd, suffixes)
        else:
            match_found = any_of_list_in_string(cpd, prefixes) or any_of_list_in_string(cpd, suffixes)
        if match_found:
            pyautogui.keyUp('shift')

            if ('suffix' not in cpd or 'prefix' not in cpd) and use_aug:
                use_aug_orb()
                aug_used = True
            if use_regal:
                check_regal(cpd)
            else:
                return

        elif (any_of_list_in_string(cpd, prefixes) or both_required == False) and 'suffix' not in cpd and use_aug:
            use_aug_orb()
            aug_used = True
        elif (any_of_list_in_string(cpd, suffixes) or both_required == False) and 'prefix' not in cpd and use_aug:
            use_aug_orb()
            aug_used = True

        if aug_used:
            cpd = capture_clipboard()
        if both_required:
            match_found = any_of_list_in_string(cpd, prefixes) and any_of_list_in_string(cpd, suffixes)
        else:
            match_found = any_of_list_in_string(cpd, prefixes) or any_of_list_in_string(cpd, suffixes)
        if match_found:
            pyautogui.keyUp('shift')

            if use_regal:
                check_regal(cpd)
            else:
                return

        counter += 1
    pyautogui.keyUp('shift')
    exit()


def check_regal(cpd):
    prefixes_match = count_patterns_in_string(cpd, prefixes)
    suffixes_match = count_patterns_in_string(cpd, suffixes)
    if use_regal and (prefixes_match + suffixes_match) >= count_to_regal:
        print("Regalling!")
        regal_slam()
        global regal_counter
        regal_counter = regal_counter + 1
        print(f"Regal no: {regal_counter}")

        cpd = capture_clipboard()

        prefixes_match = count_patterns_in_string(cpd, prefixes)
        suffixes_match = count_patterns_in_string(cpd, suffixes)

        print(f"{(prefixes_match + suffixes_match)} matches")
        if prefixes_match + suffixes_match >= count_to_regal + 1 and not use_exalt:
            print(f"{count_to_regal + 1} MODS MATCH FOUND!")
            exit()
        elif prefixes_match + suffixes_match >= count_to_exalt:
            check_exalt(cpd)
        else:
            scour()
            transmute()


def save_exalt_clipboard(content):
    # Find the next available number
    i = 1
    while os.path.exists(f"exalt{i}.txt"):
        i += 1

    filename = f"exalt{i}.txt"
    with open(filename, "w") as f:
        f.write(content)
    print(f"Saved match to {filename}")

def check_exalt(cpd):
    prefixes_match = count_patterns_in_string(cpd, prefixes)
    suffixes_match = count_patterns_in_string(cpd, suffixes)
    if use_exalt and (prefixes_match + suffixes_match) >= count_to_exalt:
        print("Exalting!")
        exalt_slam()
        global exalt_counter
        exalt_counter = exalt_counter + 1
        print(f"Exalt no: {exalt_counter}")

        cpd = capture_clipboard()

        save_exalt_clipboard(cpd)

        prefixes_match = count_patterns_in_string(cpd, prefixes)
        suffixes_match = count_patterns_in_string(cpd, suffixes)

        print(f"{(prefixes_match + suffixes_match)} matches")
        if prefixes_match + suffixes_match >= count_to_exalt + 1:
            print(f"{exalt_counter + 1} MODS MATCH FOUND!")
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


def exalt_slam():
    move_to(exalt_orb_position)
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
    x, y = pyautogui.position()
    tx, ty = target_position
    dx = tx - x
    dy = ty - y
    pyautogui.moveRel(dx, dy, duration=0.1)

print("dupa")
# === Keyboard listener ===
pressed_keys = set()
is_running = False
def on_press(key):
    try:
        if key == keyboard.Key.esc:
            print("ESC pressed. Exiting.")
            global should_stop
            should_stop = True
        elif key.char:
            pressed_keys.add(key.char.lower())
    except AttributeError:
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            pressed_keys.add('ctrl')
        elif key == keyboard.Key.esc:
            print("ESC pressed. Exiting.")
            should_stop = True

    global is_running
    if is_running:
        return None
    # Check for Ctrl + J
    if 'ctrl' in pressed_keys and 'j' in pressed_keys:
        is_running = True
        print("Ctrl + J was pressed!")
        global regal_counter
        regal_counter = 0
        should_stop = False
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
    # Check for Ctrl + L
    if 'ctrl' in pressed_keys and 'l' in pressed_keys:
        should_stop = False
        spam_thread = threading.Thread(target=delete_beasts)
        spam_thread.start()
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
