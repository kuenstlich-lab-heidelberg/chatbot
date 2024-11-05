import abc

# Definition of BaseTTS class
class BaseTTS(abc.ABC):
    def __init__(self, audio_sink):
        self.audio_sink = audio_sink

    @abc.abstractmethod
    def speak(self, session, text):
        pass

    @abc.abstractmethod
    def stop(self, session):
        pass