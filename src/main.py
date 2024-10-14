from stt.large_stt import LargeSTT
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
    # Check that MPS is available
    if not torch.backends.mps.is_available():
        if not torch.backends.mps.is_built():
            print("MPS not available because the current PyTorch install was not "
                "built with MPS enabled.")
        else:
            print("MPS not available because the current MacOS version is not 12.3+ "
                "and/or you do not have an MPS-enabled device on this machine.")
    else:
        print("MPS support for pytorch is available")


    #llm = JanLLM()
    llm = OpenAILLM(greek)

    tts = OpenAiTTS()
    #tts = CoquiTTS()
    #tts = PyTTS()

    def stop_speak():
        tts.stop()

    def process_text(text):
        print("")
        print(text)
        tts.stop()
        response = llm.chat(text)
        tts.speak(response)

    # Instantiate LargeSTT with language, model, and callback
    stt_instance = LargeSTT(speech_started=stop_speak)
    # Start recording
    # Use the generator to get transcribed text
    for text in stt_instance.start_recording():
        process_text(text)

