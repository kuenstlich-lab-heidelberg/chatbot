import yaml
import os
import unicodedata

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import matplotlib.pyplot as plt

from transitions.extensions import HierarchicalGraphMachine
from scripting.lua import LuaSandbox

class Persona:
    def __init__(self, yaml_file_path, transition_callback= None):
        # convert relative to absolute file path
        if not os.path.isabs(yaml_file_path):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            yaml_file_path = os.path.join(current_dir, yaml_file_path)

        self.yaml_file_path = yaml_file_path
        self.calculator = LuaSandbox()
        self.model = None

        if transition_callback is None:
            transition_callback = lambda: None
        self.transition_callback = transition_callback

        self._load()
        self._start_file_watcher()


    def _load(self):
        # Store the current state if the model already exists
        current_state = self.model.state if self.model and hasattr(self.model, 'state') else None
        #print(f"Current state before reload: {current_state}")

        # Read the YAML file and set up the machine
        with open(self.yaml_file_path, 'r') as f:
            self.fsm_config = yaml.safe_load(f)  # Use yaml.safe_load to parse the YAML file

        # Update the inventory and reuse already existing values or set if it is a new one
        inventory = self.fsm_config['metadata'].get('inventory', {})
        for item, value in inventory.items():
            # Do not override a var if it already exists in the sandbox. 
            # We need the old state during hot reload
            if self.calculator.get_var(item) == None:
                self.calculator.set_var(item, value)
                print(f"Set {item} = {value} in Lua sandbox")
            else:
                print(f"Reuse {item} = {self.calculator.get_var(item)} from Lua sandbox")

        self.model_metadata = self.fsm_config.get("metadata", {})
        self.action_metadata = {}
        self.state_metadata = {}
        self.last_transition_error = ""

        clean_states = self._prepare_states(self.fsm_config['states'])
        clean_transitions = self._prepare_transitions(self.fsm_config['transitions'])
            
        # Create the state machine
        self.model = type('Model', (object,), {})()
        self.machine = HierarchicalGraphMachine(
            model=self.model, 
            states=clean_states, 
            transitions=clean_transitions, 
            initial=self.fsm_config['initial'], 
            ignore_invalid_triggers=True
        )

        # Attempt to restore the previous state if it exists in the new state list
        if current_state and current_state in [state['name'] for state in clean_states]:
            #print(f"Restoring previous state: {current_state}")
            self.machine.set_state(current_state)
        else:
            print("Previous state not found in new configuration, using initial state.")
            

    def _prepare_states(self, states):
        default_metadata = {
            "description": "Default metadata",
            "system_prompt": ""
        }

        metadata_freed_states = []
        for state in states:
            metadata = state.get('metadata', default_metadata)
            self.state_metadata[state['name']] = metadata
            # Remove metadata from the state dictionary before passing it to the "transistions" state machine
            state = {key: value for key, value in state.items() if key != 'metadata'}
            metadata_freed_states.append(state)
        return metadata_freed_states


    def _prepare_transitions(self, transitions):
        default_metadata = {
            "description": "Default metadata",
            "system_prompt": ""
        }

        metadata_freed_transitions = []
        for transition in transitions:
            metadata = transition.get('metadata', default_metadata)
            self.action_metadata[transition['trigger']] = metadata
            transition = {key: value for key, value in transition.items() if key != 'metadata'}
             
            transition['after'] = self._create_transition_callback(transition['trigger'])
            transition['conditions'] = [self._create_condition_callback(transition['trigger'])]

            metadata_freed_transitions.append(transition)
        
        return metadata_freed_transitions


    def _create_transition_callback(self, action):
        """
        This creates a callback function that is triggered after a specific transition.
        """
        def callback(*args, **kwargs):
            #print(f"CALLBACK action: {action}")
            current_state = self.model.state
            metadata_state = self.state_metadata.get(current_state, {})
            metadata_action = self.action_metadata.get(action, {})
            # Execute actions in the LuaSandbox
            actions = metadata_action.get('actions', [])
            for code in actions:
                if len(code)>0:
                    self.calculator.eval(code)  # Execute each action in the Lua sandbox

            # Call the user-defined transition callback with metadata
            self.transition_callback(current_state, action, metadata_action, metadata_state)
        return callback

    def _create_condition_callback(self, action):
        """
        This creates a condition function that always returns True but can log or handle
        the action in future use cases.
        """
        def condition_callback(*args, **kwargs):
            print(f"Condition callback for action: {action}")
            metadata_action = self.action_metadata.get(action, {})
            conditions = metadata_action.get("conditions", [])

            # Evaluate all conditions using the Lua sandbox (calculator)
            for condition in conditions:
                if len(condition)>0:
                    result = self.calculator.eval(f'return ({condition})')
                    if not result:  # If any condition fails, return False
                        self.last_transition_error = f"Condition '{condition}' failed for '{action}'"
                        print(self.last_transition_error)
                        print(self.calculator.get_all_vars())
                        return False

            return True  # All conditions passed, allow the transition

        return condition_callback
    

    def get_inventory(self):
        return { "state":self.get_state(),  **self.calculator.get_all_vars()}
    

    def trigger(self, action):
        try:
            print(f"Action: '{action}'")
            return self.model.trigger(action)
        except Exception as e:
            print(e)
            print(f"Error triggering event '{action}': {e}")
            return False


    def get_action_metadata(self, action):
        return self.action_metadata.get(action, {})


    def get_global_system_prompt(self):
        return self.fsm_config["metadata"]["system_prompt"]
    

    def get_state_system_prompt(self):
        return self.state_metadata[self.get_state()]["system_prompt"]
    

    def get_action_system_prompt(self, action):
        return self.action_metadata[action]["system_prompt"]
   

    def get_action_description(self, action):
        #print(self.action_metadata[action])
        return self.action_metadata[action].get("description", "")
   

    def get_state(self):
        return self.model.state
    

    def get_possible_actions(self):
        current_state = self.model.state
        available_actions = []

        def is_triggerable(action):
            metadata_action = self.action_metadata.get(action, {})
            conditions = metadata_action.get("conditions", [])
            for condition in conditions:
                if len(condition)>0:
                    result = self.calculator.eval(f'return ({condition})')
                    if not result:
                        return False
            return True 

        # Go through machine's events and match transitions that are valid for the current state
        for event_name, event in self.machine.events.items():
            # Filter out the "to_XYZ" transitions and match the valid ones
            if not event_name.startswith("to_"):
                for transition in event.transitions[self.model.state]:
                    # check if the current state matches with the transistion source
                    if transition.source == current_state and is_triggerable(event_name):
                        available_actions.append(event_name)
        
        return available_actions


    def _start_file_watcher(self):
        """Start a watchdog observer to monitor the YAML file for changes."""
        watch_dir =  os.path.dirname(self.yaml_file_path) +"/"
       # print(f"Init file-watch on dir '{watch_dir}'")

        self.observer = Observer()
        self.observer.schedule(FileChangeHandler(self), watch_dir, recursive=True)
        self.observer.start()


    def stop_file_watcher(self):
        """Stop the file watcher when no longer needed."""
        self.observer.stop()
        self.observer.join()


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, persona):
        super().__init__()
        self.persona = persona
        self.last_modified = os.path.getmtime(persona.yaml_file_path)


    def on_modified(self, event):
        # Normalize paths to ensure consistent comparison
        event_path_normalized = unicodedata.normalize('NFC', event.src_path)
        yaml_path_normalized = unicodedata.normalize('NFC', self.persona.yaml_file_path)

        if event_path_normalized == yaml_path_normalized:
            new_modified_time = os.path.getmtime(event.src_path)
            if new_modified_time != self.last_modified:
                self.last_modified = new_modified_time
                #print("YAML file modified, reloading FSM configuration.")
                self.persona._load()  # Reload FSM configuration


# Example of how you would use the class
if __name__ == "__main__":
    fsm = Persona("default.yaml", None)
    fsm.trigger("become_annoyed")

    # Render the graph of the FSM
    graph = fsm.machine.get_graph()
    graph.draw('fsm_diagram.png', prog='dot')

    # Show the generated image
    img = plt.imread('fsm_diagram.png')
    plt.imshow(img)
    plt.axis('off')  # Hide axes
    plt.show()
