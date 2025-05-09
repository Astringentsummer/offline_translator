import sounddevice as sd
import whisper
import numpy as np
import tempfile
import soundfile as sf
import shutil
import sys
import warnings

# 🔇 Optional: Whisper-Warnung für FP16 ausblenden
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

SAMPLE_RATE = 16000
DAUER = 5  # Sekunden

# Unterstützte Sprachen
SPRACHEN = {
    "de": "Deutsch",
    "en": "Englisch",
    "ar": "Arabisch",
    "fa": "Persisch"
}

def check_ffmpeg():
    if shutil.which("ffmpeg") is None:
        print("❌ FFmpeg nicht gefunden!")
        print("📦 Bitte installiere FFmpeg und füge es dem PATH hinzu.")
        print("🔗 https://ffmpeg.org/download.html")
        sys.exit(1)

def sprache_zu_text_einmal(sprache="de", dauer=DAUER):
    print(f"🎧 [{SPRACHEN[sprache]}] Bitte sprich jetzt...")
    aufnahme = sd.rec(int(dauer * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='int16')
    sd.wait()
    print("✅ Aufnahme beendet.")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
        sf.write(temp_wav.name, aufnahme, SAMPLE_RATE)
        audio_path = temp_wav.name

    model = whisper.load_model("base")
    result = model.transcribe(audio_path, language=sprache)
    return result["text"].strip()

if __name__ == "__main__":
    check_ffmpeg()

    print("🌍 Wähle eine Sprache:")
    for code, name in SPRACHEN.items():
        print(f"  [{code}] {name}")

    sprache = input("➡️ Sprache eingeben (de/en/ar/fa): ").strip().lower()

    if sprache not in SPRACHEN:
        print("❌ Ungültige Sprache. Bitte nur de, en, ar oder fa eingeben.")
        sys.exit(1)

    try:
        text = sprache_zu_text_einmal(sprache)
        print("📝 Erkannter Text:", text)
    except Exception as e:
        print("❌ Fehler:", e)
