
import sys 
import signal

from dotenv import load_dotenv
load_dotenv() 

from motorcontroller.mock import MotorControlerMock

from state_engine import StateEngine
from tts.factory import TTSEngineFactory
from llm.factory import LLMFactory
from stt.factory import STTFactory
from session import Session
from sound.local_jukebox import LocalJukebox
from audio.pyaudio import PyAudioSink

debug_ui = MotorControlerMock()

conversation_dir = "/Users/D023280/Documents/workspace/künstlich-lab/editor/src/conversations/"
conversation_file = "zork.yaml"
conversation_file = "fsm.yaml"

stop_requested = False


def stop():
    global stop_requested
    print("\nStopping gracefully...")
    stop_requested = True
    debug_ui.stop()
    sys.exit(0)
signal.signal(signal.SIGINT, lambda sig, frame: stop())



if __name__ == '__main__':

    def process_text(session, text):

        print("=====================================================================================================")
        if text.lower() == "debug":
            session.llm.dump()
            return
        if text.lower() == "reset":
            session.llm.reset()
            return
        
        if len(text)>0:
            response = session.llm.chat(session,text)
            action = response.get("action") 
            session.tts.stop(session)
            if action:
                done = session.state_engine.trigger(session, action)
                if done:
                    debug_ui.set(response["expressions"], session.state_engine.get_inventory() )
                    session.tts.speak(session, response["text"])
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
                    debug_ui.set(response["expressions"], session.state_engine.get_inventory() )
                    session.tts.speak(session, response["text"])
            else:
                debug_ui.set(response["expressions"], session.state_engine.get_inventory() )
                session.tts.speak(session, response["text"])


    session = Session(
        conversation_dir = conversation_dir,
        state_engine=StateEngine(f"{conversation_dir}{conversation_file}"),
        llm = LLMFactory.create(),
        tts = TTSEngineFactory.create(PyAudioSink()),
        stt = STTFactory.create(),
        jukebox = LocalJukebox()
    )

    # Start the game for this new session
    #
    session.state_engine.trigger(session, "start")
    process_text(session, "Erkläre mir in kurzen Worten worum es hier geht und wer du bist")
    
    # show the current status of the game
    #
    debug_ui.set([], session.state_engine.get_inventory())

    try:
        for text in session.stt.start_recording():
            if stop_requested:
                break
            process_text(session, text)
    except Exception as e:
        print(f"An error occurred: {e}")
        stop()