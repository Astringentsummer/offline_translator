from TTS.api import TTS
import simpleaudio as sa
import os


tts = TTS(model_name="tts_models/de/thorsten/tacotron2-DDC", progress_bar=False, gpu=False)

if __name__ == "__main__":
    while True:
        myText = input("Enter the German text you want to hear: ")
        if myText.lower() == "bye":
            print("Goodbye!")
            break

        file_path = "speech.wav"
        tts.tts_to_file(text=myText, file_path=file_path)

        # Play the audio safely using simpleaudio
        wave_obj = sa.WaveObject.from_wave_file(file_path)
        play_obj = wave_obj.play()
        play_obj.wait_done()

        # Delete the file after playback
        os.remove(file_path)
