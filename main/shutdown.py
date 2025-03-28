# # Function: a 3-second press for shutdown and a 5-second press for reboot
# How to test? 1. activate virtual env 2. connect rightly 3. delete print and run with sudo
import RPi.GPIO as GPIO
import time
import os

GPIO.setmode(GPIO.BCM)
BUTTON_PIN = 17 # after connecting, change to the exact pin. Or make sure physical 11 and GND
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

while True:
    if GPIO.input(BUTTON_PIN) == False:
        press_time = time.time()
        while GPIO.input(BUTTON_PIN) == False:
            time.sleep(0.1)
        release_time = time.time()
        duration = release_time - press_time

        if duration >= 5:
            print("REBOOT")
            # when really need reboot and shutdow, otherwise just using print
            # os.system("sudo reboot")
        elif duration >= 3:
            print("SHUTDOWN")
            # os.system("sudo shutdown -h now")
