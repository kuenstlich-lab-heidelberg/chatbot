import requests
import json
import abc
import tiktoken

from llm.base import BaseLLM


# Definition of JanLLM class inheriting from BaseLLM
class JanLLM(BaseLLM):
    def __init__(self, persona):
        super().__init__()
        self.model = "llama3.2-3b-instruct"
        #self.model = "llama3.2-1b-instruct"
        self.url = "http://localhost:1337/v1/chat/completions"
        self.history = [
            {
                "role": "system", 
                "content": persona
            }
        ]
        self.stream = False
        self.max_tokens = 2048
        self.stop = None
        self.frequency_penalty = 0
        self.presence_penalty = 0
        self.temperature = 0.2
        self.top_p = 0.95
        self.token_limit = 4000  # Token limit for context, including the system prompt
        self.tokenizer = tiktoken.get_encoding("cl100k_base")


    def count_tokens(self, messages):
        return sum(len(self.tokenizer.encode(message["content"])) for message in messages)
    
    def trim_history(self):
        # Ensure the history does not exceed the token limit
        token_count_before = self.count_tokens(self.history)
        print(token_count_before)
        while self.count_tokens(self.history) > self.token_limit:
            # Remove the oldest message, but keep the system message
            if len(self.history) > 1:
                self.history.pop(1)
            else:
                break
        token_count_after = self.count_tokens(self.history)
        if token_count_before != token_count_after:
            print(f"History trimmed: Token count before = {token_count_before}, Token count after = {token_count_after}")


    def create_chat_completion(self, messages):
        headers = {
            "Content-Type": "application/json",
        }

        payload = {
            "messages": messages,
            "model": self.model,
            "stream": self.stream,
            "max_tokens": self.max_tokens,
            "stop": self.stop,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "temperature": self.temperature,
            "top_p": self.top_p
        }
        print("start")
        response = requests.post(self.url, headers=headers, data=json.dumps(payload))
        print("end")
        return response.json()


    def chat(self, user_input):
        # Add user input to history
        self.history.append({"role": "user", "content": user_input})

        # Trim history to fit within the token limit
        self.trim_history()

        # Create chat completion with the updated history
        result = self.create_chat_completion(messages=self.history)

        # Extract the content from the response
        content = result['choices'][0]['message']['content']
        content = content.replace("<|eot_id|>","")

        # Add the response to the history
        self.history.append({"role": "assistant", "content": content})

        # Return the response content
        return content
