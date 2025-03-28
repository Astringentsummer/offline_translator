import pyaudio
import wave
import os
import time

class AudioRecorder:
    def __init__(self, sample_rate=44100, channels=1, chunk=1024):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk = chunk
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../internal_mic_recordings")
        os.makedirs(self.output_dir, exist_ok=True)
        self.device_name = self.get_microphone_name()
    
    def get_microphone_name(self):
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            if device_info.get("maxInputChannels", 0) > 0:
                return device_info["name"].replace(" ", "_")
        return "Unknown_Mic"

    def start_recording(self):
        if self.is_recording:
            return
        self.frames = []
        self.stream = self.audio.open(format=pyaudio.paInt16,
                                      channels=self.channels,
                                      rate=self.sample_rate,
                                      input=True,
                                      frames_per_buffer=self.chunk)
        self.is_recording = True

    def stop_recording(self):
        if not self.is_recording:
            return
        self.stream.stop_stream()
        self.stream.close()
        self.is_recording = False
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"internal_{timestamp}.wav"
        filepath = os.path.join(self.output_dir, filename)
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(self.frames))

    def record_chunk(self):
        if self.is_recording:
            data = self.stream.read(self.chunk)
            self.frames.append(data)

    def close(self):
        if self.stream:
            self.stream.close()
        self.audio.terminate()

def main():
    recorder = AudioRecorder()
    recorder.start_recording()
    for _ in range(0, int(44100 / 1024 * 5)):  # means only 5s
        recorder.record_chunk()
    recorder.stop_recording()
    recorder.close()

if __name__ == "__main__":
    main()
