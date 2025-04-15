# Button1 function + Button2 function
# will use 2 sets of specific hardwares to record and play
# How to test? 1. activate virtual env 2. connect 2 buttons rightly 3. run
import RPi.GPIO as GPIO
import threading
import time
import os
import glob
import subprocess
from recorder import AudioRecorder as GuestRecorder
from recorder2 import AudioRecorder as UserRecorder

# Setup
GPIO.setmode(GPIO.BCM)
BUTTON1_PIN = 27 #connect 2 buttons rightly Button1
BUTTON2_PIN = 22 #Button2
GPIO.setup(BUTTON1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Recorders
guest_recorder = GuestRecorder(mic_name="SF-558") #Button1
user_recorder = UserRecorder(mic_name="EPOS PC 7 USB") #Button2

# Threads
guest_thread = None
user_thread = None
stop_guest = False
stop_user = False

# Helpers
def get_latest_recording(folder_name):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.join(base_dir, "..", folder_name)
    files = glob.glob(os.path.join(folder, "*.wav"))
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def record_loop(recorder, stop_flag_name):
    while not globals()[stop_flag_name]:
        recorder.record_chunk()
        time.sleep(0.01)

# Button 1 Logic (Guest)
def button1_pressed():
    global guest_thread, stop_guest
    if guest_recorder.is_recording:
        return
    print("Button1 pressed - start recording")
    guest_recorder.start_recording()
    stop_guest = False
    guest_thread = threading.Thread(target=record_loop, args=(guest_recorder, 'stop_guest'))
    guest_thread.start()

def button1_released():
    global guest_thread, stop_guest
    if not guest_recorder.is_recording:
        return
    print("Button1 released - stop recording")
    stop_guest = True
    guest_thread.join()
    guest_recorder.stop_recording()
    latest_file = get_latest_recording("guest_mic_recordings")
    if latest_file:
        print(f"Latest guest recording: {latest_file}")
        try:
            subprocess.run(["aplay", "-D", "plughw:CARD=USB,DEV=0", latest_file]) #Button1
        except Exception as e:
            print(f"Error playing guest audio: {e}")

# Button 2 Logic (User)
def button2_pressed():
    global user_thread, stop_user
    if user_recorder.is_recording:
        return
    print("Button2 pressed - start recording")
    user_recorder.start_recording()
    stop_user = False
    user_thread = threading.Thread(target=record_loop, args=(user_recorder, 'stop_user'))
    user_thread.start()

def button2_released():
    global user_thread, stop_user
    if not user_recorder.is_recording:
        return
    print("Button2 released - stop recording")
    stop_user = True
    user_thread.join()
    user_recorder.stop_recording()
    latest_file = get_latest_recording("user_mic_recordings")
    if latest_file:
        print(f"Latest user recording: {latest_file}")
        try:
            subprocess.run(["aplay", "-D", "plughw:CARD=Device,DEV=0", latest_file]) #Button2
        except Exception as e:
            print(f"Error playing user audio: {e}")

# GPIO Callbacks
def gpio_callback(channel):
    if channel == BUTTON1_PIN:
        if GPIO.input(BUTTON1_PIN) == 0:
            button1_pressed()
        else:
            button1_released()
    elif channel == BUTTON2_PIN:
        if GPIO.input(BUTTON2_PIN) == 0:
            button2_pressed()
        else:
            button2_released()

GPIO.add_event_detect(BUTTON1_PIN, GPIO.BOTH, callback=gpio_callback, bouncetime=200)
GPIO.add_event_detect(BUTTON2_PIN, GPIO.BOTH, callback=gpio_callback, bouncetime=200)

# Main loop
try:
    print("Waiting for button presses...")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    GPIO.cleanup()
    guest_recorder.close()
    user_recorder.close()
    print("Cleaned up and exited.")
