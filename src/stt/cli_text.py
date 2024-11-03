from stt.base import BaseSTT

class CLIText(BaseSTT):
    def __init__(self, on_text_start=None):
        super().__init__()
        self._stopped = False
        if on_text_start is None:
            on_text_start = lambda: None  # Empty lambda function

        self.on_text_start = on_text_start  # Register the callback function

    def stop(self):
        self._stopped = True


    def start_recording(self):
        """Starts recording by taking user input from CLI until stopped."""
        while not self._stopped:
            self.on_text_start()
            transcription = input("You: ")
            if self._stopped:
                break
            if transcription:
                yield transcription 