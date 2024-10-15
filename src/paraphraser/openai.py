import openai
from openai import OpenAI

import abc
import tiktoken
import os

from paraphraser.base import BaseParaphraser


# Definition der Klasse OpenAILLM, die von BaseLLM erbt
class OpenAIParaphraser(BaseParaphraser):
    def __init__(self):
        super().__init__()
        self.model = "gpt-3.5-turbo"
        self.max_tokens = 2048
        self.stop = None
        self.frequency_penalty = 0
        self.presence_penalty = 0
        self.temperature = 1.0
        self.top_p = 1.0
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)


    def paraphrase(self, sentence:str):
        print(sentence)
        prompts = [
            {
                "role": "system", 
                "content":  """
                        Bitte schreibe den untenstehenden Satz um, ohne Informationen zu verlieren. 
                        Du darfst dabei gerne neue Satzstellungen zur Hilfe nehmen um einfach ein wenig anders zu sein.
                        ABER: BEHALTE  IMMER DIE URSPRÜNGLICHE FAKTEN BEI UND ERFINDE AUF KEINE FALL NEUEN FAKTEN.
                        Acht streng darauf ich, du, er, sie, es nicht zu ändern. Die anreden und personen müssen immer gleich bleiben.
                       niemals die Anrede ändern....niemals. Achte streng ob zuvor ein "Du" oder ein "Sie" verwendet wurde wenn du jemanden ansprichst.
                    """
            },
            {
                "role": "user", 
                "content": sentence
            }
        ]

        result = self.client.chat.completions.create(model=self.model,
                    messages=prompts,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    frequency_penalty=self.frequency_penalty,
                    presence_penalty=self.presence_penalty)
        
        if result and hasattr(result, 'choices') and len(result.choices) > 0:
            content = result.choices[0].message.content
            return content
        else:
            return "I'm sorry, there was an issue processing your request."

