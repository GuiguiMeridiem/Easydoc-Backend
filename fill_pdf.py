#!/usr/bin/env python3

import os
from typing import List, Dict, Any
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

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
    """
    Example usage of the fill_pdf function.
    """
    print("[INFO] Starting example PDF filling process...")
    
    # Example placeholders
    placeholders = [
        {
            "question": "name",
            "response": "John Doe",
            "position": {"page": 1, "x": 190, "y": 685}
        },
        {
            "question": "date",
            "response": "2024-03-19",
            "position": {"page": 1, "x": 532, "y": 685}
        }
    ]

    placeholders = [
  {
    "question": "Nom",
    "response": "Schupp",
    "position": {
      "page": 1,
      "x": 147.61061946902655,
      "y": 690.625
    }
  },
  {
    "question": "Prénom",
    "response": "Guillaume",
    "position": {
      "page": 1,
      "x": 320.7079646017699,
      "y": 690.625
    }
  },
  {
    "question": "Date de nais.",
    "response": "08/01/2004",
    "position": {
      "page": 1,
      "x": 475.75221238938053,
      "y": 692.75
    }
  },
  {
    "question": "Adresse complète",
    "response": "Rue Neuve 28 Hannut",
    "position": {
      "page": 1,
      "x": 123.1858407079646,
      "y": 683.1875
    }
  },
  {
    "question": "Unité Guide (Région, n°, nom)",
    "response": "Cacahuette",
    "position": {
      "page": 1,
      "x": 161.41592920353983,
      "y": 670.4375
    }
  },
  {
    "question": "Parent 1 Nom",
    "response": "Fabrice",
    "position": {
      "page": 1,
      "x": 86.01769911504425,
      "y": 610.9375
    }
  },
  {
    "question": "Parent 1 : Lien de parenté",
    "response": "Oncle",
    "position": {
      "page": 1,
      "x": 118.93805309734513,
      "y": 601.375
    }
  },
  {
    "question": "Parent 1 : Période du",
    "response": "07/03/2005",
    "position": {
      "page": 1,
      "x": 98.76106194690266,
      "y": 590.75
    }
  },
  {
    "question": "Parent 1 : au",
    "response": "07/03/2027",
    "position": {
      "page": 1,
      "x": 142.30088495575222,
      "y": 589.6875
    }
  },
  {
    "question": "Parent 1 : tél",
    "response": "02 558 85 85",
    "position": {
      "page": 1,
      "x": 77.52212389380531,
      "y": 569.5
    }
  },
  {
    "question": "Parent 1 GSM",
    "response": "0478 87 89 90",
    "position": {
      "page": 1,
      "x": 81.76991150442478,
      "y": 561.0
    }
  },
  {
    "question": "Parent 1 E-mail",
    "response": "fabrice@gmail.com",
    "position": {
      "page": 1,
      "x": 89.20353982300885,
      "y": 550.375
    }
  },
  {
    "question": "Parent 1 Remarque(s)",
    "response": "Parent sympa",
    "position": {
      "page": 1,
      "x": 109.38053097345133,
      "y": 542.9375
    }
  },
  {
    "question": "Parent 2 Nom",
    "response": "Isabelle",
    "position": {
      "page": 1,
      "x": 336.63716814159295,
      "y": 608.8125
    }
  },
  {
    "question": "Parent 2 : Lien de parenté",
    "response": "Mamie",
    "position": {
      "page": 1,
      "x": 370.6194690265487,
      "y": 601.375
    }
  },
  {
    "question": "Parent 2 : Période du",
    "response": "01/09/2024",
    "position": {
      "page": 1,
      "x": 349.3805309734513,
      "y": 591.8125
    }
  },
  {
    "question": "Parent 2 : au",
    "response": "31/08/2025",
    "position": {
      "page": 1,
      "x": 393.98230088495575,
      "y": 591.8125
    }
  },
  {
    "question": "Parent 2 : tél",
    "response": "02 987 65 43",
    "position": {
      "page": 1,
      "x": 329.20353982300884,
      "y": 572.6875
    }
  },
  {
    "question": "Parent 2 : GSM",
    "response": "0499 87 65 43",
    "position": {
      "page": 1,
      "x": 330.2654867256637,
      "y": 559.9375
    }
  },
  {
    "question": "Parent 2 : E-mail",
    "response": "isabelle@email.be",
    "position": {
      "page": 1,
      "x": 336.63716814159295,
      "y": 551.4375
    }
  },
  {
    "question": "Parent 2 : Remarque(s)",
    "response": "belle mamie",
    "position": {
      "page": 1,
      "x": 360.0,
      "y": 541.875
    }
  }
]


    
    # Example usage
    pdf_path = "example.pdf"  # Replace with your PDF path
    print(f"[INFO] Example placeholders: {placeholders}")
    fill_pdf(pdf_path, placeholders)

if __name__ == "__main__":
    main() 