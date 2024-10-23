import json

from stt.whisper_local import WhisperLocal
from stt.whisper_openai import WhisperOpenAi
from stt.cli_text import CLIText

from llm.jan import JanLLM
from llm.openai import OpenAILLM

from tts.openai import OpenAiTTS
from tts.coqui import CoquiTTS
from tts.pytts import PyTTS
from tts.console import Console

from personas.state_engine import Persona

from dotenv import load_dotenv
load_dotenv() 


if __name__ == '__main__':
    allowed_expressions = ["friendly smile", "thoughtful nod", "surprised look", "serious expression"]


    def on_transition_fired(trigger_name, metadata_transition, metadata_state, metadata_model):
        print(f"on_transition_fired: {trigger_name} =================================")
        #print(f"Adjust System prompt: {metadata.get('system_prompt', 'No system prompt')}")
        print("Called Transition Metadata ----------")
        print(json.dumps(metadata_transition, indent=4))
        print("")
        print("New State Metadata ---------------")
        print(json.dumps(metadata_state, indent=4))
        print("")
        print("Model Metadata Inventory---------------")
        print(json.dumps(metadata_model["inventory"], indent=4))
        print("")
        llm.system(metadata_transition.get('system_prompt'))
        llm.system(metadata_state.get('system_prompt'))
        print("==========================================================================\n\n")

    persona = Persona("default.yaml", on_transition_fired)

    def process_text(text):
        print("")
        print(text)
        if(len(text)>0):
            tts.stop()
            response = llm.chat(text, allowed_expressions=allowed_expressions)
            tts.speak(response["text"])
            if "trigger" in response:
                persona.trigger(response["trigger"])
            response["state"] = persona.get_state()
            print(json.dumps(response, indent=4))

    #llm = JanLLM()
    llm = OpenAILLM(persona)

    #tts = OpenAiTTS()
    #tts = CoquiTTS()
    #tts = PyTTS()
    tts = Console()

    #stt = WhisperLocal()
    stt = WhisperOpenAi()
    stt = CLIText()

    # Start recording
    # Use the generator to get transcribed text
    for text in stt.start_recording():
        process_text(text)

