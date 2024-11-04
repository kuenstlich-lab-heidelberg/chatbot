import abc

# Definition of BaseTTS class
class BaseTTS(abc.ABC):
    def __init__(self):
        pass

    @abc.abstractmethod
    def speak(self, text, audio_sink):
        pass

    @abc.abstractmethod
    def stop(self):
        pass