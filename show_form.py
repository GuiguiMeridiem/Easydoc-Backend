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
    """Applies a clean, modern light theme."""
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            # Background
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (245, 245, 245, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (255, 255, 255, 255))
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (255, 255, 255, 255))

            # Input / Frame background
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (230, 230, 230, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (210, 210, 255, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (180, 200, 255, 255))

            # Text colors
            dpg.add_theme_color(dpg.mvThemeCol_Text, (30, 30, 30, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TextSelectedBg, (200, 220, 255, 255))

            # Buttons
            dpg.add_theme_color(dpg.mvThemeCol_Button, (220, 220, 235, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (200, 200, 250, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (170, 190, 250, 255))

            # Separator / Border
            dpg.add_theme_color(dpg.mvThemeCol_Separator, (200, 200, 200, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Border, (200, 200, 200, 255))

            # Styling
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 10, 10)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 20, 20)

    dpg.bind_theme(global_theme)


def create_form():
    data = load_data()
    if not data:
        print(f"Could not load data from {JSON_FILE} or file is empty.")
        return

    dpg.create_context()
    apply_modern_theme()

    input_tags = []

    # Créer la fenêtre principale sans bord ni barre
    with dpg.window(tag="Primary Window", no_title_bar=True, no_resize=True, no_move=True,
                    no_scrollbar=True, no_collapse=True):
        
        # Centrage vertical avec spacer flexible (haut)
        dpg.add_spacer(height=50)
        # Centrage horizontal
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=340)  # Marge gauche pour centrage horizontal

            with dpg.child_window(width=600, height=650, border=True):
                dpg.add_text("Remplissage du formulaire", color=(50, 50, 50, 255))
                dpg.add_separator()
                dpg.add_spacer(height=10)

                # Contenu scrollable du formulaire
                with dpg.child_window(height=460, border=False):
                    for i, item in enumerate(data):
                        question = item.get("question", "N/A")
                        response = item.get("response", "")
                        input_tag = f"{INPUT_TAG_PREFIX}{i}"
                        input_tags.append(input_tag)

                        with dpg.group():
                            dpg.add_text(f"{question} :", color=(80, 80, 80, 255))
                            dpg.add_input_text(tag=input_tag, default_value=response, width=560)
                            dpg.add_spacer(height=10)

                dpg.add_spacer(height=10)
                dpg.add_button(label="Enregistrer et fermer", width=560, height=40,
                               callback=save_callback, user_data=(data, input_tags))

            dpg.add_spacer(width=340)  # Marge droite

        # Centrage vertical (bas)
        dpg.add_spacer(height=100)

    # Fenêtre plein écran
    dpg.create_viewport(title='Formulaire PDF', width=1280, height=800)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("Primary Window", True)
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    create_form()
