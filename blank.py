from pynput import keyboard

# Track pressed keys
pressed_keys = set()

def on_press(key):
    pressed_keys.add(key)

    if key == keyboard.Key.esc:
        print("ESC pressed, exiting.")
        return False

    # Check if CTRL is held and 'j' is pressed
    if (keyboard.Key.ctrl_l in pressed_keys or keyboard.Key.ctrl_r in pressed_keys) and \
       key == keyboard.KeyCode.from_char('j'):
        print("CTRL + J detected!")
        return None
    return None


def on_release(key):
    # Remove key from pressed_keys set
    pressed_keys.discard(key)

# Start the listener
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
