import os
import time
import json
import google.generativeai as genai
from google.generativeai.types import content_types

from llm.base import BaseLLM


class GeminiRemoteHistoryLLM(BaseLLM):
    def __init__(self):
        super().__init__()
        self.model_name = "gemini-1.5-pro"
        #self.model_name = "gemini-1.5-flash" 
        self.generation_config = {
            "temperature": 0.1,
            "top_p": 0.95,
            "top_k": 64,  # 64
            "max_output_tokens": 310,
            "response_mime_type": "text/plain",
        }

        self.api_key=os.environ["GEMINI_API_KEY"]
        if not self.api_key:
            raise ValueError("API key 'GEMINI_API_KEY' not found in environment variables.")
        genai.configure(api_key=self.api_key)

        self.instruction_addon = f"""
            Ich wähle je nach Gesprächskontext und nur auf expliziten Wunsch des Benutzers die 
            passende Funktion aus. Dabei achte ich darauf, dass das Handlungsverb der Aktion semantisch 
            zur Anweisung passt, um Verwechslungen wie „öffne...“ statt „untersuche...“ zu vermeiden. Verben die semantisch identisch
            sind wie "gehen", "laufen", "rennen" oder "aufheben", "nehmen",...können als identisch und gleichwertig angesehen werden.

            Wenn keine der bereitgestellten Funktionen dem Befehl des Nutzers entspricht, fahre ich ohne technische 
            Hinweise oder Rückmeldung ganz normal im Gesprächsverlauf fort, ohne eine Funktion auszuführen.
        """
        #self.instruction_addon =""
        self.model = None
        self.chat_session = None


    def dump(self):
        try:
            # Access history directly as a list
            history = self.chat_session.history

            # Format history by extracting the role and concatenating text from all parts
            formatted_history = []
            for msg in history:
                # Concatenate text from all parts
                message_text = ' '.join(part.text for part in msg.parts)
                formatted_history.append({"speaker": msg.role, "message": message_text})

            # Print the formatted history in JSON format
            print(json.dumps(formatted_history, indent=4))

        except AttributeError as e:
            print("Error: Expected each item in `self.chat_session.history` to have 'role' and 'parts' attributes with 'content' in each part.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


    def system(self, system_instruction):
        if system_instruction:
            self.chat_session.send_message("System instruction: "+system_instruction.replace(f'\n', ''))


    def reset(self, session):
        if self.model==None:
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self.generation_config,
                safety_settings={
                    'HATE': 'BLOCK_NONE',
                    'HARASSMENT': 'BLOCK_NONE',
                    'SEXUAL': 'BLOCK_NONE',
                    'DANGEROUS': 'BLOCK_NONE'
                },
                system_instruction=session.state_engine.get_global_system_prompt()+". "+self.instruction_addon,
            )
        self.chat_session = self.model.start_chat(enable_automatic_function_calling=False)


    def chat(self, session, user_input):
        if not user_input:
            print("Error: No user input provided.")
            return {"text": "No input provided.", "expressions": [], "action": None}

        if self.chat_session==None:
            print("Generate Chat Session")
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self.generation_config,
                safety_settings={
                    'HATE': 'BLOCK_NONE',
                    'HARASSMENT': 'BLOCK_NONE',
                    'SEXUAL': 'BLOCK_NONE',
                    'DANGEROUS': 'BLOCK_NONE'
                },
                system_instruction=session.state_engine.get_global_system_prompt()+" "+self.instruction_addon,
            )
            self.chat_session = self.model.start_chat( enable_automatic_function_calling=False)
            print(session.state_engine.get_global_system_prompt()+" "+self.instruction_addon)


        #user_input = user_input.replace(f'\n', '')
        tools = [
            genai.protos.Tool(
                function_declarations=[
                    genai.protos.FunctionDeclaration(
                        name=action,
                        description=session.state_engine.get_action_description(action),
                        parameters=None
                    )
                ]
            )
            for action in session.state_engine.get_possible_actions()
        ]
        print(json.dumps(session.state_engine.get_possible_actions(), indent=4))

        # Erster Modellaufruf mit "function_calling_config" auf "ANY" um zu versuchen "action" und "text" zu bekommen
        #
        tool_config = content_types.to_tool_config({ "function_calling_config": { "mode": "AUTO"} })
        result = self._get_response_with_config(user_input, tools, tool_config)
        action = result["action"]

        # Falls Gemini nur "action" geliefert hat, dann starten wir einen zweiten Aufruf um uns nur eine "text" Antwort abzuholen.
        # Kann manchmal passieren. AI = fuzzy
        #
        if result["text"] is None:
            tool_config= content_types.to_tool_config({ "function_calling_config": {"mode": "NONE"}})
            #"No text response; retrying with function_calling_config set to 'NONE'.")
            if action in session.state_engine.get_possible_actions():
                second_result = self._get_response_with_config(f"""
                    SYSTEM: Du hast die Aktion '{result["action"]}' erfolgreich im Hintergrund ausgeführt. Bitte teile dies nun dem Benutzer mit, was du getan hast:
                    User: """+ user_input, tools, tool_config)
            else:
                result["action"] = None
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
                attempt += 1
                if attempt > max_retries:
                    print("Max retries reached. Returning empty result.")
                    return {"text": "Error: Unable to get response after multiple attempts.", "expressions": [], "action": None}
                time.sleep(0.1)
