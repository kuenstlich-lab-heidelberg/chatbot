
from sound.jukebox import Jukebox

class Session():
    def __init__(self, conversation_dir, state_engine, llm, tts, stt):
        self.conversation_dir = conversation_dir
        self.state_engine = state_engine
        self.llm = llm
        self.tts= tts
        self.stt = stt
        self.last_action = ""
        self.last_state = ""
        self.jukebox = Jukebox(conversation_dir)

