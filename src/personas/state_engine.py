import json
import os
from transitions.extensions import HierarchicalGraphMachine
import matplotlib.pyplot as plt

class Persona:
    def __init__(self, json_file_path, callback):
        # Load the FSM configuration from the external JSON file
        if not os.path.isabs(json_file_path):
            # Get the directory of the current script
            current_dir = os.path.dirname(os.path.abspath(__file__))
            json_file_path = os.path.join(current_dir, json_file_path)
        
        # Read the JSON file and set up the machine
        with open(json_file_path, 'r') as f:
            self.fsm_config = json.load(f)

        self.transition_metadata = {}
        clean_transitions = self._prepare_transitions(self.fsm_config['transitions'])
        self.model = type('Model', (object,), {})()
            
        # Create the state machine
        self.machine = HierarchicalGraphMachine(
            model=self.model, 
            states=self.fsm_config['states'], 
            transitions=clean_transitions, 
            initial=self.fsm_config['initial'], 
            ignore_invalid_triggers=True
        )

        # Register the callback for all transitions
        self.callback = callback
        self._register_metadata_callbacks()


    def _prepare_transitions(self, transitions):
        clean_transitions = []
        # Cleanup "metadata" attribute because "transitions" lib can't handle it.
        #
        for transition in transitions:
            if 'metadata' in transition:
                self.transition_metadata[transition['trigger']] = transition['metadata']
                transition = {key: value for key, value in transition.items() if key != 'metadata'}
            
            clean_transitions.append(transition)
        
        return clean_transitions


    def _register_metadata_callbacks(self):
        for transition in self.fsm_config['transitions']:
            trigger_name = transition['trigger']
            metadata = transition.get('metadata', {})
            self.machine.on_enter(transition['dest'], self._create_callback(trigger_name, metadata))


    def _create_callback(self, trigger_name, metadata):
        def callback(*args, **kwargs):
            self.callback(trigger_name, metadata)
        return callback


    def trigger(self, event_name):
        try:
            self.model.trigger(event_name)
        except Exception as e:
            print(f"Error triggering event '{event_name}': {e}")


    def get_system_prompt(self):
        return self.fsm_config["system_prompt"]
    

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


# Example callback function
def on_transition_fired(trigger_name, metadata):
    print(f"Transition triggered: {trigger_name}")
    print(f"Description: {metadata.get('description', 'No description')}")
    print(f"System prompt: {metadata.get('system_prompt', 'No system prompt')}")

# Example of how you would use the class
if __name__ == "__main__":
    fsm = Persona("conversation.json", on_transition_fired)
    
    print("Initial state:", fsm.get_state())
    print("Possible triggers:", fsm.get_possible_triggers())

    # Trigger a state change
    fsm.trigger('become_friendly')
    print("State after 'become_friendly':", fsm.get_state())
    print("Possible triggers after 'become_friendly':", fsm.get_possible_triggers())

    fsm.trigger('become_annoyed')
    print("State after 'become_annoyed':", fsm.get_state())
    print("Possible triggers after 'become_annoyed':", fsm.get_possible_triggers())

    # Render the graph of the FSM
    graph = fsm.machine.get_graph()
    graph.draw('fsm_diagram.png', prog='dot')

    # Show the generated image
    img = plt.imread('fsm_diagram.png')
    plt.imshow(img)
    plt.axis('off')  # Hide axes
    plt.show()
