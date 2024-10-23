import yaml  # Import the PyYAML library
import os
from transitions.extensions import HierarchicalGraphMachine
import matplotlib.pyplot as plt

class Persona:
    def __init__(self, yaml_file_path, transition_callback):
        # Load the FSM configuration from the external YAML file
        if not os.path.isabs(yaml_file_path):
            # Get the directory of the current script
            current_dir = os.path.dirname(os.path.abspath(__file__))
            yaml_file_path = os.path.join(current_dir, yaml_file_path)

        # Read the YAML file and set up the machine
        with open(yaml_file_path, 'r') as f:
            self.fsm_config = yaml.safe_load(f)  # Use yaml.safe_load to parse the YAML file


        if transition_callback is None:
            transition_callback = lambda: None
        self.transition_callback = transition_callback

        self.transition_metadata = {}
        self.state_metadata = {}

        clean_states = self._prepare_states(self.fsm_config['states'])
        clean_transitions = self._prepare_transitions(self.fsm_config['transitions'])

        self.model = type('Model', (object,), {})()
            
        # Create the state machine
        self.machine = HierarchicalGraphMachine(
            model=self.model, 
            states=clean_states, 
            transitions=clean_transitions, 
            initial=self.fsm_config['initial'], 
            ignore_invalid_triggers=True
        )


    def _prepare_states(self, states):
        clean_states = []
        for state in states:
            if 'metadata' in state:
                # Store the metadata for this state in the cache
                self.state_metadata[state['name']] = state['metadata']
                # Remove metadata from the state dictionary before passing it to the state machine
                state = {key: value for key, value in state.items() if key != 'metadata'}
            clean_states.append(state)
        return clean_states


    def _prepare_transitions(self, transitions):
        clean_transitions = []
        for transition in transitions:
            if 'metadata' in transition:
                self.transition_metadata[transition['trigger']] = transition['metadata']
                transition = {key: value for key, value in transition.items() if key != 'metadata'}
             
            # Add 'after' callback for each transition
            transition['after'] = self._create_transition_callback(transition['trigger'])
            clean_transitions.append(transition)
        
        return clean_transitions


    def _create_transition_callback(self, trigger_name):
        """
        This creates a callback function that is triggered after a specific transition.
        """
        def callback(*args, **kwargs):
            print(f"CALLBACK triggered for transition: {trigger_name}")
            current_state = self.model.state
            metadata_state = self.state_metadata.get(current_state, {})
            metadata_trigger = self.transition_metadata.get(trigger_name, {})
            # Call the user-defined transition callback with metadata
            self.transition_callback(trigger_name, metadata_trigger, metadata_state)
        return callback


    def trigger(self, event_name):
        try:
            self.model.trigger(event_name)
        except Exception as e:
            print(e)
            print(f"Error triggering event '{event_name}': {e}")


    def get_system_prompt(self):
        return self.fsm_config["metadata"]["system_prompt"]
    

    def get_state(self):
        return self.model.state
    

    def get_possible_triggers(self):
        current_state = self.model.state
        available_triggers = []
        
        # Go through machine's events and match transitions that are valid for the current state
        for event_name, event in self.machine.events.items():
            # Filter out the "to_XYZ" transitions and match the valid ones
            if not event_name.startswith("to_"):
                for transition in event.transitions[self.model.state]:
                    if transition.source == current_state:
                        available_triggers.append(event_name)
        
        return available_triggers



# Example of how you would use the class
if __name__ == "__main__":
    fsm = Persona("default.yaml")
    
    # Render the graph of the FSM
    graph = fsm.machine.get_graph()
    graph.draw('fsm_diagram.png', prog='dot')

    # Show the generated image
    img = plt.imread('fsm_diagram.png')
    plt.imshow(img)
    plt.axis('off')  # Hide axes
    plt.show()
