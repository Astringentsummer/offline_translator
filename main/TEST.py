from gpiozero import Button
import threading
import time

button1 = Button(27, pull_up=True, bounce_time=0.1)
button2 = Button(22, pull_up=True, bounce_time=0.1)
button3 = Button(20, pull_up=True, bounce_time=0.1)
button4 = Button(21, pull_up=True, bounce_time=0.1)

pressed_buttons = set()
active_recordings = set()
button_lock = threading.Lock()

buttons_illegal_state = False
button1_confirmed = False
button2_confirmed = False

# 新增用于 Button3/4 控制
button3_disturbed = False
button3_timer_running = False
button4_disturbed = False
button4_timer_running = False

def check_multiple_buttons(btn):
    global buttons_illegal_state, button3_disturbed, button4_disturbed
    with button_lock:
        # 如果自己已经按下过，则表示重复按，也要视为干扰
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

# --- Button1 ---
def button1_pressed():
    global button1_confirmed
    if not check_multiple_buttons(button1):
        return
    print("Button1: start recording immediately")
    button1_confirmed = False
    active_recordings.add(27)

    def confirm():
        global button1_confirmed
        time.sleep(1)
        with button_lock:
            if 27 not in pressed_buttons:
                print("Button1: recording cancelled — user released button within 1 second")
            elif buttons_illegal_state:
                print("Button1: recording cancelled — another button was pressed within 1 second")
            else:
                print("Button1: recording confirmed")
                button1_confirmed = True

    threading.Thread(target=confirm).start()

def button1_released():
    release_button(button1)
    if 27 not in active_recordings:
        print("Button1: recording was never started, skipping output")
        return
    active_recordings.discard(27)
    if button1_confirmed:
        print("Button1: save recording and start STT, translate, TTS")
    else:
        print("Button1: recording discarded")

# --- Button2 ---
def button2_pressed():
    global button2_confirmed
    if not check_multiple_buttons(button2):
        return
    print("Button2: start recording immediately")
    button2_confirmed = False
    active_recordings.add(22)

    def confirm():
        global button2_confirmed
        time.sleep(1)
        with button_lock:
            if 22 not in pressed_buttons:
                print("Button2: recording cancelled — user released button within 1 second")
            elif buttons_illegal_state:
                print("Button2: recording cancelled — another button was pressed within 1 second")
            else:
                print("Button2: recording confirmed")
                button2_confirmed = True

    threading.Thread(target=confirm).start()

def button2_released():
    release_button(button2)
    if 22 not in active_recordings:
        print("Button2: recording was never started, skipping output")
        return
    active_recordings.discard(22)
    if button2_confirmed:
        print("Button2: save recording and start STT, translate, TTS")
    else:
        print("Button2: recording discarded")

# --- Button3 ---
def button3_pressed():
    global button3_disturbed, button3_timer_running
    if button3_timer_running:
        print(f"[ERROR] Multiple buttons pressed: {{20}} (Button3 was pressed twice within 1s)")
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
                print("Button3: source language switched and audio played")
        button3_timer_running = False

    threading.Thread(target=confirm).start()

def button3_released():
    release_button(button3)

# --- Button4 ---
def button4_pressed():
    global button4_disturbed, button4_timer_running
    if button4_timer_running:
        print(f"[ERROR] Multiple buttons pressed: {{20}} (Button4 was pressed twice within 1s)")
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
                print("Button4: target language switched and audio played")
        button4_timer_running = False

    threading.Thread(target=confirm).start()

def button4_released():
    release_button(button4)

# --- GPIO Bindings ---
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
    print("\nSystem exited.")
