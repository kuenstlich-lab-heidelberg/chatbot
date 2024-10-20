from abc import ABC, abstractmethod


class BaseVad(ABC):
    @abstractmethod
    def __init__(self, on_speech_data=None, on_speech_start=None, on_speech_end=None):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def close(self):
        pass
