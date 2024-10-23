from lupa import LuaRuntime
from scripting.base import BaseSandbox

class LuaSandbox(BaseSandbox):
    
    def __init__(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.env = self.lua.globals()
        # Capture the initial state of Lua globals (before setting user variables)
        self.initial_globals = set(self.env.keys())


    def set_var(self, name, value):
        if isinstance(value, bool):
            # Lua uses `true` and `false` for booleans
            lua_value = 'true' if value else 'false'
            self.lua.execute(f"{name} = {lua_value}")
        else:
            self.lua.execute(f"{name} = {value}")

    def get_var(self, name):
        """Gets a Lua variable."""
        return self.lua.globals()[name]

    def get_all_vars(self):
        # Get all current globals and filter out the initial (default) Lua globals
        current_globals = set(self.env.keys())
        user_defined_globals = current_globals - self.initial_globals
        # Create a dictionary of only user-defined variables
        return {key: self.env[key] for key in user_defined_globals}


    def eval(self, code):
        """Evaluates Lua code."""
        print(f"Execute '{code}'")
        return self.lua.execute(code)


# Example usage of LuaSandbox
if __name__ == "__main__":
    sandbox = LuaSandbox()

    # Set a variable in the Lua environment
    sandbox.set_var("coins", 10)

    # Get the value of the variable
    print(f"Coins before: {sandbox.get_var('coins')}")

    sandbox.eval("coins = 5")

    # Add 5 to coins using eval
    sandbox.eval("coins = coins *5")

    sandbox.eval("return (coins > 5)")

    # Get the updated value of coins
    print(f"Coins after: {sandbox.get_var('coins')}")

    print(sandbox.get_all_vars())
