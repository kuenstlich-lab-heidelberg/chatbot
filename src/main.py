import os
import sys 
import signal
import json
from dotenv import load_dotenv
load_dotenv() 

from tts.factory import TTSEngineFactory
from llm.factory import LLMFactory
from stt.factory import STTFactory
from session import Session
from audio.pyaudio import PyAudioSink


stop_requested = False


def stop():
    global stop_requested
    print("\nStopping gracefully...")
    stop_requested = True
    sys.exit(0)
signal.signal(signal.SIGINT, lambda sig, frame: stop())


def newSession():
    return Session(
        llm = LLMFactory.create(),
        tts = TTSEngineFactory.create(PyAudioSink()),
        stt = STTFactory.create(),
    )

if __name__ == '__main__':

    def process_text(session, text):

        if text.lower() == "debug":
            session.llm.dump()
            return

        if text.lower() == "reset":
            session.llm.reset(session)
            return
        
        if len(text)>0:
            response = session.llm.chat(session,text)
            print(json.dumps(response, indent=4))

            session.tts.stop(session)
            tts_text = response["text"]
                
            session.tts.speak(session, tts_text)


    session = newSession()

    # Start the game for this new session
    #
    process_text(session, "Erkläre mir in kurzen Worten worum es hier geht und wer du bist")
    
    try:
        for text in session.stt.start_recording():
            if stop_requested:
                break
            process_text(session, text)
    except Exception as e:
        print(f"An error occurred: {e}")
        stop()