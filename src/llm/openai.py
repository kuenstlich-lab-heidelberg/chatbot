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
        self.token_limit = 4000  # Token-Limit für den Kontext, einschließlich der Systemaufforderung
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)


    def count_tokens(self, messages):
        return sum(len(self.tokenizer.encode(message["content"])) for message in messages)


    def trim_history(self):
        # Sicherstellen, dass der Verlauf das Token-Limit nicht überschreitet
        token_count_before = self.count_tokens(self.history)
        while self.count_tokens(self.history) > self.token_limit:
            # Entferne die älteste Nachricht, aber behalte die Systemnachricht
            if len(self.history) > 1:
                self.history.pop(1)
            else:
                break
        token_count_after = self.count_tokens(self.history)
        if token_count_before != token_count_after:
            print(f"History trimmed: Token count before = {token_count_before}, Token count after = {token_count_after}")


    def system(self, system_instruction):
        """
        Add a System Prompt for the next call to trim of fit the LLM for the next chat conversation

        """
        self.history.append({"role": "system", "content": system_instruction})


    def chat(self, user_input, allowed_expressions):
        # Füge Benutzereingabe zum Verlauf hinzu
        self.history.append({"role": "user", "content": user_input})

        # Anweisung, nur die erlaubten Ausdrücke zu verwenden
        allowed_expressions_str = ', '.join(f'"{expr}"' for expr in allowed_expressions)
        system_instruction = f"Please generate text with multiple appropriate emotions or gestures, but only use the following expressions: {allowed_expressions_str}. Ensure there are multiple expressions that are aligned with the flow of the conversation."
        self.history.append({"role": "system", "content": system_instruction})

        # Anweisung zur Auswahl einer Stimmungsänderung
        possible_mood_triggers = self.persona.get_possible_triggers()  # hole mögliche Stimmungsänderungen
        allowed_triggers_str = ', '.join(f'"{trigger}"' for trigger in possible_mood_triggers)
        mood_system_instruction = f"Based on the conversation tone, you can change the mood using one of the following: {allowed_triggers_str}. If the tone is negative or inappropriate, please change the mood accordingly."
        self.history.append({"role": "system", "content": mood_system_instruction})

        # Trim Verlauf, um innerhalb des Token-Limits zu bleiben
        self.trim_history()

        # Combined Function Definition for text, expressions, and mood trigger
        functions = [
            {
                "name": "generate_text_with_expressions_and_mood",
                "description": "Generates text with multiple appropriate emotions and gestures, and optionally triggers a mood transition.",
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
                        "mood_trigger": {
                            "type": "string",
                            "description": "The trigger to switch the mood, chosen from the allowed triggers."
                        }
                    },
                    "required": ["text"]
                }
            }
        ]

        # Erstelle Chat-Vervollständigung mit Function Calling
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

                # Wenn es einen function_call gibt
                if message and message.function_call:
                    function_call = message.function_call
                    function_name = function_call.name
                    function_args = function_call.arguments

                    # Handle text, expressions, and mood trigger together
                    if function_name == "generate_text_with_expressions_and_mood":
                        try:
                            args = json.loads(function_args)
                            text = args.get("text", "")
                            expressions = args.get("expressions", [])
                            
                            # Ensure there are multiple expressions
                            if len(expressions) <= 1:
                                print("Warning: Only one or no expression provided. Ensure multiple expressions.")
                            
                            trigger = args.get("mood_trigger")
                            if trigger not in possible_mood_triggers:
                                trigger = None
                        except json.JSONDecodeError:
                            print("Error parsing function arguments.")
                
                # Falls keine function_call vorhanden ist
                elif message and message.content:
                    text = message.content  # Direkte Antwort vom Assistenten ohne Funktionsaufruf

            # Sicherstellen, dass wir immer einen Text zurückgeben
            if not text:
                print(json.dumps(make_serializable(message), indent=4))
                text = "I'm sorry, there was an issue processing your request."

        except openai.OpenAIError as e:
            print(f"Error: {e}")
            text = "I'm sorry, there was an issue processing your request."

        return {"text": text, "expressions": expressions, "trigger": trigger}
