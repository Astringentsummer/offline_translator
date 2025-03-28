import os
import pyaudio

class AudioRecorder:
    def __init__(self, sample_rate=44100, channels=1, chunk=1024, folder_name="guest_mic_recordings", device_name=None):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk = chunk
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.device_name = device_name or self.get_microphone_name()
        self.output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", folder_name)
        os.makedirs(self.output_dir, exist_ok=True)
