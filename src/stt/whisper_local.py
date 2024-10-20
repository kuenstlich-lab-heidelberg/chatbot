from stt.base import BaseSTT
from RealtimeSTT import AudioToTextRecorder


class WhisperLocal(BaseSTT):
    def __init__(self, on_speech_start=None):
        super().__init__()
        if on_speech_start is None:
            on_speech_start = lambda: None  # Leere Lambda-Funktion

        self.recorder = AudioToTextRecorder( 
            language="de",
            model="medium", 
            print_transcription_time=True)
        self.recorder.on_recording_start = on_speech_start


    def start_recording(self):
        print("LargeSTT is ready. Wait until it says 'speak now'")
        # Call text() synchronously to get the transcription result.
        while True:
            transcription = self.recorder.text()
            if transcription:
                yield transcription