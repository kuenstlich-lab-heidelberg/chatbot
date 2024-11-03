from stt.base import BaseSTT
from RealtimeSTT import AudioToTextRecorder


class WhisperLocal(BaseSTT):
    def __init__(self, on_speech_start=None):
        super().__init__()
        self._stopped = False
        if on_speech_start is None:
            on_speech_start = lambda: None  # Leere Lambda-Funktion

        self.recorder = AudioToTextRecorder( 
            language="de",
            model="medium", 
            print_transcription_time=True)
        self.recorder.on_recording_start = on_speech_start

    def stop(self):
        self._stopped = True

    def start_recording(self):
        print("LargeSTT is ready. Wait until it says 'speak now'")
        # Call text() synchronously to get the transcription result.
        while not self._stopped:
            transcription = self.recorder.text()
            if self._stopped:
                break
            if transcription:
                yield transcription