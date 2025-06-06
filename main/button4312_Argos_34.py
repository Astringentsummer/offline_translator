# Button3 + Button4 decide source and target languages (source = guest's native language, target = user's native language)
# And then Button1 function or Button2 function using gpiozero to record sounds
# will use 2 sets of specific hardwares to record and replay the translation
# How to test? 1. activate virtual env 2. connect 4 buttons rightly 3. run test
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

# Button pin definitions
BUTTON1_PIN = 27  # button1 - guest mic
BUTTON2_PIN = 22  # button2 - user mic
BUTTON3_PIN = 20  # button3 - select source language
BUTTON4_PIN = 21  # button4 - select target language

button1 = Button(BUTTON1_PIN, pull_up=True, bounce_time=0.2)
button2 = Button(BUTTON2_PIN, pull_up=True, bounce_time=0.2)
button3 = Button(BUTTON3_PIN)
button4 = Button(BUTTON4_PIN)

# For Button1 (Guest Mic) long-press confirmation
guest_button_confirmed = False
guest_record_start_time = None
# For Button2 (User Mic) long-press confirmation
user_button_confirmed = False
user_record_start_time = None


# Audio confirmation files 
audio_map = {
    'zh_en': os.path.join(os.path.dirname(__file__), '../languages/zh_en.wav'), # means user_guest lang
    'zh_de': os.path.join(os.path.dirname(__file__), '../languages/zh_de.wav'),
    'en_zh': os.path.join(os.path.dirname(__file__), '../languages/en_zh.wav'),
    'en_de': os.path.join(os.path.dirname(__file__), '../languages/en_de.wav'),
    'de_zh': os.path.join(os.path.dirname(__file__), '../languages/de_zh.wav'),
    'de_en': os.path.join(os.path.dirname(__file__), '../languages/de_en.wav'),

    't_en': os.path.join(os.path.dirname(__file__), '../languages/en_user.wav'), # target = user lang
    't_de': os.path.join(os.path.dirname(__file__), '../languages/de_user.wav'),
    't_zh': os.path.join(os.path.dirname(__file__), '../languages/zh_user.wav'),
    
    'default': os.path.join(os.path.dirname(__file__), '../languages/default.wav'),
    'error': os.path.join(os.path.dirname(__file__), '../languages/error.wav')
}

current_audio_process = None
current_audio_owner = None 
interrupt_whitelist = set()

def play_audio(lang_code, owner=None, allow_interrupt_from=None):
    global current_audio_process, current_audio_owner, interrupt_whitelist

    path = audio_map.get(lang_code)
    if path and os.path.exists(path):
        print(f"Playing audio: {path}")

        if current_audio_process and current_audio_process.poll() is None:
            current_audio_process.terminate()
            print(f"Previous audio interrupted. Owner was {current_audio_owner}")

        current_audio_owner = owner
        interrupt_whitelist = set(allow_interrupt_from or [])
        current_audio_process = subprocess.Popen(['aplay', '-D', 'plughw:CARD=USB,DEV=0', path])

        # Start monitor thread to clear owner when playback finishes
        threading.Thread(target=monitor_audio_completion, args=(owner,), daemon=True).start()

    else:
        print(f"Audio file not found: {path}")

def monitor_audio_completion(owner_to_clear):
    global current_audio_process, current_audio_owner

    if current_audio_process:
        current_audio_process.wait()  # block until playback ends
        print(f"Audio playback by {owner_to_clear} completed.")
        if current_audio_owner == owner_to_clear:
            current_audio_owner = None
            print("Audio owner cleared. Button1/2 can now record.")


def interrupt_audio_playback(caller):
    global current_audio_process, current_audio_owner, interrupt_whitelist
    if current_audio_process and current_audio_process.poll() is None:
        if caller in interrupt_whitelist:
            current_audio_process.terminate()
            print(f"Audio interrupted by {caller}. Previous owner was {current_audio_owner}")
            return True
        else:
            print(f"Caller {caller} not allowed to interrupt current playback from {current_audio_owner}")
            return False
    return True  # nothing is playing, so allow



# Language selection logic
language_codes = ['en', 'de', 'zh']
source_index = language_codes.index('en') # guest's default lang
target_index = language_codes.index('de') # user's default lang
selected_langs = {'source': language_codes[source_index], 'target': language_codes[target_index]}
print("Default setting: user's language is German (target), guest's language is English (source).")
play_audio("default", owner=None, allow_interrupt_from=["button1", "button2", "button3", "button4"]) 

# Button4
def select_target():
    if not interrupt_audio_playback("button4"):
        return  # do not proceed

    global target_index
    target_index = (target_index + 1) % len(language_codes)
    selected_langs['target'] = language_codes[target_index]
    print(f"Selected target language: {selected_langs['target']}")
    play_audio(f"t_{selected_langs['target']}", owner="button4", allow_interrupt_from=["button4"])

#play target languages' audioes, couldn't be interrupted by any other button expect itself
    
# Button3    
def select_source():
    if not interrupt_audio_playback("button3"):
        return

    global source_index
    target_lang = selected_langs['target']
    available_sources = [lang for lang in language_codes if lang != target_lang]

    if selected_langs['source'] not in available_sources:
        selected_langs['source'] = available_sources[0]
        source_index = language_codes.index(selected_langs['source'])

    current_index = available_sources.index(selected_langs['source'])
    new_index = (current_index + 1) % len(available_sources)
    selected_langs['source'] = available_sources[new_index]
    source_index = language_codes.index(selected_langs['source'])

    print(f"Selected source language: {selected_langs['target']}_{selected_langs['source']}")
    play_audio(f"{selected_langs['target']}_{selected_langs['source']}", owner="button3", allow_interrupt_from=["button3"])

# couldn't be interrupted by any other button expect itself


#Argos
def translate_text(source_lang_code, target_lang_code, text):
    installed_languages = argostranslate.translate.get_installed_languages()
    from_lang = next((lang for lang in installed_languages if lang.code == source_lang_code), None)
    to_lang = next((lang for lang in installed_languages if lang.code == target_lang_code), None)

    if not from_lang or not to_lang:
        return f"Error: Argos translation not available from {source_lang_code} to {target_lang_code}."

    translation = from_lang.get_translation(to_lang)
    return translation.translate(text)

class AudioRecorder:
    def __init__(self, sample_rate=48000, channels=1, chunk=1024, folder_name=None, mic_name=None):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk = chunk
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.device_index = self.get_input_device_index(mic_name)
        self.device_name = self.get_device_name(self.device_index)
        self.folder_name = folder_name or ("guest_mic_recordings" if "SF-558" in mic_name else "user_mic_recordings") #Button1's mic
        self.output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", self.folder_name)
        os.makedirs(self.output_dir, exist_ok=True)

    def get_input_device_index(self, target_name=None):
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info.get("maxInputChannels", 0) > 0:
                if target_name is None or target_name.lower() in info["name"].lower():
                    return i
        raise ValueError(f"No input device found matching name: {target_name}")

    def get_device_name(self, index):
        return self.audio.get_device_info_by_index(index)["name"].replace(" ", "_")

    def start_recording(self):
        if self.is_recording:
            return
        self.frames = []
        self.stream = self.audio.open(format=pyaudio.paInt16,
                                      channels=self.channels,
                                      rate=self.sample_rate,
                                      input=True,
                                      input_device_index=self.device_index,
                                      frames_per_buffer=self.chunk)
        self.is_recording = True

    def stop_recording(self):
        if not self.is_recording:
            return
        self.stream.stop_stream()
        self.stream.close()
        self.is_recording = False
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{self.device_name}_{timestamp}.wav"
        filepath = os.path.join(self.output_dir, filename)
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(self.frames))
        self.last_filepath = filepath

    def record_chunk(self):
        if self.is_recording:
            try:
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                self.frames.append(data)
            except Exception as e:
                print(f"Audio read error: {e}")

    def close(self):
        if self.stream:
            self.stream.close()
        self.audio.terminate()

    def get_last_filepath(self):
        return getattr(self, "last_filepath", None)

guest_recorder = AudioRecorder(mic_name="SF-558")
user_recorder = AudioRecorder(mic_name="EPOS PC 7 USB")

guest_thread = None
user_thread = None
stop_guest = False
stop_user = False

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

def speak_with_piper(text, lang_code, device):
    piper_models = {
        "zh": {
            "model": "zh_CN-huayan-medium.onnx",
            "config": "zh_CN-huayan-medium.onnx.json"
        },
        "en": {
            "model": "en_US-john-medium.onnx",
            "config": "en_US-john-medium.onnx.json"
        },
        "de": {
            "model": "de_DE-thorsten-medium.onnx",
            "config": "de_DE-thorsten-medium.onnx.json"
        }
    }

    PIPER_PATH = "/home/tollmatcher2/offline_translator/piper_rebuild/piper/piper"
    OUTPUT_DIR = "/home/tollmatcher2/offline_translator/output"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    voice = piper_models[lang_code]
    timestamp = int(time.time())
    output_file = os.path.join(OUTPUT_DIR, f"{lang_code}_{timestamp}.wav")

    command = [
        PIPER_PATH,
        "--model", f"/home/tollmatcher2/offline_translator/piper_rebuild/piper/{voice['model']}",
        "--config", f"/home/tollmatcher2/offline_translator/piper_rebuild/piper/{voice['config']}",
        "--output_file", output_file,
    ]

    print("Synthesizing speech with Piper...")
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    process.communicate(input=text.encode("utf-8"))
    print(f"Synthesized speech saved to: {output_file}")

    # Play using the specified speaker device
    subprocess.run(["aplay", "-D", device, output_file])

# Button 1 Logic (Guest)
def button1_pressed():
    interrupt_audio_playback("button1")

    global guest_thread, stop_guest, guest_button_confirmed, guest_record_start_time

    if current_audio_owner in ["button3", "button4"]:
        print("Playback from Button3/4 is active. Button1 recording blocked.")
        return

    if guest_recorder.is_recording:
        return

    print("Button1 pressed — start recording immediately")
    guest_button_confirmed = False
    guest_record_start_time = time.time()

    guest_recorder.start_recording()
    stop_guest = False
    guest_thread = threading.Thread(target=record_loop, args=(guest_recorder, 'stop_guest'))
    guest_thread.start()



def button1_released():
    global guest_thread, stop_guest, guest_button_confirmed, guest_record_start_time

    if not guest_recorder.is_recording:
        return

    duration = time.time() - guest_record_start_time
    stop_guest = True
    guest_thread.join()
    guest_recorder.stop_recording()
    
    latest_file = get_latest_recording("guest_mic_recordings")
    if duration < 1.0:  # Have to hold button1 more than 1s
        print("Button1 released too early — delete latest recording")
        if latest_file and os.path.exists(latest_file):
            os.remove(latest_file)
        return

    print("Button1 released after 1s — continue with STT + translation + TTS")

    latest_file = get_latest_recording("guest_mic_recordings")
    if latest_file:
        print(f"Latest guest recording: {latest_file}")
        try:
            source = selected_langs['source']
            target = selected_langs['target']

            t0 = time.time()
            print(f"Transcribing ({source})...")
            model = whisper.load_model("tiny", device="cpu")
            result = model.transcribe(latest_file, language=source)
            recognized = result["text"].strip()
            t1 = time.time()
            print("Recognized text:", recognized)
            print(f"[Time] STT took {t1 - t0:.2f} seconds")

            print(f"Translating to {target}...")
            translation = translate_text(source, target, recognized)
            t2 = time.time()
            print("Translated text:", translation)
            print(f"[Time] Translation took {t2 - t1:.2f} seconds")

            print("Speaking with Piper...")
            speak_with_piper(translation, target, device="plughw:CARD=USB,DEV=0")
            t3 = time.time()
            print(f"[Time] TTS took {t3 - t2:.2f} seconds")
            print(f"[Total Time] {t3 - t0:.2f} seconds")

        except Exception as e:
            print(f"Error in transcription, translation, or TTS: {e}")



# Button 2 Logic (User)
def button2_pressed():
    interrupt_audio_playback("button2")

    global user_thread, stop_user, user_button_confirmed, user_record_start_time

    if current_audio_owner in ["button3", "button4"]:
        print("Playback from Button3/4 is active. Button2 recording blocked.")
        return

    source = selected_langs['source']
    target = selected_langs['target']
    if source == target:
        print("Source and target languages must be different.")
        play_audio("error", owner="button2", allow_interrupt_from=["button2"])
        return

    if user_recorder.is_recording:
        return

    print("Button2 pressed — start recording immediately")
    user_button_confirmed = False
    user_record_start_time = time.time()

    user_recorder.start_recording()
    stop_user = False
    user_thread = threading.Thread(target=record_loop, args=(user_recorder, 'stop_user'))
    user_thread.start()




# button2s target language and source language are opposite with button1's
def button2_released():
    global user_thread, stop_user, user_button_confirmed, user_record_start_time

    if not user_recorder.is_recording:
        return

    duration = time.time() - user_record_start_time
    stop_user = True
    user_thread.join()
    user_recorder.stop_recording()

    latest_file = get_latest_recording("user_mic_recordings")
    if duration < 1.0: # Have to hold button2 more than 1s
        print("Button2 released too early — delete latest recording")
        if latest_file and os.path.exists(latest_file):
            os.remove(latest_file)
        return
        
    print("Button2 released after 1s — continue with STT + translation + TTS")

    latest_file = get_latest_recording("user_mic_recordings")
    if latest_file:
        print(f"Latest user recording: {latest_file}")
        try:
            # reverse
            source = selected_langs['target']
            target = selected_langs['source']

            t0 = time.time()
            print(f"Transcribing ({source})...")
            model = whisper.load_model("tiny", device="cpu")
            result = model.transcribe(latest_file, language=source)
            recognized = result["text"].strip()
            t1 = time.time()
            print("Recognized text:", recognized)
            print(f"[Time] STT took {t1 - t0:.2f} seconds")

            print(f"Translating to {target}...")
            translation = translate_text(source, target, recognized)
            t2 = time.time()
            print("Translated text:", translation)
            print(f"[Time] Translation took {t2 - t1:.2f} seconds")

            print("Speaking with Piper...")
            speak_with_piper(translation, target, device="plughw:CARD=Device,DEV=0")
            t3 = time.time()
            print(f"[Time] TTS took {t3 - t2:.2f} seconds")
            print(f"[Total Time] {t3 - t0:.2f} seconds")

        except Exception as e:
            print(f"Error in transcription, translation, or TTS: {e}")

# gpiozero button binding
button1.when_pressed = button1_pressed
button1.when_released = button1_released
button2.when_pressed = button2_pressed
button2.when_released = button2_released
button3.when_pressed = select_source
button4.when_pressed = select_target

try:
    print("Waiting for button presses...")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    guest_recorder.close()
    user_recorder.close()
    print("Cleaned up and exited.")
