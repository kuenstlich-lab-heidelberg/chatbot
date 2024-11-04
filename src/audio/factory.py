from audio.pyaudio import PyAudioSink


class AudioSinkFactory:

    @classmethod
    def create(cls):
        return PyAudioSink()

