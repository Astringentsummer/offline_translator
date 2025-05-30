# Button1 function: press_hold_record
# recording guest's sounds by using device SF-558
# + when releasing button1, play the lastest recording sounds (in guest_mic_recordings file) in device EPOS PC 7 USB
# How to test? 1. activate virtual env 2. connect rightly 3. run with sudo
import RPi.GPIO as GPIO
import threading
import time
from recorder import AudioRecorder
import os
import glob
import subprocess

GPIO.setmode(GPIO.BCM)
BUTTON_PIN = 27 # notice: connect correctly
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

recorder = AudioRecorder(mic_name="SF-558")
recording_thread = None
stop_thread = False

def get_latest_recording():
    base_dir = os.path.dirname(os.path.abspath(__file__)) 
    folder = os.path.join(base_dir, "..", "guest_mic_recordings")
    files = glob.glob(os.path.join(folder, "*.wav"))
    if not files:
        return None
    latest_file = max(files, key=os.path.getmtime)
    return os.path.abspath(latest_file)

def record_loop():
    global stop_thread
    while not stop_thread:
        recorder.record_chunk()
        time.sleep(0.01)

def button_pressed(channel):
    global recording_thread, stop_thread
    if recorder.is_recording:
        return
    print("Button1 pressed - start recording")
    recorder.start_recording()
    stop_thread = False
    recording_thread = threading.Thread(target=record_loop)
    recording_thread.start()

def button_released(channel):
    global recording_thread, stop_thread
    if not recorder.is_recording:
        return
    print("Button1 released - stop recording")
    stop_thread = True
    recording_thread.join()
    recorder.stop_recording()
    
    # find the lastest recording sounds (in guest_mic_recordings file) and play it by device EPOS ( will be changed for tranlation later)
    latest_file = get_latest_recording()
    if latest_file:
        print(f"Latest recording: {latest_file}")
        # now:just play the lastest sounds
        try:
            subprocess.run(["aplay", "-D", "plughw:CARD=USB,DEV=0", latest_file])
            # use device EPOS PC 7 USB, plughw:CARD=USB,DEV=0
        except Exception as e:
            print(f"Error playing sound with aplay: {e}")
            
def button_callback(channel):
    if GPIO.input(BUTTON_PIN) == 0:
        button_pressed(channel)
    else:
        button_released(channel)
        
GPIO.add_event_detect(BUTTON_PIN, GPIO.BOTH, callback=button_callback, bouncetime=200)

try:
    print("Waiting for button1 press...")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    GPIO.cleanup()
    recorder.close()
    print("Cleaned up and exited.")
