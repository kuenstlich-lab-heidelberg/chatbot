import openai
from openai import OpenAI
import json

import tiktoken
import os

from llm.base import BaseLLM

def make_serializable(obj):
    """Convert an object to a form that is JSON serializable."""
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_serializable(i) for i in obj]
    elif hasattr(obj, '__dict__'):
        return make_serializable(vars(obj))
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        return str(obj)


# Definition der Klasse OpenAILLM, die von BaseLLM erbt
class OpenAILLM(BaseLLM):
    def __init__(self):
        super().__init__()
        #self.model = "gpt-4"
        self.model = "gpt-3.5-turbo"
        #self.model = "gpt-4o-mini"
        #self.model = "gpt-4o"

        self.history = []
        self.max_tokens = 2048
        self.stop = None
        self.frequency_penalty = 0
        self.presence_penalty = 0
        self.temperature = 0.1
        self.top_p = 0.95
        self.token_limit = 4000 
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API key for OpenAI not found in environment variables.")
     
        self.client = OpenAI(api_key=self.api_key)


    def dump(self):
        print(json.dumps(self.history, indent=4))


    def reset(self, session):
        self.history = []


    def system(self, system_instruction):
        if system_instruction:
            self._add_to_history("system", system_instruction)
        else:
            print("Warning: No system instruction provided.")


    def _add_to_history(self, role, message):
        if not message:
            print("Warning: No message provided.")
            return
        
        if self.history and self.history[-1]["role"] == role and self.history[-1]["content"] == message:
            print("Duplicate message detected; not adding to history.")
            return
        
        self.history.append({"role": role, "content": message})


    def chat(self, session, user_input):
        if not user_input:
            return {"text": "No input provided.", "expressions": [], "action": None}
        self._add_to_history("user", user_input)
        self._trim_history()

        response = self._call_openai_model(session)
        response["text"] =  response["text"].replace("Was möchtest du als nächstes tun?", "")

        self._add_to_history("assistant", response["text"])
        return response
    

    def _call_openai_model(self, session):
        combined_history = [
            {"role": "system", "content": session.system_prompt},
        ] + self.history

        text ="?"
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=combined_history,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
            )

            if response and response.choices:
                choice = response.choices[0].message
                text = choice.content

        except openai.OpenAIError as e:
            print(f"Error: {e}")
            return {"text": "I'm sorry, there was an issue processing your request.", "expressions": [], "action": None}
        return {"text": text}


    def _trim_history(self):
        while self._count_tokens(self.history) > self.token_limit:
            if len(self.history) > 1:
                self.history.pop(0)
            else:
                break

    def _count_tokens(self, messages):
        return sum(len(self.tokenizer.encode(message["content"])) for message in messages)