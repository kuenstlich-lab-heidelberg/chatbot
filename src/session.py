


class Session():
    def __init__(self, state_engine, llm, tts, stt):
        self.state_engine = state_engine
        self.llm = llm
        self.tts= tts
        self.stt = stt
        self.last_action = ""
        self.last_state = ""

