
from llm.jan import JanLLM
from llm.openai import OpenAILLM
from llm.gemini import GeminiLLM
from llm.gemini_remote_history import GeminiRemoteHistoryLLM


class LLMFactory:

    @classmethod
    def create(cls):
        #return JanLLM()
        return OpenAILLM()
        #return GeminiLLM(persona)
        #return GeminiRemoteHistoryLLM(persona)

