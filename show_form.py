import dearpygui.dearpygui as dpg
import json
import os

JSON_FILE = 'manual_coordinates.json'
INPUT_TAG_PREFIX = "input_"

def load_data(filename=JSON_FILE):
    """Loads data from the JSON file."""
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading {filename}: {e}")
        return []

def save_data(data, filename=JSON_FILE):
    """Saves data to the JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Data successfully saved to {filename}")
    except IOError as e:
        print(f"Error saving to {filename}: {e}")

def save_callback(sender, app_data, user_data):
    """Callback function to save data and close the app."""
    data, input_tags = user_data
    for i, item in enumerate(data):
        input_tag = input_tags[i]
        item["response"] = dpg.get_value(input_tag)
    save_data(data)
    dpg.stop_dearpygui()

def apply_modern_theme():
    """Applies a custom modern-looking theme."""
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll): # Apply to all items
            # Window background and padding
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (30, 30, 30, 255))
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 15, 15)
            # Frame background (used by input fields, buttons etc.)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (50, 50, 50, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (70, 70, 70, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (90, 90, 90, 255))
            # Text color
            dpg.add_theme_color(dpg.mvThemeCol_Text, (230, 230, 230, 255))
            # Button colors
            dpg.add_theme_color(dpg.mvThemeCol_Button, (70, 70, 70, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (90, 90, 90, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (110, 110, 110, 255))
             # Separator color
            dpg.add_theme_color(dpg.mvThemeCol_Separator, (70, 70, 70, 255))
             # Input field border radius
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5)
             # General item spacing
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 8)

    dpg.bind_theme(global_theme)

def create_form():
    data = load_data()
    if not data:
        print(f"Could not load data from {JSON_FILE} or file is empty.")
        return

    dpg.create_context()
    apply_modern_theme() # Apply the theme

    input_tags = [] # To store the tags of the input widgets

    with dpg.window(label="PDF Form Entry", tag="Primary Window", width=600, height=700):
        # Add a small title/header inside the window
        dpg.add_text("Edit Form Data", color=(200, 200, 255, 255))
        dpg.add_separator()
        dpg.add_spacer(height=10)

        # Use a child window for scrolling content if needed
        # with dpg.child_window(height=-80): # Leave space for the button
        for i, item in enumerate(data):
            question = item.get("question", "N/A")
            response = item.get("response", "")
            input_tag = f"{INPUT_TAG_PREFIX}{i}" # Unique tag for each input
            input_tags.append(input_tag)

            with dpg.group(horizontal=True):
                # Fixed width for question label to improve alignment
                dpg.add_text(f"{question}:", wrap=180) # Wrap long questions
                # Use spacing based on a fixed label width for better alignment
                dpg.add_spacer(width=200 - dpg.get_item_width(dpg.last_item()))
                dpg.add_input_text(tag=input_tag, default_value=response, width=-1) # Use remaining width
            # dpg.add_separator() # Removed separator for cleaner look, spacing handles separation
            dpg.add_spacer(height=5) # Add vertical space between rows

        dpg.add_spacer(height=20)
        # Center the button
        win_width = dpg.get_item_width("Primary Window")
        btn_width = 120 # Approximate button width, adjust if needed
        dpg.add_spacer(width=(win_width - btn_width) // 2 - 15) # Adjust for padding
        with dpg.group(horizontal=True):
            # Pass data and input_tags to the callback
            dpg.add_button(label="Save and Close", callback=save_callback, user_data=(data, input_tags), width=btn_width)

    dpg.create_viewport(title='PDF Form Editor', width=620, height=750)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == "__main__":
    create_form()
