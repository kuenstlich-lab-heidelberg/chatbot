from tts.base import BaseTTS

# Definition of CLIOutput class inheriting from BaseTTS
class Console(BaseTTS):
    def __init__(self):
        super().__init__()

    def speak(self, text, audio_sink):
        # Simulate speaking by printing the text to the console
        print(f"Console: {text}")

    def stop(self):
        # Simulate stopping the speech
        pass

