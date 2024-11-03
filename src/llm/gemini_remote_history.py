import os
import time
import json
import google.generativeai as genai
from google.generativeai.types import content_types

from llm.base import BaseLLM


class GeminiRemoteHistoryLLM(BaseLLM):
    def __init__(self, persona):
        super().__init__()
        self.persona = persona
        self.model_name = "gemini-1.5-pro"  # stable
        self.generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,  # 64
            "max_output_tokens": 210,
            "response_mime_type": "text/plain",
        }

        self.api_key=os.environ["GEMINI_API_KEY"]
        if not self.api_key:
            raise ValueError("API key 'GEMINI_API_KEY' not found in environment variables.")
        genai.configure(api_key=self.api_key)

        possible_actions_instruction = f"""
            Im Hintergrund wähle ich je nach Gesprächskontext oder auf expliziten Wunsch des Benutzers die 
            passende Funktion aus. Dabei achte ich darauf, dass das Handlungsverb der Aktion semantisch 
            zur Anweisung passt, um Verwechslungen wie „öffne...“ statt „untersuche...“. Verben die semantisch identisch
            sind wie gehen, laufen, rennen oder aufheben, nehmen,...können als identisch und gleichwertig angesehen werden.
            Jede gewählte Aktion soll im Sinne der Absicht des Nutzers ausgeführt werden.

            Wenn keine dieser Funktionen dem Befehl des Nutzers entspricht, fahre ich ohne technische 
            Hinweise oder Rückmeldung ganz normal im Gesprächsverlauf fort, ohne eine Aktion auszuführen.
            Achte drauf dem Benutzer IMMER einen text als zu liefern.
        """
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self.generation_config,
            safety_settings={
                'HATE': 'BLOCK_NONE',
                'HARASSMENT': 'BLOCK_NONE',
                'SEXUAL': 'BLOCK_NONE',
                'DANGEROUS': 'BLOCK_NONE'
            },
            system_instruction=self.persona.get_global_system_prompt()+". "+possible_actions_instruction,
        )
        self.chat_session = self.model.start_chat( enable_automatic_function_calling=False)


    def dump(self):
        print(json.dumps(self.chat_session.history(), indent=4))


    def system(self, system_instruction):
        if system_instruction:
            self.chat_session.send_message("System instruction: "+system_instruction.replace(f'\n', ''))
        else:
            print("Warning: No system instruction provided.")


    def chat(self, user_input, allowed_expressions=[]):
        if not user_input:
            print("Error: No user input provided.")
            return {"text": "No input provided.", "expressions": [], "action": None}

        user_input = user_input.replace(f'\n', '')
        tools = [
            genai.protos.Tool(
                function_declarations=[
                    genai.protos.FunctionDeclaration(
                        name=action,
                        description=self.persona.get_action_description(action),
                        parameters=None
                    )
                ]
            )
            for action in self.persona.get_possible_actions()
        ]
        print(json.dumps(self.persona.get_possible_actions(), indent=4))

        tool_config= content_types.to_tool_config({
            "function_calling_config": {
                "mode": "ANY", 
                "allowed_function_names": self.persona.get_possible_actions()
            }
        })

        # Erster Modellaufruf mit "function_calling_config" auf "ANY" um zu versuchen "action" und "text" zu bekommen
        #
        result = self._get_response_with_config(user_input, tools, tool_config)
        action = result["action"]

        # Falls Gemini nur "action" geliefert hat, dann starten wir einen zweiten Aufruf um uns nur eine "text" Antwort abzuholen.
        # Kann manchmal passieren. AI = fuzzy
        #
        if result["text"] is None:
            print("No text response; retrying with function_calling_config set to 'NONE'.")
            if action in self.persona.get_possible_actions():
                self.system(f"""Antworte so, als ob die Aktion '{result["action"]}' erfolgreich ausgeführt wurde.
                    Achte bitte darauf, dass du so Antwortest, als ob die Aktion erfolgreich war und du 
                    diese ausgeführt hast. Egal welche anderen Annahmen du triffst. Diese information NIEMALS 
                    dem Benutzer zeigen oder zurückliefern
                    """)
            else:
                result["action"] = None

            tool_config= content_types.to_tool_config({
                "function_calling_config": {
                    "mode": "NONE"
                }
            })

            second_result = self._get_response_with_config(user_input, tools, tool_config)

            # Merging der Antworten
            result["text"] = second_result["text"] if result["text"] is None else result["text"]
            if result["action"] is None and second_result["action"] is not None:
                result["action"] = second_result["action"]

        return result


    def _get_response_with_config(self, user_input, tools, tool_config):
        max_retries = 2
        attempt = 0
        
        while attempt <= max_retries:
            try:
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT"        ,"threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH"       ,"threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT" ,"threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT" ,"threshold": "BLOCK_NONE"}
                ]

                response = self.chat_session.send_message(
                    user_input, 
                    tools= tools, 
                    tool_config=tool_config,
                    safety_settings = safety_settings)

                result = {"text": None, "expressions": [], "action": None}

                # Process response parts
                for part in response.parts:
                    if part.text and not result["text"]:
                        result["text"] = part.text
                    if part.function_call and not result["action"]:
                        result["action"] = part.function_call.name

                return result  # Exit the loop and function if successful

            except Exception as e:
                print(e)
                print(json.dumps(self.chat_session.history(), indent=4))
                attempt += 1
                if attempt > max_retries:
                    print("Max retries reached. Returning empty result.")
                    return {"text": "Error: Unable to get response after multiple attempts.", "expressions": [], "action": None}
                time.sleep(0.1)
