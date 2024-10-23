import abc

# Abstract base class for sandboxes
class BaseSandbox(abc.ABC):
    
    @abc.abstractmethod
    def set_var(self, name, value):
        """Sets a variable in the sandbox."""
        pass

    @abc.abstractmethod
    def get_var(self, name):
        """Gets a variable from the sandbox."""
        pass

    def get_all_vars(self):
        pass

    @abc.abstractmethod
    def eval(self, code):
        """Evaluates code in the sandbox."""
        pass

