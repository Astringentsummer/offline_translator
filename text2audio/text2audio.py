from gtts import gTTS
from playsound import playsound
import os


# def speech(myText, myobj):
   
#    myobj.save("speech.mp3")
#    #    *****Change the path of the mp3 file location*****
#    playsound('D:/GitHub/Tollmatcher/text2audio/speech.mp3')
#    os.remove("speech.mp3")


if __name__ == "__main__":
   
   while True:
      myText = input("Enter the German text you want to hear: ")
      if myText.lower()== "bye":
         print("Goodbye!")
         break
      # We can change the language to any translated language that we want
      language = 'de'  # 'en' for English, 'de' for German, etc.
      output = gTTS(text=myText, lang=language, slow=False)
      
      output.save("speech.mp3")
   #    *****Change the path of the mp3 file location*****
      playsound('D:/GitHub/Tollmatcher/text2audio/speech.mp3')
      os.remove("speech.mp3")
      #speech(myText, output)

