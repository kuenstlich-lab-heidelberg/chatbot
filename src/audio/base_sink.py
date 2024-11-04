from abc import ABC, abstractmethod

class BaseAudioSink(ABC):
    @abstractmethod
    def write(self, chunk):
        pass

    @abstractmethod
    def close(self):
        pass
