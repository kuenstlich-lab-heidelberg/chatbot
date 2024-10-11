import openai
from openai import OpenAI

import abc
import tiktoken
import os

from llm.base import BaseLLM

# Definition der Klasse OpenAILLM, die von BaseLLM erbt
class OpenAILLM(BaseLLM):
    def __init__(self, persona):
        super().__init__()
        self.model = "gpt-3.5-turbo"
        self.history = [
            {
                "role": "system", 
                "content": persona
            }
        ]
        self.max_tokens = 2048
        self.stop = None
        self.frequency_penalty = 0
        self.presence_penalty = 0
        self.temperature = 0.2
        self.top_p = 0.95
        self.token_limit = 4000  # Token-Limit für den Kontext, einschließlich der Systemaufforderung
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)


    def count_tokens(self, messages):
        return sum(len(self.tokenizer.encode(message["content"])) for message in messages)

    def trim_history(self):
        # Sicherstellen, dass der Verlauf das Token-Limit nicht überschreitet
        token_count_before = self.count_tokens(self.history)
        print(token_count_before)
        while self.count_tokens(self.history) > self.token_limit:
            # Entferne die älteste Nachricht, aber behalte die Systemnachricht
            if len(self.history) > 1:
                self.history.pop(1)
            else:
                break
        token_count_after = self.count_tokens(self.history)
        if token_count_before != token_count_after:
            print(f"History trimmed: Token count before = {token_count_before}, Token count after = {token_count_after}")

    def create_chat_completion(self, messages):
        try:
            response = self.client.chat.completions.create(model=self.model,
                        messages=messages,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                        top_p=self.top_p,
                        frequency_penalty=self.frequency_penalty,
                        presence_penalty=self.presence_penalty)
            return response
        except openai.OpenAIError as e:
            print(f"Error: {e}")
            return None

    def chat(self, user_input):
        # Füge Benutzereingabe zum Verlauf hinzu
        self.history.append({"role": "user", "content": user_input})

        # Trim Verlauf, um innerhalb des Token-Limits zu bleiben
        self.trim_history()

        # Erstelle Chat-Vervollständigung mit dem aktualisierten Verlauf
        result = self.create_chat_completion(messages=self.history)

        if result and hasattr(result, 'choices') and len(result.choices) > 0:
            content = result.choices[0].message.content
            # Füge die Antwort zum Verlauf hinzu
            self.history.append({"role": "assistant", "content": content})
            return content
        else:
            return "I'm sorry, there was an issue processing your request."

