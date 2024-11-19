from tts.base import BaseTTS
from typing import Callable

# Definition of CLIOutput class inheriting from BaseTTS
class Console(BaseTTS):
    def __init__(self, audio_sink):
        super().__init__(audio_sink)

    def speak(self, session, text, on_start: Callable = lambda session: None):
        # Simulate speaking by printing the text to the console
        self.run_callback(on_start, session)
        print(f"Console: {text}")

    def stop(self, session):
        # Simulate stopping the speech
        pass

