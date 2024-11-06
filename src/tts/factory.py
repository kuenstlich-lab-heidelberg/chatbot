from tts.openai import OpenAiTTS
from tts.coqui import CoquiTTS
from tts.pytts import PyTTS
from tts.console import Console
from tts.piper import PiperTTS
from tts.google import GoogleTTS

class TTSEngineFactory:

    @classmethod
    def create(cls, audio_sink):
        #return OpenAiTTS(audio_sink)
        #return CoquiTTS(audio_sink)
        #return PyTTS(audio_sink)
        #return Console(audio_sink)
        #return PiperTTS(audio_sink)
        return GoogleTTS(audio_sink)
