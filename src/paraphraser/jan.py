import requests
import json

from paraphraser.base import BaseParaphraser


class JanParaphraser(BaseParaphraser):
    def __init__(self):
        super().__init__()
        self.model = "llama3.2-3b-instruct"
        self.url = "http://localhost:1337/v1/chat/completions"
        self.stream = False
        self.stop = None
        self.frequency_penalty = 0
        self.presence_penalty = 0
        self.temperature = 0.9
        self.top_p = 0.95


    def paraphrase(self, sentence:str):
        print(sentence)
        prompts = [
            {
                "role": "system", 
                "content": """
                  Bitte schreibe den untenstehenden Satz um, ohne Informationen zu verlieren. 
                  Du darfst dabei gerne neue Satzstellungen zur Hilfe nehmen um einfach ein wenig anders zu sein.
                  ABER: BEHALTE  IMMER DIE URSPRÜNGLICHE FAKTEN BEI UND ERFINDE AUF KEINE FALL NEUEN FAKTEN.
                  Acht streng darauf ich, du, er, sie, es nicht zu ändern. Die anreden und personen müssen immer gleich bleiben.
                  niemals die Anrede ändern....niemals
                   """
            },
            {
                "role": "user", 
                "content": sentence

            }
        ]

        headers = {
            "Content-Type": "application/json",
        }

        payload = {
            "messages": prompts,
            "model": self.model,
            "stream": self.stream,
            "stop": self.stop,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "temperature": self.temperature,
            "top_p": self.top_p
        }
        response = requests.post(self.url, headers=headers, data=json.dumps(payload))
        result = response.json()
        # Extract the content from the response
        content = result['choices'][0]['message']['content']
        content = content.replace("<|eot_id|>","")

        # Return the response content
        return content
