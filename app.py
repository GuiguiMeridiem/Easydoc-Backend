#!/usr/bin/env python3
import os
import io
import json
import PyPDF2
from typing import List, Dict, Any
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import dearpygui.dearpygui as dpg
import webbrowser


JSON_FILE = "manual_coordinates.json" 
INPUT_TAG_PREFIX = "input_"

def launch_docusign_signing_ceremony(signing_url):
    webbrowser.open(signing_url)

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
                            dpg.add_button(label="Signer via xxx", width=560, height=40, callback=lambda: launch_signing("https://"))


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

def load_placeholders(filepath):
    """Charge les placeholders depuis un fichier JSON"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Impossible de charger le fichier JSON : {e}")
        return []

def get_average_char_size(pdf_path: str) -> float:
    """
    Analyze the PDF to find the average character size using multiple methods.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        float: Average character size in points
    """
    print(f"\n[INFO] Analyzing PDF '{pdf_path}' for average character size...")
    
    # Default size if we can't determine it
    DEFAULT_SIZE = 9
    sizes = []
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            print(f"[INFO] Successfully opened PDF with {len(reader.pages)} pages")
            
            # Method 1: Analyze font dictionaries
            print("[INFO] Method 1: Analyzing font dictionaries...")
            for page_num, page in enumerate(reader.pages, 1):
                print(f"[INFO] Analyzing page {page_num}...")
                
                if '/Resources' in page and '/Font' in page['/Resources']:
                    fonts = page['/Resources']['/Font']
                    print(f"[INFO] Found {len(fonts)} font entries")
                    
                    for font_key, font in fonts.items():
                        if isinstance(font, dict):
                            # Try different font dictionary methods
                            size = None
                            
                            # 1.1: Try FontDescriptor
                            if '/FontDescriptor' in font:
                                descriptor = font['/FontDescriptor']
                                for size_key in ['/CapHeight', '/XHeight', '/Ascent', '/FontHeight']:
                                    if size_key in descriptor:
                                        size = float(descriptor[size_key])
                                        print(f"[INFO] Found size from {size_key} for font {font_key}: {size}")
                                        break
                                
                                # 1.2: Try FontBBox
                                if size is None and '/FontBBox' in descriptor:
                                    bbox = descriptor['/FontBBox']
                                    if len(bbox) >= 4:
                                        size = float(bbox[3] - bbox[1]) / 1000.0 * 12
                                        print(f"[INFO] Estimated size from FontBBox for font {font_key}: {size}")
                            
                            # 1.3: Try BaseFont name
                            if size is None and '/BaseFont' in font:
                                base_font = str(font['/BaseFont'])
                                if '-' in base_font:
                                    try:
                                        potential_size = base_font.split('-')[-1]
                                        if potential_size.replace('.', '').isdigit():
                                            size = float(potential_size)
                                            print(f"[INFO] Found size from BaseFont name for font {font_key}: {size}")
                                    except ValueError:
                                        pass
                            
                            # 1.4: Try font matrix
                            if size is None and '/FontMatrix' in font:
                                matrix = font['/FontMatrix']
                                if len(matrix) >= 4:
                                    try:
                                        size = abs(float(matrix[3]) * 1000)
                                        print(f"[INFO] Found size from FontMatrix for font {font_key}: {size}")
                                    except (ValueError, TypeError):
                                        pass
                            
                            if size is not None and 4 <= size <= 72:
                                sizes.append(size)
            
            # Method 2: Analyze text objects in content stream
            print("\n[INFO] Method 2: Analyzing text objects in content stream...")
            for page_num, page in enumerate(reader.pages, 1):
                if page.contents:
                    try:
                        content = page.contents.get_data()
                        # Look for text size operators (Tf operator)
                        import re
                        # Pattern matches font size specifications like "/F1 12 Tf"
                        size_matches = re.findall(rb'/[A-Za-z0-9+]+ (\d+\.?\d*) Tf', content)
                        for size_match in size_matches:
                            try:
                                size = float(size_match)
                                if 4 <= size <= 72:
                                    sizes.append(size)
                                    print(f"[INFO] Found size from content stream on page {page_num}: {size}")
                            except ValueError:
                                continue
                    except Exception as e:
                        print(f"[WARNING] Could not analyze content stream of page {page_num}: {e}")
            
            # Method 3: Extract text and analyze positioning
            print("\n[INFO] Method 3: Analyzing text positioning...")
            for page_num, page in enumerate(reader.pages, 1):
                try:
                    text_objects = page.extract_text(0)  # Extract with detailed layout
                    if hasattr(text_objects, 'get_text_layout'):
                        layout = text_objects.get_text_layout()
                        for obj in layout:
                            if 'height' in obj:
                                size = float(obj['height'])
                                if 4 <= size <= 72:
                                    sizes.append(size)
                                    print(f"[INFO] Found size from text layout on page {page_num}: {size}")
                except Exception as e:
                    print(f"[WARNING] Could not analyze text layout of page {page_num}: {e}")
            
            # Calculate final size
            if sizes:
                # Remove outliers (values more than 2 standard deviations from mean)
                if len(sizes) > 2:
                    mean = sum(sizes) / len(sizes)
                    std = (sum((x - mean) ** 2 for x in sizes) / len(sizes)) ** 0.5
                    sizes = [s for s in sizes if abs(s - mean) <= 2 * std]
                
                avg_size = sum(sizes) / len(sizes)
                print(f"\n[SUCCESS] Calculated average character size: {avg_size:.2f} points from {len(sizes)} measurements")
                print(f"[INFO] Found sizes: {sorted(sizes)}")
                return avg_size
            
            print(f"\n[WARNING] No valid font sizes found using any method, using default size: {DEFAULT_SIZE}")
            return DEFAULT_SIZE
            
    except Exception as e:
        print(f"[ERROR] Could not determine average character size: {e}")
        print(f"[WARNING] Using default size: {DEFAULT_SIZE}")
        return DEFAULT_SIZE

def fill_pdf(pdf_path: str, placeholders: List[Dict[str, Any]], output_path: str = None) -> None:
    """
    Fill a PDF with text at specified positions.
    
    Args:
        pdf_path (str): Path to the original PDF file
        placeholders (List[Dict]): List of dictionaries containing:
            - question: str (the question identifier)
            - response: str (the text to write)
            - position: Dict with:
                - page: int (page number, 1-based)
                - x: float (x-coordinate from left)
                - y: float (y-coordinate from bottom)
        output_path (str): Path for the output PDF. If None, will use original_name_filled.pdf
    """
    print("\n[INFO] Starting PDF filling process...")
    print(f"[INFO] Input PDF: {pdf_path}")
    
    # Determine output path if not provided
    if output_path is None:
        base_name = os.path.splitext(pdf_path)[0]
        output_path = f"{base_name}_filled.pdf"
    print(f"[INFO] Output will be saved to: {output_path}")

    # Get average character size
    char_size = get_average_char_size(pdf_path)
    print(f"[INFO] Using character size: {char_size} points for text insertion")

    print("\n[INFO] Processing placeholders...")
    print(f"[INFO] Total placeholders to process: {len(placeholders)}")

    # Open the original PDF
    with open(pdf_path, 'rb') as file:
        print("[INFO] Reading original PDF...")
        reader = PyPDF2.PdfReader(file)
        writer = PyPDF2.PdfWriter()
        
        # Create a mapping of page numbers to placeholders for that page
        page_placeholders = {}
        for ph in placeholders:
            page_num = ph['position']['page'] - 1  # Convert to 0-based index
            if page_num not in page_placeholders:
                page_placeholders[page_num] = []
            page_placeholders[page_num].append(ph)
            print(f"[INFO] Placeholder '{ph['question']}' mapped to page {ph['position']['page']}")

        # Process each page
        print("\n[INFO] Starting page processing...")
        for page_num in range(len(reader.pages)):
            print(f"\n[INFO] Processing page {page_num + 1}")
            page = reader.pages[page_num]
            
            # If we have placeholders for this page
            if page_num in page_placeholders:
                print(f"[INFO] Found {len(page_placeholders[page_num])} placeholders for page {page_num + 1}")
                
                # Create a new PDF with just the text
                packet = io.BytesIO()
                can = canvas.Canvas(packet)
                
                # Set italic font (using built-in font)
                can.setFont("Helvetica-Oblique", char_size)
                print(f"[INFO] Set up canvas with italic font Helvetica-Oblique, size {char_size}")
                
                # Set dark blue marine color (RGB: 0, 51, 102)
                can.setFillColorRGB(0, 51/255, 102/255)
                print("[INFO] Set text color to dark blue marine")
                
                # Add each placeholder text
                for ph in page_placeholders[page_num]:
                    x = ph['position']['x']
                    y = ph['position']['y']
                    y = y - 5
                    text = ph['response']
                    
                    # Draw the text left-aligned
                    can.drawString(x, y, text)
                    print(f"[INFO] Added text '{text}' at position ({x}, {y}) for question '{ph['question']}'")
                
                print("[INFO] Saving temporary text layer...")
                can.save()
                
                # Move to the beginning of the BytesIO buffer
                packet.seek(0)
                
                # Create a new PDF with the text
                new_pdf = PyPDF2.PdfReader(packet)
                
                # Merge the text with the original page
                print("[INFO] Merging text layer with original page...")
                page.merge_page(new_pdf.pages[0])
            else:
                print(f"[INFO] No placeholders for page {page_num + 1}, keeping original")
            
            # Add the page to the writer
            writer.add_page(page)
            print(f"[INFO] Added processed page {page_num + 1} to output")
        
        # Write the output file
        print(f"\n[INFO] Writing final PDF to {output_path}...")
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        print("[SUCCESS] PDF processing completed successfully!")

def main():
    create_form()

    print("[INFO] Starting example PDF filling process...")
    placeholders = load_placeholders(JSON_FILE)
    if not placeholders:
        print("[ERROR] Aucun placeholder chargé.")
        return

    # Example usage
    pdf_path = "example.pdf"  # Replace with your PDF path
    fill_pdf(pdf_path, placeholders)

if __name__ == "__main__":
    main() 