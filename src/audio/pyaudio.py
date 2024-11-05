import pyaudio

from audio.base_sink import BaseAudioSink


class PyAudioSink(BaseAudioSink):
    _pyaudio_instance = None

    @classmethod
    def get_instance(cls):
        """Ensures a single PyAudio instance is created and shared."""
        if cls._pyaudio_instance is None:
            cls._pyaudio_instance = pyaudio.PyAudio()
        return cls._pyaudio_instance


    def __init__(self):
        self.stream = self.get_instance().open(
            format=pyaudio.paInt16,
            channels=1,
            rate=24000,
            output=True
        )


    def write(self, session, chunk):
        self.stream.write(chunk)

    def close(self, session):
        print("CLOSE SINK")
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

