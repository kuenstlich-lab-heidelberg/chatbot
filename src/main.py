import json
import sys 
import signal

from stt.whisper_local import WhisperLocal
from stt.whisper_openai import WhisperOpenAi
from stt.cli_text import CLIText

from llm.jan import JanLLM
from llm.openai import OpenAILLM
from llm.gemini import GeminiLLM
from llm.gemini_remote_history import GeminiRemoteHistoryLLM

from tts.openai import OpenAiTTS
from tts.coqui import CoquiTTS
from tts.pytts import PyTTS
from tts.console import Console
from tts.piper import PiperTTS
from tts.google import GoogleTTS

from motorcontroller.mock import MotorControlerMock

from sound.jukebox import Jukebox

from personas.state_engine import Persona

from dotenv import load_dotenv
load_dotenv() 


jukebox = Jukebox()
controller = MotorControlerMock()

conversation_dir = "/Users/D023280/Documents/workspace/künstlich-lab/editor/src/conversations/"
conversation_file = "zork.yaml"
conversation_path = f"{conversation_dir}{conversation_file}"

last_action = ""
last_state = ""
stop_requested = False

# Stop function to handle cleanup
def stop():
    global stop_requested
    stop_requested = True
    print("\nStopping gracefully...")
    tts.stop()
    jukebox.stop_all()
    controller.stop()
    sys.exit(0)

# Handle Ctrl+C to call stop function
signal.signal(signal.SIGINT, lambda sig, frame: stop())


if __name__ == '__main__':
    allowed_expressions = ["friendly smile", "thoughtful nod", "surprised look", "serious expression"]

    def on_transition_fired(state, action, metadata_transition, metadata_state):
        global last_action, last_state

        if last_state != state:
            llm.system(metadata_state.get('system_prompt'))
            jukebox.stop_all()
            value = metadata_state.get("ambient_sound")
            if value and value.strip():
                jukebox.play_sound(f"{conversation_dir}{value}")

        if last_action != action:
            llm.system(metadata_transition.get('system_prompt'))
            value = metadata_transition.get("sound_effect")
            if value and value.strip():
                jukebox.play_sound(f"{conversation_dir}{value}", False)

        last_action = action
        last_state = state


    persona = Persona(conversation_path, on_transition_fired)


    def process_text(text):
        print("=====================================================================================================")
        if text == "debug":
            llm.dump()
            return
        
        if(len(text)>0):
            tts.stop()
            response = llm.chat(text, allowed_expressions=allowed_expressions)
            action = response.get("action") 
            if action:
                done = persona.trigger(action)
                if done:
                    controller.set(response["expressions"], persona.get_inventory() )
                    tts.speak(response["text"])
                    llm.system(persona.get_action_system_prompt(action))
                else:
                    # generate a negative answer to the last tried transition
                    text = """
                    Die letze Aktion hat leider nicht geklappt. Unten ist der Grund dafür. Schreibe den Benutzer 
                    eine der Situation angepasste Antwort, so, dass die Gesamtstory und experience nicht kaputt geht. 
                    Schreibe diese direkt raus und vermeide sowas wie 'Hier ist die Antort' oder so...
                    Hier ist der Fehler den wir vom Sytem erhalten haben:

                    """+persona.last_transition_error
                    response = llm.chat(text, allowed_expressions=allowed_expressions)
                    controller.set(response["expressions"], persona.get_inventory() )
                    tts.speak(response["text"])
            else:
                controller.set(response["expressions"], persona.get_inventory() )
                tts.speak(response["text"])


    # Choose between diffeent LLM. All of them has differrent behaviours and different "character"
    #
    #llm = JanLLM()
    llm = OpenAILLM(persona)
    #llm = GeminiLLM(persona)
    #llm = GeminiRemoteHistoryLLM(persona)

    # Choose the voice you like by budget and sounding
    #
    #tts = OpenAiTTS()
    #tts = CoquiTTS()
    #tts = PyTTS()
    #tts = Console()
    #tts = PiperTTS()
    tts = GoogleTTS()

    # Differnet STT (speech to text) implementation. On CUDA computer we can use the WisperLocal without
    # any latence....absolute amazing
    #
    #stt = WhisperLocal()
    #stt = WhisperOpenAi()
    stt = CLIText()

    persona.trigger("start")
    process_text("Erkläre mir worum es hier geht und wer du bist")
    controller.set([], persona.get_inventory())


    try:
        for text in stt.start_recording():
            if stop_requested:
                break
            process_text(text)
    except Exception as e:
        print(f"An error occurred: {e}")
        stop()