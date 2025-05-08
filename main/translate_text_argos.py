import argostranslate.package
import argostranslate.translate
from gpiozero import Button
from signal import pause
import os
import subprocess
import time

SOURCE_BUTTON_PIN = 20  # button3 to select source language
TARGET_BUTTON_PIN = 21  # button4 to select target language or long press>1s to translate

language_codes = ['en', 'de', 'zh']

# Audio confirmation files 
audio_map = {
    'en': os.path.join(os.path.dirname(__file__), '../languages/en.wav'),
    'de': os.path.join(os.path.dirname(__file__), '../languages/de.wav'),
    'zh': os.path.join(os.path.dirname(__file__), '../languages/zh.wav')
}

# Setup buttons
source_button = Button(SOURCE_BUTTON_PIN)
target_button = Button(TARGET_BUTTON_PIN)

# State variables
source_index = 0
target_index = 0
press_time = None
selected_langs = {
    'source': None,
    'target': None
}

def play_audio(lang_code):
    path = audio_map.get(lang_code)
    if path and os.path.exists(path):
        print(f"Playing audio: {path}")
        subprocess.run(['aplay', "-D", "plughw:CARD=Device,DEV=0", path])  # Use USB speaker to play Audio confirmation files 
    else:
        print(f"Audio file not found: {path}")

def select_source():
    global source_index
    source_index = (source_index + 1) % len(language_codes)
    lang = language_codes[source_index]
    selected_langs['source'] = lang
    print(f"Selected source language: {lang}")
    play_audio(lang)

def select_target():
    global target_index
    target_index = (target_index + 1) % len(language_codes)
    lang = language_codes[target_index]
    selected_langs['target'] = lang
    print(f"Selected target language: {lang}")
    play_audio(lang)

def translate_text(source_lang_code, target_lang_code, text):
    installed_languages = argostranslate.translate.get_installed_languages()
    from_lang = next((lang for lang in installed_languages if lang.code == source_lang_code), None)
    to_lang = next((lang for lang in installed_languages if lang.code == target_lang_code), None)

    if not from_lang or not to_lang:
        return f"Error: Languages '{source_lang_code}' to '{target_lang_code}' not available."

    translation = from_lang.get_translation(to_lang)
    return translation.translate(text)

def manual_translate():
    source = selected_langs['source']
    target = selected_langs['target']
    if not source or not target:
        print("Source and target languages must both be selected before translating.")
        return
    if source == target:
        print("Source and target languages must be different.")
        return
    print("Ready to translate. Please type text to translate:")
    text = input("Text: ").strip()
    translated = translate_text(source, target, text)
    print("\nTranslated Text:")
    print(translated)

def target_button_pressed():
    global press_time
    press_time = time.time()

def target_button_released():
    global press_time
    duration = time.time() - press_time
    if duration >= 1.0:
        print("Long press detected → running translation")
        manual_translate()
    else:
        print("Short press detected → switching target")
        select_target()

print("Press Button3 to select source language (en/de/zh), changes on every press.")
print("Press Button4 to select target language (short press), or hold >1s to translate.")

source_button.when_pressed = select_source
target_button.when_pressed = target_button_pressed
target_button.when_released = target_button_released

pause()
