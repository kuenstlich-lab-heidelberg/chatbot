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

    #persona = Persona("default.yaml", on_transition_fired)
    #persona = Persona("/Users/D023280/Documents/workspace/künstlich-lab/editor/src/conversations/document.yaml", on_transition_fired)
    persona = Persona("/Users/D023280/Documents/workspace/künstlich-lab/editor/src/conversations/zork.yaml", on_transition_fired)


    def process_text(text):
        print("")
        print(text)
        if(len(text)>0):
            tts.stop()
            response = llm.chat(text, allowed_expressions=allowed_expressions)

            trigger = response.get("trigger") 
            if trigger:
                done = persona.trigger(trigger)
                if done:
                    tts.speak(response["text"])
                    llm.system(persona.get_trigger_system_prompt(trigger))
                else:
                    # generate a negative answer to the last tried transition
                    text = """
                    Die letze Aktion hat leider nicht geklappt. Unten ist der Grund dafür. Schreibe den Benutzer 
                    eine der Situation angepasste Antwort, so, dass die Gesamtstory und experience nicht kaputt geht. 
                    Schreibe diese direkt raus und vermeide sowas wie 'Hier ist die Antort' oder so...
                    Hier ist der Fehler den wir vom Sytem erhalten haben:

                    """+persona.last_transition_error
                    response = llm.chat(text, allowed_expressions=allowed_expressions)
                    tts.speak(response["text"])
            else:
                tts.speak(response["text"])

            response["state"] = persona.get_state()
            print(json.dumps(response, indent=4))

    #llm = JanLLM()
    llm = OpenAILLM(persona)

    tts = OpenAiTTS()
    #tts = CoquiTTS()
    #tts = PyTTS()
    #tts = Console()

    #stt = WhisperLocal()
    #stt = WhisperOpenAi()
    stt = CLIText()

    # Process incomming text from the user one by one
    for text in stt.start_recording():
        process_text(text)

