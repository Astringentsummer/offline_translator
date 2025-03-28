import RPi.GPIO as GPIO
from main.recorder import AudioRecorder
import time

GPIO.setmode(GPIO.BCM)
BUTTON_PIN = 27 # notice: connect correctly
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

recorder = AudioRecorder()
last_pressed = 0

def toggle_recording(channel):
    global last_pressed
    now = time.time()
    if now - last_pressed < 0.5:
        return
    last_pressed = now

    if recorder.is_recording:
        recorder.stop_recording()
    else:
        recorder.start_recording()

GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=toggle_recording, bouncetime=300)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    GPIO.cleanup()
