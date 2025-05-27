import subprocess
import time
import os

PIPER_PATH = "/home/tollmatcher2/offline_translator/piper_rebuild/piper/piper"
OUTPUT_DIR = "/home/tollmatcher2/offline_translator/output"

VOICE_MODELS = {
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

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    lang_choice = input("Enter language (zh, en, de): ").strip().lower()
    if lang_choice not in VOICE_MODELS:
        print("Invalid language")
        return

    text = input("Enter text to synthesize: ").strip()
    if not text:
        print("Empty input")
        return

    voice = VOICE_MODELS[lang_choice]
    timestamp = int(time.time())
    output_file = os.path.join(OUTPUT_DIR, f"{lang_choice}_{timestamp}.wav")

    command = [
        PIPER_PATH,
        "--model", f"/home/tollmatcher2/offline_translator/piper_rebuild/piper/{voice['model']}",
        "--config", f"/home/tollmatcher2/offline_translator/piper_rebuild/piper/{voice['config']}",
        "--output_file", output_file,
    ]

    print("Synthesizing...")
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    process.communicate(input=text.encode("utf-8"))
    print(f"Saved to: {output_file}")

if __name__ == "__main__":
    main()
