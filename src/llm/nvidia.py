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
class NvidiaLLM(BaseLLM):
    def __init__(self):
        super().__init__()
        self.model = "meta/llama-3.1-70b-instruct"

        self.history = []
        self.max_tokens = 2048
        self.stop = None
        self.frequency_penalty = 0
        self.presence_penalty = 0
        self.temperature = 0.1
        self.top_p = 0.95
        self.token_limit = 4000 
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        self.api_key = os.getenv("NVIDIA_API_KEY")
        if not self.api_key:
            raise ValueError("API key for OpenAI not found in environment variables.")
     
        self.client = OpenAI(
            api_key=self.api_key,
            base_url = "https://integrate.api.nvidia.com/v1"
        )


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
        if (response["text"] is None or response["text"].strip() == "") and response["action"]:
            response = self._retry_for_text(session, response)
        response["text"] =  response["text"].replace("Was möchtest du als nächstes tun?", "")

        self._add_to_history("assistant", response["text"])
        return response
    

    def _call_openai_model(self, session):
        combined_history = [
            {"role": "system", "content": session.state_engine.get_global_system_prompt()},
            {"role": "system", "content": self._possible_actions_instruction(session)}
        ] + self.history

        functions = self._define_action_functions(session)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=combined_history,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                tools=functions,
                  tool_choice="auto",
            )
            return self._process_response(response)
        except openai.OpenAIError as e:
            print(f"Error: {e}")
            return {"text": "I'm sorry, there was an issue processing your request.", "expressions": [], "action": None}


    def _define_action_functions(self, session):
        print(json.dumps(session.state_engine.get_possible_actions(), indent=4))
        return [
            {
                "type": "function",  # Add this top-level type key
                "function": {  # Nest the actual function details here
                    "name": action,
                    "description": session.state_engine.get_action_description(action),
                    "parameters": {
                        "type": "object",
                        "properties": {},  # Define properties if needed
                        "required": []  # Define any required fields if necessary
                    }
                }
            }
            for action in session.state_engine.get_possible_actions()
        ]


    def _possible_actions_instruction(self, session):
        possible_actions = session.state_engine.get_possible_actions()
        possible_actions_str = ', '.join(f'"{action}"' for action in possible_actions)
        return f"Available actions: [{possible_actions_str}]"


    def _process_response(self, response):
        text, action = "", None
        if response and response.choices:
            choice = response.choices[0].message
            if choice.function_call:
                action = choice.function_call.name
            elif choice.content:
                text = choice.content
        return {"text": text, "expressions":[], "action": action}


    def _retry_for_text(self, session, initial_response):
        action = initial_response["action"]
        if action in session.state_engine.get_possible_actions():
            # Instruct the model to respond as if the action was successful
            self.system(f"""
                Respond as if the action '{action}' was executed successfully. 
                Do not reveal any internal details to the user.
            """)
        else:
            # If the action is not valid, we clear it to avoid returning an incorrect action
            action = None

        # Retry without requesting a function call, focusing on obtaining a text response
        second_response = self._call_openai_model(session)

        # Preserve the original action and update only the text
        initial_response["text"] = second_response["text"]
        initial_response["action"] = action  # Ensure the action from the first response is kept

        return initial_response


    def _trim_history(self):
        while self._count_tokens(self.history) > self.token_limit:
            if len(self.history) > 1:
                self.history.pop(0)
            else:
                break

    def _count_tokens(self, messages):
        return sum(len(self.tokenizer.encode(message["content"])) for message in messages)