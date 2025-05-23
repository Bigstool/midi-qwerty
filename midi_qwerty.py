import mido
from pynput.keyboard import Controller, Key
import threading
import time


def main():
    keyboard = Controller()

    # Customize this mapping!
    note_to_key = {
        41: 'z',
        42: Key.esc,
        43: 'x',
        45: 'c',
        44: 'v',
        46: Key.tab,
        47: Key.ctrl_l,
        48: Key.shift_l,
        49: Key.alt_l,
        50: 'a',
        51: 'w',
        52: 's',
        53: 'd',
        55: Key.space,
        60: 'a',
        61: 'b',
        62: 'c',
        63: 'd',
        64: 'e',
        65: 'f',
        66: 'g',
        67: 'h',
        68: 'i',
        69: 'j',
        70: 'k',
        71: 'l',
        72: Key.alt_r,
        73: Key.ctrl_r,
        74: Key.left,
        75: Key.up,
        76: Key.down,
        77: Key.right,
        78: Key.enter,
        79: Key.shift_r
        # Add more as needed!
    }

    key_repeat_interval = 0.05  # seconds between repeated characters
    key_repeat_delay = 0.5  # delay before starting repeat
    repeat_threads = {}  # note -> thread
    stop_flags = {}  # note -> threading.Event
    damper_on = False

    print("Available MIDI input ports:")
    for i, name in enumerate(mido.get_input_names()):
        print(f"{i}: {name}")
    input_index = int(input("Select input port number: "))
    input_name = mido.get_input_names()[input_index]

    print(f"\n🎧 Listening for MIDI notes on '{input_name}'...")
    with mido.open_input(input_name) as inport:
        try:
            for msg in inport:
                if msg.type in ['note_on', 'note_off'] and msg.note not in note_to_key:
                    continue
                elif msg.type == 'note_on':
                    note = msg.note
                    key = note_to_key[note]
                    if msg.velocity > 0:
                        if note not in repeat_threads:
                            keyboard.press(key)
                            stop_flags[note] = threading.Event()
                            repeat_threads[note] = threading.Thread(
                                target=repeat_key,
                                args=(keyboard, key_repeat_delay, key_repeat_interval, key, stop_flags[note])
                            )
                            repeat_threads[note].daemon = True
                            repeat_threads[note].start()
                            print(f"⬇️ Note {note} → Press '{key}'")
                    else:
                        if note in repeat_threads:
                            stop_flags[note].set()
                            repeat_threads[note].join()
                            del repeat_threads[note]
                            del stop_flags[note]
                            keyboard.release(key)
                            print(f"⬆️ Note {note} → Release '{key}'")
                elif msg.type == 'note_off':
                    note = msg.note
                    key = note_to_key[note]
                    if note in repeat_threads:
                        stop_flags[note].set()
                        repeat_threads[note].join()
                        del repeat_threads[note]
                        del stop_flags[note]
                        keyboard.release(key)
                        print(f"⬆️ Note {note} → Release '{key}'")
                elif msg.type == 'control_change' and msg.control == 64:
                    key = Key.shift_l
                    if msg.value >= 64 and not damper_on:
                        keyboard.press(key)
                        damper_on = True
                        print(f"🎛️ Damper down → Press {key}")
                    elif msg.value < 64 and damper_on:
                        keyboard.release(key)
                        damper_on = False
                        print(f"🎛️ Damper up → Release {key}")
        except KeyboardInterrupt:
            print("\n👋 Exiting.")
            for note in list(repeat_threads.keys()):
                stop_flags[note].set()
                repeat_threads[note].join()
                del repeat_threads[note]
                del stop_flags[note]
                keyboard.release(note_to_key[note])


# def press_key(keyboard, note_to_key, repeat_threads, stop_flags, interval, note):
#     key = note_to_key[note]
#     keyboard.press(key)
#     stop_flags[note] = threading.Event()
#     repeat_threads[note] = threading.Thread(
#         target=repeat_key,
#         args=(keyboard, key, interval, key, stop_flags[note])
#     )
#     repeat_threads[note].daemon = True
#     repeat_threads[note].start()
#     print(f"⬇️ Note {note} → Press '{key}'")

def repeat_key(keyboard, delay, interval, key, stop_event):
    time.sleep(delay)
    while not stop_event.is_set():
        keyboard.press(key)
        keyboard.release(key)
        time.sleep(interval)


if __name__ == "__main__":
    main()
