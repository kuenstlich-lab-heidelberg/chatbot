from tts.base import BaseTTS

# Definition of CLIOutput class inheriting from BaseTTS
class Console(BaseTTS):
    def __init__(self, audio_sink):
        super().__init__(audio_sink)

    def speak(self, session, text):
        # Simulate speaking by printing the text to the console
        print(f"Console: {text}")

    def stop(self, session):
        # Simulate stopping the speech
        pass

