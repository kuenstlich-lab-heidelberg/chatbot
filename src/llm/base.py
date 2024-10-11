import abc

# Definition of BaseLLM class (could be extended in the future with more functionalities)
class BaseLLM(abc.ABC):
    def __init__(self):
        pass

    @abc.abstractmethod
    def chat(self, user_input):
        pass
