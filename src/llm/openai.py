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
        return str(obj)  # Fallback: Convert any non-serializable objects to their string representation


# Definition der Klasse OpenAILLM, die von BaseLLM erbt
class OpenAILLM(BaseLLM):
    def __init__(self, persona):
        super().__init__()
        self.persona = persona
        self.model = "gpt-4"
        self.history = [
            {
                "role": "system", 
                "content": self.persona.get_system_prompt()
            }
        ]
        self.max_tokens = 2048
        self.stop = None
        self.frequency_penalty = 0
        self.presence_penalty = 0
        self.temperature = 0.2
        self.top_p = 0.95
        self.token_limit = 4000 
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)


    def count_tokens(self, messages):
        return sum(len(self.tokenizer.encode(message["content"])) for message in messages)


    def trim_history(self):
        token_count_before = self.count_tokens(self.history)
        while self.count_tokens(self.history) > self.token_limit:
            if len(self.history) > 1:
                self.history.pop(1)
            else:
                break
        token_count_after = self.count_tokens(self.history)
        if token_count_before != token_count_after:
            print(f"History trimmed: Token count before = {token_count_before}, Token count after = {token_count_after}")


    def system(self, system_instruction):
        self.history.append({"role": "system", "content": system_instruction})


    def chat(self, user_input, allowed_expressions):
        # Append user input to the history
        self.history.append({"role": "user", "content": user_input})

        # Instruct the LLM to use only allowed expressions
        allowed_expressions_str = ', '.join(f'"{expr}"' for expr in allowed_expressions)
        system_instruction = f"Please generate text with multiple appropriate emotions or gestures, but only use the following expressions: {allowed_expressions_str}. Ensure there are multiple expressions that are aligned with the flow of the conversation."
        self.history.append({"role": "system", "content": system_instruction})

        # Instruct the LLM to decide on a generic action trigger based on the context
        possible_triggers = self.persona.get_possible_triggers()  # fetch available triggers
        allowed_triggers_str = ', '.join(f'"{trigger}"' for trigger in possible_triggers)
        trigger_system_instruction = f"Based on the conversation context or user commands, select the most appropriate action trigger from the following: {allowed_triggers_str}. These triggers could be actions or changes in the conversation. Choose accordingly."
        self.history.append({"role": "system", "content": trigger_system_instruction})

        # Trim the conversation history to stay within the token limit
        self.trim_history()

        # Function definitions for handling text, expressions, and triggers
        functions = [
            {
                "name": "generate_text_with_expressions_and_trigger",
                "description": "Generates text with multiple appropriate emotions and gestures, and optionally triggers an action or state transition.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to be spoken."
                        },
                        "expressions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "expression": {
                                        "type": "string",
                                        "description": "Emotion or gesture to be performed. Ensure multiple expressions are used."
                                    },
                                    "start_time": {
                                        "type": "number",
                                        "description": "Time in seconds when the gesture should be performed."
                                    }
                                },
                                "required": ["expression", "start_time"]
                            }
                        },
                        "trigger": {
                            "type": "string",
                            "description": "The action or state transition trigger, chosen from the allowed triggers."
                        }
                    },
                    "required": ["text"]
                }
            }
        ]

        # Call the LLM API with the function definitions
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.history,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                frequency_penalty=self.frequency_penalty,
                presence_penalty=self.presence_penalty,
                functions=functions,
            )

            text = ""
            expressions = []
            trigger = None

            # Process the LLM response
            if response and len(response.choices) > 0:
                choice = response.choices[0]
                message = choice.message
                #print(json.dumps(make_serializable(message), indent=4))
                # Handle function calls if they exist
                if message and message.function_call:
                    function_call = message.function_call
                    function_name = function_call.name
                    function_args = function_call.arguments

                    # Handle the combined generation of text, expressions, and action trigger
                    if function_name == "generate_text_with_expressions_and_trigger":
                        try:
                            args = json.loads(function_args)
                            text = args.get("text", "")
                            expressions = args.get("expressions", [])
                            
                            # Ensure there are multiple expressions
                            if len(expressions) <= 1:
                                print("Warning: Only one or no expression provided. Ensure multiple expressions.")
                            
                            trigger = args.get("trigger")
                            if trigger not in possible_triggers:
                                trigger = None
                        except json.JSONDecodeError:
                            print("Error parsing function arguments.")

                    # Handle the dynamic trigger selection based on user input and context
                    elif function_name == "choose_trigger_based_on_context":
                        try:
                            args = json.loads(function_args)
                            trigger = args.get("trigger")
                            if trigger not in possible_triggers:
                                trigger = None
                        except json.JSONDecodeError:
                            print("Error parsing function arguments.")

                # Handle direct responses without function calls
                elif message and message.content:
                    text = message.content

            # Ensure we always return some text and the expressions
            if not text:
                print(json.dumps(make_serializable(message), indent=4))
                text = "I'm sorry, there was an issue processing your request."

        except openai.OpenAIError as e:
            print(f"Error: {e}")
            text = "I'm sorry, there was an issue processing your request."

        return {"text": text, "expressions": expressions, "trigger": trigger}
