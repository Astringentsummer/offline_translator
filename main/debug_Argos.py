# Combines check_multiple_buttons + button4312_Argos.py

from gpiozero import Button
import threading
import time
import os
import glob
import subprocess
import pyaudio
import wave
import whisper
import warnings
import argostranslate.package
import argostranslate.translate

warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

# GPIO buttons
button1 = Button(27, pull_up=True, bounce_time=0.2)
button2 = Button(22, pull_up=True, bounce_time=0.2)
button3 = Button(20, pull_up=True, bounce_time=0.1)
button4 = Button(21, pull_up=True, bounce_time=0.1)

pressed_buttons = set()
active_recordings = set()
button_lock = threading.Lock()

buttons_illegal_state = False
button1_confirmed = False
button2_confirmed = False

button3_disturbed = False
button3_timer_running = False
button4_disturbed = False
button4_timer_running = False

def check_multiple_buttons(btn):
    global buttons_illegal_state, button3_disturbed, button4_disturbed
    with button_lock:
        if btn == button3 and button3_timer_running:
            print("[DEBUG] Button3 disturbed by re-pressing itself")
            button3_disturbed = True
        if btn == button4 and button4_timer_running:
            print("[DEBUG] Button4 disturbed by re-pressing itself")
            button4_disturbed = True

        pressed_buttons.add(btn.pin.number)
        if len(pressed_buttons) > 1:
            buttons_illegal_state = True
            print(f"[ERROR] Multiple buttons pressed: {pressed_buttons}")
            button3_disturbed = True
            button4_disturbed = True
            return False

        buttons_illegal_state = False
    return True

def release_button(btn):
    global buttons_illegal_state
    with button_lock:
        pressed_buttons.discard(btn.pin.number)
        if len(pressed_buttons) == 0:
            buttons_illegal_state = False

# Audio map and language setup
audio_map = {...}  # same as original
language_codes = ['en', 'de', 'zh']
source_index = language_codes.index('en')
target_index = language_codes.index('de')
selected_langs = {'source': language_codes[source_index], 'target': language_codes[target_index]}
play_audio("default")

# --- Implement real functions ---
def select_target(): ...
def select_source(): ...
def play_audio(lang_code): ...
def translate_text(...): ...
class AudioRecorder: ...

guest_recorder = AudioRecorder(mic_name="SF-558")
user_recorder = AudioRecorder(mic_name="EPOS PC 7 USB")
... # guest_thread, stop_guest, etc

def get_latest_recording(...): ...
def record_loop(...): ...
def speak_with_piper(...): ...

# --- Button1 ---
def button1_pressed(): ...
def button1_released(): ...

# --- Button2 ---
def button2_pressed(): ...
def button2_released(): ...

# --- Button3 ---
def button3_pressed():
    global button3_disturbed, button3_timer_running
    if button3_timer_running:
        print("[ERROR] Button3 pressed again within 1s")
        button3_disturbed = True
        return
    if not check_multiple_buttons(button3):
        return
    button3_disturbed = False
    button3_timer_running = True

    def confirm():
        global button3_timer_running
        time.sleep(1)
        with button_lock:
            if button3_disturbed or buttons_illegal_state:
                print("Button3: language switch cancelled")
            else:
                select_source()
        button3_timer_running = False

    threading.Thread(target=confirm).start()

def button3_released():
    release_button(button3)

# --- Button4 ---
def button4_pressed():
    global button4_disturbed, button4_timer_running
    if button4_timer_running:
        print("[ERROR] Button4 pressed again within 1s")
        button4_disturbed = True
        return
    if not check_multiple_buttons(button4):
        return
    button4_disturbed = False
    button4_timer_running = True

    def confirm():
        global button4_timer_running
        time.sleep(1)
        with button_lock:
            if button4_disturbed or buttons_illegal_state:
                print("Button4: language switch cancelled")
            else:
                select_target()
        button4_timer_running = False

    threading.Thread(target=confirm).start()

def button4_released():
    release_button(button4)

# Bindings
button1.when_pressed = button1_pressed
button1.when_released = button1_released
button2.when_pressed = button2_pressed
button2.when_released = button2_released
button3.when_pressed = button3_pressed
button3.when_released = button3_released
button4.when_pressed = button4_pressed
button4.when_released = button4_released

print("System ready. Waiting for button input...")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    guest_recorder.close()
    user_recorder.close()
    print("Cleaned up and exited.")
