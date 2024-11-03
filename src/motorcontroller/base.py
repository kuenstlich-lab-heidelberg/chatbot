from abc import abstractmethod, ABC

# Step 1: Define the Base Class using abc
class Base(ABC):

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def set(self, expressions, inventory):
        """Sets the expression to use"""
        pass
