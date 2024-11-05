from abc import ABC, abstractmethod

class BaseAudioSink(ABC):


    @abstractmethod
    def write(self, session, chunk):
        pass

    @abstractmethod
    def close(self, session):
        pass
