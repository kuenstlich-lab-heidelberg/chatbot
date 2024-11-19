from llm.openai import OpenAILLM
from llm.gemini import GeminiLLM
from llm.gemini_remote_history import GeminiRemoteHistoryLLM

class LLMFactory:

    @classmethod
    def create(cls):
        return OpenAILLM()
        #return GeminiLLM()
        #return GeminiRemoteHistoryLLM()

