# Button1 function + Button2 function using gpiozero , integate with whisper
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
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")


BUTTON1_PIN = 27 #button1
BUTTON2_PIN = 22 #button2
button1 = Button(BUTTON1_PIN, pull_up=True, bounce_time=0.2)
button2 = Button(BUTTON2_PIN, pull_up=True, bounce_time=0.2)

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
        self.folder_name = folder_name or ("guest_mic_recordings" if "SF-558" in mic_name else "user_mic_recordings")
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
            subprocess.run(["aplay", "-D", "plughw:CARD=USB,DEV=0", latest_file])  # hardware of button1
        except Exception as e:
            print(f"Error playing guest audio: {e}")

        # --- Whisper integration starts here ---
        try:
            print("Source language (e.g., en, zh, de, ar):") # type to choose source lanuage
            language = input("Enter source language code: ").strip().lower()

            print(f"Transcribing with tiny model using language: {language}") #using whisper(tiny) for speech2text
            model = whisper.load_model("tiny", device="cpu")
            result = model.transcribe(latest_file, language=language)
            print("Recognized text:", result["text"])

        except Exception as e:
            print(f"Error during transcription: {e}")
        # --- Whisper integration ends here ---


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
            subprocess.run(["aplay", "-D", "plughw:CARD=Device,DEV=0", latest_file])  # hardware of button2
        except Exception as e:
            print(f"Error playing user audio: {e}")

        # --- Whisper integration starts here ---
        try:
            print("Source language (e.g., en, zh, de, ar):") # type to choose source lanuage
            language = input("Enter source language code: ").strip().lower()

            print(f"Transcribing with tiny model using language: {language}") #using whisper(tiny) for speech2text
            model = whisper.load_model("tiny", device="cpu")
            result = model.transcribe(latest_file, language=language)
            print("Recognized text:", result["text"])

        except Exception as e:
            print(f"Error during transcription: {e}")
        # --- Whisper integration ends here ---


#gpiozero 
button1.when_pressed = button1_pressed
button1.when_released = button1_released
button2.when_pressed = button2_pressed
button2.when_released = button2_released

try:
    print("Waiting for button presses...")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    guest_recorder.close()
    user_recorder.close()
    print("Cleaned up and exited.")
