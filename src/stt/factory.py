from stt.whisper_local import WhisperLocal
from stt.whisper_openai import WhisperOpenAi
from stt.cli_text import CLIText

class STTFactory:

    @classmethod
    def create(cls):
        #return  WhisperLocal()
        return WhisperOpenAi()
        #return CLIText()
