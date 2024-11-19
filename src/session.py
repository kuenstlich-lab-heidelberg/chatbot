

class Session():
    def __init__(self, llm, tts, stt, system_prompt="Du bist ein netter, albener Chatbot", ws_token = None):
        self.llm = llm
        self.tts= tts
        self.stt = stt
        self.ws_token = ws_token
        self.system_prompt = system_prompt
        self.scheduled_tasks = [] 
