import pyttsx3
from tts.base import BaseTTS

# Definition of JanTTS class inheriting from BaseTTS
class PyTTS(BaseTTS):
    def __init__(self):
        super().__init__()
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)  # Setting speech rate
        self.engine.setProperty('volume', 1.0)  # Setting volume level (0.0 to 1.0)


    def speak(self, text):
        print("PyTTS: "+text)
        self.engine.say(text)
        self.engine.runAndWait()

    def stop(self):
        print("PyTTS: stop")
        self.engine.stop()
        pass