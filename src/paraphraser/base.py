from abc import ABC, abstractmethod

class BaseParaphraser(ABC):
    @abstractmethod
    def paraphrase(self, sentence: str) -> str:
        """
        Abstract method to paraphrase a given sentence.

        Parameters:
        - sentence (str): The sentence to be paraphrased.

        Returns:
        - str: The paraphrased sentence.
        """
        pass
