import pyaudio
import asyncio

from audio.base_sink import BaseAudioSink

class PyAudioSink(BaseAudioSink):
    def __init__(self):
        self.pyaudio_instance = pyaudio.PyAudio()
        self.stream = self.pyaudio_instance.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=24000,
            output=True
        )

    def write(self, chunk):
        self.stream.write(chunk)

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pyaudio_instance.terminate()
