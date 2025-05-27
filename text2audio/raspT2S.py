import subprocess
import os
import simpleaudio as sa

# Set paths to model and config files
model_path = "/home/tollmatcher2/offline_translator/text2audio/piper/en_US-kristin-medium.onnx"
config_path = "/home/tollmatcher2/offline_translator/text2audio/piper/en_US-kristin-medium.onnx.json"
output_path = "speech.wav"

while True:
    text = input("Enter text (or type 'bye' to exit): ")
    if text.lower() == "bye":
        print("Goodbye!")
        break

    # Call Piper via subprocess
    subprocess.run([
        "/home/tollmatcher2/offline_translator/text2audio/piper/piper/piper",
        "--model", model_path,
        "--config", config_path,
        "--output_file", output_path,
        "--text", text
    ])

    # Play the audio
    wave_obj = sa.WaveObject.from_wave_file(output_path)
    play_obj = wave_obj.play()
    play_obj.wait_done()

    os.remove(output_path)
