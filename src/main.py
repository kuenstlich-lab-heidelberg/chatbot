from stt.whisper_local import WhisperLocal
from stt.whisper_openai import WhisperOpenAi

from llm.jan import JanLLM
from llm.openai import OpenAILLM

from tts.openai import OpenAiTTS
from tts.coqui import CoquiTTS
from tts.pytts import PyTTS

from personas.greek import PERSONA as greek
from personas.lilly import PERSONA as lilly
from personas.mannheimer import PERSONA as mannheimer
import torch

from dotenv import load_dotenv
load_dotenv() 


if __name__ == '__main__':

    def stop_speak():
        tts.stop()

    def process_text(text):
        print("")
        print(text)
        tts.stop()
        response = llm.chat(text)
        tts.speak(response)



    #llm = JanLLM()
    llm = OpenAILLM(greek)

    tts = OpenAiTTS()
    #tts = CoquiTTS()
    #tts = PyTTS()

    #stt = WhisperLocal(on_speech_start=stop_speak)
    stt = WhisperOpenAi(on_speech_start=stop_speak)


    # Start recording
    # Use the generator to get transcribed text
    for text in stt.start_recording():
        process_text(text)

