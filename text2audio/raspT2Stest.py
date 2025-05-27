import subprocess
import os
import simpleaudio as sa

model_path = "/home/tollmatcher2/offline_translator/text2audio/piper/en_US-kristin-medium.onnx"
config_path = "/home/tollmatcher2/offline_translator/text2audio/piper/  .onnx.json"
output_path = "speech.wav"

while True:
    text = input("Enter text (or type 'bye' to exit): ")
    if text.lower() == "bye":
        print("Goodbye!")
        break

    result = subprocess.run([
        "/home/tollmatcher2/offline_translator/text2audio/piper/piper/piper",        
        "--model", model_path,
        "--config", config_path,
        "--output_file", output_path,
        "--text", "how are you"
    ])

    # Check if audio file was created
    if os.path.exists(output_path):
        wave_obj = sa.WaveObject.from_wave_file(output_path)
        play_obj = wave_obj.play()
        play_obj.wait_done()
        os.remove(output_path)
    else:
        print("Failed to generate audio. Check if model and config are valid.")
