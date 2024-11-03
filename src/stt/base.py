
from abc import ABC, abstractmethod

class BaseSTT(ABC):
    def __init__(self, speech_started=None):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def start_recording(self):
        pass
