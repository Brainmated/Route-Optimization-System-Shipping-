import tkinter as tk
from tkinter import ttk

def get_weather_index():
    propeller_condition = propeller_entry.get()
    gas_prices = gas_entry.get()
    loaded_weight = weight_entry.get()

    # Perform calculations or actions using the entered values
    # For demonstration purposes, let's simply print the values
    print("Propeller Condition:", propeller_condition)
    print("Current Gas Prices:", gas_prices)
    print("Loaded Weight:", loaded_weight)

# Create a new Tkinter window
window = tk.Tk()

# Set the window title
window.title("Ship Parameters")

window.state("zoomed")

window.resizable(True, True)

# Ship selection dropdown menu
ship_label = tk.Label(window, text="Select Ship:")
ship_label.pack()

ship_var = tk.StringVar()
ship_dropdown = ttk.Combobox(window, textvariable=ship_var, values=["Ship A", "Ship B", "Ship C"])
ship_dropdown.pack()

# Parameter input boxes
propeller_label = tk.Label(window, text="Propeller Condition:")
propeller_label.pack()

propeller_entry = tk.Entry(window)
propeller_entry.pack()

gas_label = tk.Label(window, text="Current Gas Prices:")
gas_label.pack()

gas_entry = tk.Entry(window)
gas_entry.pack()

weight_label = tk.Label(window, text="Loaded Weight:")
weight_label.pack()

weight_entry = tk.Entry(window)
weight_entry.pack()

# Weather Index button
weather_button = tk.Button(window, text="Weather Index", command=get_weather_index)
weather_button.pack()

# Start the Tkinter event loop
window.mainloop()
