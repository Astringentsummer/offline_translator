# Button3 + Button4 decide source and target languages
# And then Button1 function or Button2 function using gpiozero to record sounds
# will use 2 sets of specific hardwares to record and play
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
from transformers import MarianMTModel, MarianTokenizer

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

# Language selection logic
language_codes = ['en', 'de', 'zh']
source_index = 0
target_index = 0
selected_langs = {'source': language_codes[source_index], 'target': language_codes[target_index]}

# Audio confirmation files 
audio_map = {
    'en': os.path.join(os.path.dirname(__file__), '../languages/en.wav'),
    'de': os.path.join(os.path.dirname(__file__), '../languages/de.wav'),
    'zh': os.path.join(os.path.dirname(__file__), '../languages/zh.wav')
}

def play_audio(lang_code):
    path = audio_map.get(lang_code)
    if path and os.path.exists(path):
        print(f"Playing audio: {path}")
        subprocess.run(['aplay', "-D", "plughw:CARD=Device,DEV=0", path]) # using usb speaker to replay audip_map, letting user and guest know which language is chosen
    else:
        print(f"Audio file not found: {path}")

def select_source():
    global source_index
    source_index = (source_index + 1) % len(language_codes)
    selected_langs['source'] = language_codes[source_index]
    print(f"Selected source language: {selected_langs['source']}")
    play_audio(selected_langs['source'])

def select_target():
    global target_index
    target_index = (target_index + 1) % len(language_codes)
    selected_langs['target'] = language_codes[target_index]
    print(f"Selected target language: {selected_langs['target']}")
    play_audio(selected_langs['target'])

def translate_text(source_lang_code, target_lang_code, text):
    model_name = f"Helsinki-NLP/opus-mt-{source_lang_code}-{target_lang_code}" # using MarienMT with small model to translate text
    try:
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        translated_tokens = model.generate(**inputs)
        translation = tokenizer.decode(translated_tokens[0], skip_special_tokens=True)
        return translation
    except Exception as e:
        return f"Translation error: {e}"

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
            subprocess.run(["aplay", "-D", "plughw:CARD=USB,DEV=0", latest_file]) #button1's speaker, latest_file needs be changed later
        except Exception as e:
            print(f"Error playing guest audio: {e}")
        try:
            source = selected_langs['source']
            target = selected_langs['target']
            print(f"Transcribing ({source})...")
            model = whisper.load_model("tiny", device="cpu")          #using whisper for speech2text
            result = model.transcribe(latest_file, language=source)
            recognized = result["text"].strip()
            print("Recognized text:", recognized)
            print(f"Translating to {target}...")
            translation = translate_text(source, target, recognized)
            print("Translated text:", translation)
        except Exception as e:
            print(f"Error in transcription or translation: {e}")

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
            subprocess.run(["aplay", "-D", "plughw:CARD=Device,DEV=0", latest_file]) #button2's speaker
        except Exception as e:
            print(f"Error playing user audio: {e}")
        try:
            source = selected_langs['source']
            target = selected_langs['target']
            print(f"Transcribing ({source})...")
            model = whisper.load_model("tiny", device="cpu")
            result = model.transcribe(latest_file, language=source)
            recognized = result["text"].strip()
            print("Recognized text:", recognized)
            print(f"Translating to {target}...")
            translation = translate_text(source, target, recognized)
            print("Translated text:", translation)
        except Exception as e:
            print(f"Error in transcription or translation: {e}")

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
