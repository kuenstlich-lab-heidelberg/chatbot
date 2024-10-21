import json
from transitions.extensions import HierarchicalMachine

# Sample JSON with conditions based on inventory items
json_data = '''
{
  "world": {
    "initial": "room1",
    "states": [
      {
        "name": "room1",
        "initial": "doorLocked",
        "children": ["doorLocked", "doorUnlocked"]
      },
      {
        "name": "room2",
        "initial": "enemyAlive",
        "children": ["enemyAlive", "enemyDead"]
      },
      {
        "name": "room3",
        "initial": "puzzleUnsolved",
        "children": ["puzzleUnsolved", "puzzleSolved"]
      }
    ],
    "transitions": [
      ["unlock_door",   "room1_doorLocked",     "room1_doorUnlocked",  "key"],
      ["move_to_room2", "room1_doorUnlocked",   "room2_enemyAlive"],
      ["defeat_enemy",  "room2_enemyAlive",     "room2_enemyDead"],
      ["move_to_room3", "room2_enemyDead",      "room3_puzzleUnsolved", "water_bottle"],
      ["solve_puzzle",  "room3_puzzleUnsolved", "room3_puzzleSolved"],
      ["move_to_room1", "room3_puzzleSolved",   "room1_doorUnlocked"]
    ]
  }
}
'''

# Load the JSON data into a Python dictionary
world_data = json.loads(json_data)

# Custom machine that overrides resolve_callable for dynamic inventory checking
class CustomMachine(HierarchicalMachine):

    @staticmethod
    def resolve_callable(func, event_data):
        # Access the model (game model) from event data
        model = event_data.model
        
        # Check if the function is a string (representing an item or condition)
        if isinstance(func, str):
            # Check if this string matches an inventory item and return its value (True or False)
            if func in model.inventory:
                return lambda: model.inventory[func]  # Return a callable (lambda) instead of a bool

        # If no inventory match or condition, fallback to the default behavior
        return super(CustomMachine, CustomMachine).resolve_callable(func, event_data)

# Define the game model with dynamic inventory
class GameModel:
    def __init__(self):
        # Inventory for the world and each room
        self.inventory = {
            "key": False,
            "water_bottle": False
        }

# Create the states and transitions for the world from JSON
states = world_data["world"]["states"]
transitions = world_data["world"]["transitions"]
initial_state = world_data["world"]["initial"]

# Initialize the game model
game_model = GameModel()

# Create the CustomMachine with dynamic condition resolution
machine = CustomMachine(
    model=game_model, 
    states=states, 
    transitions=[
        {
            "trigger": transition[0],
            "source": transition[1],
            "dest": transition[2],
            "conditions": transition[3] if len(transition) > 3 else None
        }
        for transition in transitions
    ],
    initial=initial_state, 
    ignore_invalid_triggers=True
)

# Function to list custom transitions based on the current state
def list_available_transitions(machine, model):
    current_state = model.state
    available_transitions = []
    
    # Traverse the explicitly defined transitions
    for event_name, event in machine.events.items():
        for source_state, transitions_list in event.transitions.items():
            # Filter the transitions for the current state
            if current_state == source_state:
                available_transitions.append(event_name)

    return available_transitions

# Example gameplay simulation
print(f"Current state: {game_model.state}")

# List available transitions for the current state
available_transitions = list_available_transitions(machine, game_model)
print(f"Available transitions in current state: {available_transitions}")

# Try unlocking the door without the key (this should fail)
game_model.unlock_door()
print(f"Current state after trying to unlock door without key: {game_model.state}")

# Add key to the inventory and try unlocking the door again
game_model.inventory["key"] = True
game_model.unlock_door()  # Now it should work
print(f"Current state after unlocking the door with the key: {game_model.state}")

# List available transitions again after changing the state
available_transitions = list_available_transitions(machine, game_model)
print(f"Available transitions in current state: {available_transitions}")

# Move to room2 (no condition here)
game_model.move_to_room2()
print(f"Current state after moving to room2: {game_model.state}")

# List available transitions in room2
available_transitions = list_available_transitions(machine, game_model)
print(f"Available transitions in current state: {available_transitions}")

# Defeat the enemy in room2
game_model.defeat_enemy()  # This transition should succeed
print(f"Current state after defeating enemy: {game_model.state}")

# Try moving to room3 without the water bottle (this should fail)
game_model.move_to_room3()
print(f"Current state after trying to move to room3 without water bottle: {game_model.state}")

# Add water bottle to the inventory and try moving to room3 again
game_model.inventory["water_bottle"] = True
game_model.move_to_room3()  # Now it should work
print(f"Current state after moving to room3 with the water bottle: {game_model.state}")

# Solve the puzzle and move back to room1
game_model.solve_puzzle()
game_model.move_to_room1()
print(f"Current state after solving puzzle and moving back to room1: {game_model.state}")

# List available transitions after moving back to room1
available_transitions = list_available_transitions(machine, game_model)
print(f"Available transitions in current state: {available_transitions}")
