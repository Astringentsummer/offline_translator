from main.recorder import AudioRecorder
import time

recorder = AudioRecorder()
recorder.start_recording()

for _ in range(0, int(recorder.sample_rate / recorder.chunk * 5)):
    recorder.record_chunk()

recorder.stop_recording()
recorder.close()
