
from llm.jan import JanLLM
from llm.openai import OpenAILLM
from llm.gemini import GeminiLLM
from llm.gemini_remote_history import GeminiRemoteHistoryLLM
from llm.ollama import OllamaLLM
from llm.nvidia import NvidiaLLM

class LLMFactory:

    @classmethod
    def create(cls):
        #return JanLLM()
        return OpenAILLM()
        #return GeminiLLM()
        #return GeminiRemoteHistoryLLM()
        #return OllamaLLM()
        return NvidiaLLM()

