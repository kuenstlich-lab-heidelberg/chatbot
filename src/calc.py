import sympy as sp

class SympySandbox:
    def __init__(self):
        self.environment = {}

    def define_variable(self, name, value):
        """
        Defines or updates a variable in the sandbox.
        :param name: Name of the variable (e.g., 'coins')
        :param value: Initial value of the variable
        """
        self.environment[name] = value

    def evaluate_expression(self, expression_str):
        """
        Evaluates a given mathematical expression and updates the sandbox.
        :param expression_str: Expression to evaluate (e.g., 'coins = coins + 3')
        """
        # Split the expression into left-hand and right-hand sides
        lhs, rhs = expression_str.split('=')
        lhs = lhs.strip()
        rhs = rhs.strip()

        # Evaluate the right-hand side using the current environment
        rhs_value = eval(rhs, {}, self.environment)

        # Update the variable on the left-hand side
        self.environment[lhs] = rhs_value

    def get_variable_value(self, name):
        """
        Retrieves the value of a variable.
        :param name: The name of the variable to query.
        :return: Value of the variable in the sandbox.
        """
        return self.environment.get(name, None)


# Example usage:

sandbox = SympySandbox()

# Define a variable 'coins' with an initial value of 4
sandbox.define_variable('coins', 4)

# Evaluate an expression that updates 'coins'
sandbox.evaluate_expression('coins = coins + 3')

# Query the value of 'coins'
print(f"Value of coins: {sandbox.get_variable_value('coins')}")
