import tkinter as tk
from tkinter import ttk

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Three Column Layout with Log Window")

        # Create a PanedWindow to hold top and bottom sections
        self.paned_window = tk.PanedWindow(root, orient=tk.VERTICAL, sashrelief=tk.RAISED)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Top section (for the three columns)
        self.top_frame = tk.Frame(self.paned_window)
        self.paned_window.add(self.top_frame, height=400)  # initial height for the top section

        # Bottom section (for the log window)
        self.bottom_frame = tk.Frame(self.paned_window)
        self.paned_window.add(self.bottom_frame, height=200)  # initial height for the bottom section

        # Configure top_frame to expand and fill available space
        self.top_frame.rowconfigure(0, weight=1)  # Allow the first row to expand (containing the columns)

        # Create three columns inside the top frame
        self.create_three_columns()

        # Create the log window at the bottom
        self.create_log_window()


    def create_three_columns(self):
        # Create 3 columns (as frames) with equal width
        self.column1 = tk.Frame(self.top_frame)
        self.column1.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)

        # Add separator between column 1 and column 2
        self.separator1 = ttk.Separator(self.top_frame, orient='vertical')
        self.separator1.grid(row=0, column=1, sticky="ns", padx=10)

        self.column2 = tk.Frame(self.top_frame)
        self.column2.grid(row=0, column=2, sticky="nsew", padx=(0, 10), pady=10)

        # Add separator between column 2 and column 3
        self.separator2 = ttk.Separator(self.top_frame, orient='vertical')
        self.separator2.grid(row=0, column=3, sticky="ns", padx=10)

        self.column3 = tk.Frame(self.top_frame)
        self.column3.grid(row=0, column=4, sticky="nsew", padx=(0, 10), pady=10)

        # Set equal weight to the columns for equal resizing
        self.top_frame.columnconfigure(0, weight=1)
        self.top_frame.columnconfigure(2, weight=1)
        self.top_frame.columnconfigure(4, weight=1)

        # Add widgets to each column
        self.create_column_widgets(self.column1, "Column 1 Header")
        self.create_column_widgets(self.column2, "Column 2 Header")
        self.create_column_widgets(self.column3, "Column 3 Header")

    def create_column_widgets(self, master, header_text):
        # Header
        header = tk.Label(master, text=header_text, font=("Arial", 14, "bold"))
        header.pack(anchor="n", pady=10)

        # Combobox
        combo = ttk.Combobox(master, values=["Option 1", "Option 2", "Option 3"])
        combo.set("Select Option")
        combo.pack(anchor="n", pady=5)

        # Additional widgets (sliders, buttons, etc.)
        slider = tk.Scale(master, from_=0, to=100, orient=tk.HORIZONTAL, label="Slider")
        slider.pack(anchor="n", pady=5)

        button = tk.Button(master, text="Button", command=lambda: self.log_message(f"Button clicked in {header_text}"))
        button.pack(anchor="n", pady=5)

        # Text field at the bottom of each column (to be updated via a utility function)
        text_field = tk.Entry(master)
        text_field.pack(anchor="s", pady=10, fill=tk.X)

        # Store the text field for later updates
        master.text_field = text_field

    def create_log_window(self):
        # Log window (bottom part)
        self.log_text = tk.Text(self.bottom_frame, height=10, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def log_message(self, message):
        # Utility function to log messages in the bottom text area
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.config(state=tk.DISABLED)

    def update_column_text_field(self, column, text):
        # Utility function to update the text field in a specific column
        column.text_field.delete(0, tk.END)
        column.text_field.insert(0, text)


# Create the main window
root = tk.Tk()

# Create and run the application
app = App(root)

# Example of updating text fields via the utility function
app.update_column_text_field(app.column1, "Column 1 updated text")
app.update_column_text_field(app.column2, "Column 2 updated text")
app.update_column_text_field(app.column3, "Column 3 updated text")

# Start the Tkinter main loop
root.mainloop()
