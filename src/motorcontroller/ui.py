import tkinter as tk
import json
import os

class TkinterFileReaderApp:
    def __init__(self, json_file="data.json", check_interval=200):
        # Set up the Tkinter window
        self.root = tk.Tk()
        self.root.title("On-Screen Display")
        self.root.attributes("-topmost", True)  # Keep window on top

        # Header label for the main heading
        self.header_label = tk.Label(self.root, text="", font=("Helvetica", 24, "bold"), fg="black")
        self.header_label.pack(pady=10)

        # Frame to make the expression field stand out
        self.expression_frame = tk.Frame(self.root, bg="#dfe3e6", bd=2, relief="solid", padx=10, pady=5)
        self.expression_frame.pack(pady=10)
        
        # Expression label inside the frame
        self.expression_label = tk.Label(self.expression_frame, text="", font=("Helvetica", 18, "bold"), fg="blue", bg="#dfe3e6")
        self.expression_label.pack()

        # Frame to display inventory items in a grid layout
        self.inventory_frame = tk.Frame(self.root)
        self.inventory_frame.pack(pady=10)
        self.inventory_labels = {}

        # JSON file to read data from and check interval
        self.json_file = json_file
        self.check_interval = check_interval
        self.last_mtime = 0  # Track the last modification time

        # Start periodic check for updates
        self.root.after(0, self.check_for_updates)

    def check_for_updates(self):
        """Check for updates in the JSON file and refresh UI if changes are found."""
        try:
            current_mtime = os.path.getmtime(self.json_file)
            if current_mtime != self.last_mtime:
                self.last_mtime = current_mtime
                self.load_and_update()
        except FileNotFoundError:
            print(f"File '{self.json_file}' not found.")
        except json.JSONDecodeError:
            print(f"Error decoding JSON in '{self.json_file}'.")

        self.root.after(self.check_interval, self.check_for_updates)

    def load_and_update(self):
        """Load JSON data from the file and update the Tkinter display."""
        try:
            with open(self.json_file, 'r') as f:
                data = json.load(f)
                
            # Extract header, expression, and inventory
            header = data.get("header", "No header provided")
            expression = data.get("expression", "")
            inventory = data.get("inventory", {})

            # Update header and expression labels
            self.header_label.config(text=header)
            self.expression_label.config(text=f"Expression: {expression}")

            # Clear existing inventory labels in the frame
            for labels in self.inventory_labels.values():
                labels[0].destroy()
                labels[1].destroy()
            self.inventory_labels.clear()

            # Sort inventory items alphabetically by key and display them in a grid layout
            for row, (key, value) in enumerate(sorted(inventory.items())):
                key_label = tk.Label(self.inventory_frame, text=f"{key}:", font=("Helvetica", 14, "bold"), anchor="w")
                value_label = tk.Label(self.inventory_frame, text=str(value), font=("Helvetica", 14), anchor="w")
                key_label.grid(row=row, column=0, sticky="w", padx=5, pady=2)
                value_label.grid(row=row, column=1, sticky="w", padx=5, pady=2)
                self.inventory_labels[key] = (key_label, value_label)

        except Exception as e:
            print(f"Error loading or updating data: {e}")

    def run(self):
        """Run the Tkinter main loop."""
        self.root.mainloop()

if __name__ == "__main__":
    app = TkinterFileReaderApp(json_file="data.json", check_interval=2000)
    app.run()
