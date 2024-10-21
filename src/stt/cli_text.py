from stt.base import BaseSTT

class CLIText(BaseSTT):
    def __init__(self, on_text_start=None):
        super().__init__()
        if on_text_start is None:
            on_text_start = lambda: None  # Empty lambda function

        self.on_text_start = on_text_start  # Register the callback function

    def start_recording(self):
        print("CLIText is ready. Type your input and press Enter:")
        # Call the generator to yield the user's CLI input.
        while True:
            self.on_text_start()  # Trigger callback when text input starts
            transcription = input("You: ")  # Read user input from the command line
            if transcription:
                yield transcription  # Yield the input as transcription
