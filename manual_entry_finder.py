import pygame
import sys
import json
import os
from PIL import Image
import pyperclip # Import for clipboard access

# --- Configuration ---
IMAGE_PATH = "example_grid_patterned1.png"
OUTPUT_FILENAME = "manual_coordinates.json"
BACKGROUND_COLOR = (200, 200, 200)
INPUT_BOX_COLOR_INACTIVE = pygame.Color('lightskyblue3')
INPUT_BOX_COLOR_ACTIVE = pygame.Color('dodgerblue2')
INPUT_TEXT_COLOR = pygame.Color('black')
FONT_SIZE = 24
# Max display dimensions for the image portion
MAX_DISPLAY_WIDTH = 1200
MAX_DISPLAY_HEIGHT = 800
# Target A4 dimensions for output coordinates (bottom-left origin)
TARGET_WIDTH = 600.0
TARGET_HEIGHT = 850.0
# ---------------------

# --- Initialization ---
pygame.init()

# Check if image exists
if not os.path.exists(IMAGE_PATH):
    print(f"Error: Image file not found: {IMAGE_PATH}")
    sys.exit()

# Load original image with pygame to get dimensions and surface
try:
    original_img_surface = pygame.image.load(IMAGE_PATH)
    original_img_width, original_img_height = original_img_surface.get_size()
except Exception as e:
    print(f"Error loading image: {e}")
    pygame.quit()
    sys.exit()

# --- Image Scaling --- 
scale_factor = 1.0
display_img_width = original_img_width
display_img_height = original_img_height

# Calculate scale factor if image exceeds max dimensions
if original_img_width > MAX_DISPLAY_WIDTH:
    scale_factor = MAX_DISPLAY_WIDTH / original_img_width
if original_img_height * scale_factor > MAX_DISPLAY_HEIGHT:
     scale_factor = MAX_DISPLAY_HEIGHT / original_img_height

# If scaling is needed, apply it
if scale_factor < 1.0:
    display_img_width = int(original_img_width * scale_factor)
    display_img_height = int(original_img_height * scale_factor)
    try:
        # Use smoothscale for better quality resizing
        display_img_surface = pygame.transform.smoothscale(original_img_surface, (display_img_width, display_img_height))
        print(f"Image scaled down by {scale_factor:.2f} to {display_img_width}x{display_img_height}")
    except Exception as e:
        print(f"Error scaling image: {e}. Using original.")
        display_img_surface = original_img_surface # Fallback to original if scaling fails
        display_img_width = original_img_width
        display_img_height = original_img_height
        scale_factor = 1.0
else:
    display_img_surface = original_img_surface # No scaling needed

# Set up display using potentially scaled dimensions
input_box_height = 40
screen_width = display_img_width
screen_height = display_img_height + input_box_height + 30 # Image + box + prompt padding
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Manual Coordinate Entry (A4 Output: 600x850)")

# Font for input box
font = pygame.font.Font(None, FONT_SIZE)

# --- Data Storage ---
entries = []
current_click_target_coords = None # Stores (x, y) in TARGET A4 coordinates (bottom-left origin)
input_text = ''
input_active = False
prompt_text = "Click on image, then type identifier here and press Enter:"

# --- Main Loop ---
running = True
while running:
    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False # Exit loop, will trigger save later

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x_display, mouse_y_display = event.pos
            # Check if click is within the *displayed* image area
            if 0 <= mouse_x_display < display_img_width and 0 <= mouse_y_display < display_img_height:
                # --- Calculate coords relative to TARGET A4 dimensions (600x850, bottom-left) ---
                # Proportional position on displayed image
                prop_x = mouse_x_display / display_img_width
                prop_y = mouse_y_display / display_img_height

                # Map proportions to target dimensions
                target_x = prop_x * TARGET_WIDTH
                # Calculate y relative to top-left first
                target_y_topleft = prop_y * TARGET_HEIGHT
                # Convert to bottom-left origin for final output y
                target_y_bottomleft = TARGET_HEIGHT - target_y_topleft

                current_click_target_coords = (target_x, target_y_bottomleft)
                input_active = True # Activate input box on image click
                input_text = '' # Clear previous text
                # Show target coords in prompt
                prompt_text = f"Enter identifier for target ({target_x:.1f}, {target_y_bottomleft:.1f}):"
            else:
                # Deactivate if clicking outside image, activate if clicking inside input box
                input_box_rect = pygame.Rect(5, display_img_height + 5, screen_width - 10, input_box_height)
                input_active = input_box_rect.collidepoint(mouse_x_display, mouse_y_display)

        if event.type == pygame.KEYDOWN and input_active:
            mods = pygame.key.get_mods() # Get modifier keys (Shift, Ctrl, Alt, Cmd)

            # --- Paste (Cmd+V or Ctrl+V) ---
            # KMOD_GUI is Cmd on macOS, KMOD_CTRL is Ctrl on Win/Linux
            if event.key == pygame.K_v and (mods & pygame.KMOD_GUI or mods & pygame.KMOD_CTRL):
                try:
                    pasted_text = pyperclip.paste()
                    if pasted_text: # Check if clipboard is not empty
                         input_text += pasted_text
                except Exception as e:
                    print(f"Error pasting from clipboard: {e}") # Handle potential errors

            # --- Enter Key ---
            elif event.key == pygame.K_RETURN:
                if current_click_target_coords and input_text:
                    target_x, target_y_bottomleft = current_click_target_coords

                    entry_data = {
                        "question": input_text,
                        "response": "",
                        "position": {
                            "page": 1,
                            "x": float(target_x),
                            "y": float(target_y_bottomleft)
                        }
                    }
                    entries.append(entry_data)
                    print(f"Added: {input_text} at target ({target_x:.1f}, {target_y_bottomleft:.1f})")

                    # Reset for next entry
                    input_text = ''
                    current_click_target_coords = None
                    input_active = False
                    prompt_text = "Click on image, then type identifier here and press Enter:"
                else:
                    print("Enter/Return pressed but no click location or identifier text.")

            # --- Backspace Key ---
            elif event.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]

            # --- Other Characters ---
            else:
                # Add typed character (ignore if a modifier like Cmd is the main key)
                if not (mods & pygame.KMOD_GUI or mods & pygame.KMOD_CTRL or mods & pygame.KMOD_ALT):
                     input_text += event.unicode

    # --- Drawing ---
    screen.fill(BACKGROUND_COLOR)

    # Draw potentially scaled image
    screen.blit(display_img_surface, (0, 0))

    # Draw Input Box Area (position based on scaled image height)
    input_box_rect = pygame.Rect(5, display_img_height + 5, screen_width - 10, input_box_height)
    color = INPUT_BOX_COLOR_ACTIVE if input_active else INPUT_BOX_COLOR_INACTIVE
    pygame.draw.rect(screen, color, input_box_rect, 2) # Draw border

    # Draw Prompt Text (above input box)
    prompt_surface = font.render(prompt_text, True, INPUT_TEXT_COLOR)
    screen.blit(prompt_surface, (input_box_rect.x + 5, input_box_rect.y - FONT_SIZE - 2)) # Position above box

    # Draw Input Text inside box
    text_surface = font.render(input_text, True, INPUT_TEXT_COLOR)
    # Ensure text doesn't overflow box width easily
    text_rect = text_surface.get_rect(centery=input_box_rect.centery)
    text_rect.x = input_box_rect.x + 5
    screen.blit(text_surface, text_rect)

    # --- Update Display ---
    pygame.display.flip()


# --- Save on Exit ---
if entries:
    try:
        with open(OUTPUT_FILENAME, 'w') as f:
            json.dump(entries, f, indent=2)
        print(f"\nCoordinates saved to {OUTPUT_FILENAME}")
    except Exception as e:
        print(f"\nError saving JSON file: {e}")
else:
    print("\nNo coordinates entered. Exiting.")

pygame.quit()
sys.exit()
