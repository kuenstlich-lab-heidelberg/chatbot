import abc

# Step 1: Define the Base Class using abc
class Base(abc.ABC):
    @abc.abstractmethod
    def set(self, expressions, inventory):
        """Sets the expression to use"""
        pass
