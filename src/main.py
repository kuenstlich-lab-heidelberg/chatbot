
import sys 
import signal

from dotenv import load_dotenv
load_dotenv() 

from motorcontroller.mock import MotorControlerMock
from sound.jukebox import Jukebox
from state_engine import StateEngine
from audio.factory import AudioSinkFactory
from tts.factory import TTSEngineFactory
from llm.factory import LLMFactory
from stt.factory import STTFactory
from session import Session


jukebox = Jukebox()
controller = MotorControlerMock()
conversation_dir = "/Users/D023280/Documents/workspace/künstlich-lab/editor/src/conversations/"
conversation_file = "zork.yaml"
conversation_path = f"{conversation_dir}{conversation_file}"
allowed_expressions = ["friendly smile", "thoughtful nod", "surprised look", "serious expression"]
stop_requested = False


def stop():
    global stop_requested
    stop_requested = True
    print("\nStopping gracefully...")
    jukebox.stop_all()
    controller.stop()
    sys.exit(0)
signal.signal(signal.SIGINT, lambda sig, frame: stop())



if __name__ == '__main__':

    def on_transition_fired(session, state, metadata_state, action, metadata_action):

        if session.last_state != state:
            session.llm.system(metadata_state.get('system_prompt'))
            jukebox.stop_all()
            value = metadata_state.get("ambient_sound")
            if value and value.strip():
                jukebox.play_sound(f"{conversation_dir}{value}")

        if session.last_action != action:
            session.llm.system(metadata_action.get('system_prompt'))
            value = metadata_action.get("sound_effect")
            if value and value.strip():
                jukebox.play_sound(f"{conversation_dir}{value}", False)

        session.last_action = action
        session.last_state = state

    def process_text(session, text):

        print("=====================================================================================================")
        if text.lower() == "debug":
            session.llm.dump()
            return
        if text.lower() == "reset":
            session.llm.reset()
            return
        
        if(len(text)>0):
            response = session.llm.chat(session,text)
            action = response.get("action") 
            session.tts.stop()
            if action:
                done = session.state_engine.trigger(session, action)
                if done:
                    controller.set(response["expressions"], session.state_engine.get_inventory() )
                    session.tts.speak(response["text"])
                    session.llm.system(session.state_engine.get_action_system_prompt(action))
                else:
                    # generate a negative answer to the last tried transition
                    text = """
                    Die letze Aktion hat leider nicht geklappt. Unten ist der Grund dafür. Schreibe den Benutzer 
                    eine der Situation angepasste Antwort, so, dass die Gesamtstory und experience nicht kaputt geht. 
                    Schreibe diese direkt raus und vermeide sowas wie 'Hier ist die Antort' oder so...
                    Hier ist der Fehler den wir vom Sytem erhalten haben:

                    """+session.state_engine.last_transition_error
                    response = session.llm.chat(session, text)
                    controller.set(response["expressions"], session.state_engine.get_inventory() )
                    session.tts.speak(response["text"])
            else:
                controller.set(response["expressions"], session.state_engine.get_inventory() )
                session.tts.speak(response["text"])

    session = Session(
        state_engine=StateEngine(conversation_path, on_transition_fired),
        llm = LLMFactory.create(),
        tts = TTSEngineFactory.create(AudioSinkFactory.create()),
        stt = STTFactory.create()
    )

    session.state_engine.trigger(session, "start")
    process_text(session, "Erkläre mir in kurzen Worten worum es hier geht und wer du bist")
    controller.set([], session.state_engine.get_inventory())

    try:
        for text in session.stt.start_recording():
            if stop_requested:
                break
            process_text(session, text)
    except Exception as e:
        print(f"An error occurred: {e}")
        stop()