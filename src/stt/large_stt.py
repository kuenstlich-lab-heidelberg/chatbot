from stt.base_stt import BaseSTT
from RealtimeSTT import AudioToTextRecorder


class LargeSTT(BaseSTT):
    def __init__(self, speech_started=None):
        super().__init__()
        if speech_started is None:
            speech_started = lambda: None  # Leere Lambda-Funktion

        self.recorder = AudioToTextRecorder( 
            language="de",
            model="medium", 
            print_transcription_time=True)
        self.recorder.on_recording_start = speech_started


    def start_recording(self):
        print("LargeSTT is ready. Wait until it says 'speak now'")
        # Call text() synchronously to get the transcription result.
        while True:
            transcription = self.recorder.text()
            if transcription:
                yield transcription