#!/usr/bin/env python3

import os
import io
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import lightgrey, darkgrey

# Add pdf2image import. Requires poppler installed on the system.
from pdf2image import convert_from_path

def add_grid_to_pdf(input_pdf_path: str, output_pdf_path: str, grid_spacing: int = 50):
    """
    Adds a grid with coordinate labels to each page of a PDF.

    Args:
        input_pdf_path (str): Path to the original PDF file.
        output_pdf_path (str): Path for the output PDF with the grid.
        grid_spacing (int): The spacing between grid lines in points.
    """
    print(f"[INFO] Starting grid addition process for '{input_pdf_path}'...")
    print(f"[INFO] Grid spacing set to {grid_spacing} points.")

    try:
        # Open the original PDF
        with open(input_pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            writer = PyPDF2.PdfWriter()
            num_pages = len(reader.pages)
            print(f"[INFO] Opened PDF with {num_pages} pages.")

            # Process each page
            for page_num in range(num_pages):
                page = reader.pages[page_num]
                media_box = page.mediabox
                width = float(media_box.width)
                height = float(media_box.height)
                print(f"[INFO] Processing Page {page_num + 1}: Dimensions {width:.2f} x {height:.2f} points")

                # Create an overlay PDF with the grid using reportlab
                packet = io.BytesIO()
                can = canvas.Canvas(packet, pagesize=(width, height))

                # Set grid line style
                can.setStrokeColor(lightgrey)
                can.setLineWidth(0.5)

                # Set text style for coordinates
                can.setFillColor(darkgrey)
                can.setFont("Helvetica", 6)

                # Draw vertical grid lines and X-axis labels
                x = 0
                while x <= width:
                    can.line(x, 0, x, height)
                    if x > 0: # Don't label 0,0 twice
                         can.drawString(x + 2, 3, str(int(x)))
                    x += grid_spacing

                # Draw horizontal grid lines and Y-axis labels
                y = 0
                while y <= height:
                    can.line(0, y, width, y)
                    can.drawString(3, y + 2, str(int(y)))
                    y += grid_spacing

                # Save the canvas to the BytesIO buffer
                print(f"[INFO] Generated grid overlay for Page {page_num + 1}")
                can.save()
                packet.seek(0)

                # Create a PdfReader for the overlay
                overlay_pdf = PyPDF2.PdfReader(packet)
                overlay_page = overlay_pdf.pages[0]

                # Merge the overlay onto the original page
                page.merge_page(overlay_page)
                print(f"[INFO] Merged grid overlay onto Page {page_num + 1}")

                # Add the modified page to the writer
                writer.add_page(page)

            # Write the output file
            with open(output_pdf_path, 'wb') as output_file:
                writer.write(output_file)
            print(f"[SUCCESS] Successfully created gridded PDF: '{output_pdf_path}'")

    except FileNotFoundError:
        print(f"[ERROR] Input PDF not found: '{input_pdf_path}'")
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")

def convert_pdf_to_images(pdf_path: str, output_prefix: str, image_format: str = 'png'):
    """
    Converts each page of a PDF into an image file.

    Args:
        pdf_path (str): Path to the input PDF file.
        output_prefix (str): Prefix for the output image filenames.
        image_format (str): The desired image format (e.g., 'png', 'jpeg').
    """

    if not os.path.exists(pdf_path):
        print(f"[ERROR] PDF file not found for conversion: '{pdf_path}'")
        return

    print(f"\n[INFO] Starting PDF to image conversion for '{pdf_path}'...")
    print(f"[INFO] Output format: {image_format}")

    try:
        # Convert PDF to a list of PIL images
        images = convert_from_path(pdf_path)

        if not images:
            print("[WARNING] No pages found or converted from the PDF.")
            return

        # Save each page as an image
        for i, image in enumerate(images):
            page_num = i + 1
            image_filename = f"{output_prefix}{page_num}.{image_format}"
            image.save(image_filename, image_format.upper())
            print(f"[INFO] Saved Page {page_num} as '{image_filename}'")

        print(f"[SUCCESS] Successfully converted PDF to {len(images)} image(s).")

    except Exception as e:
        print(f"[ERROR] An error occurred during PDF to image conversion: {e}")
        print("[ERROR] Please ensure Poppler is installed and in your system's PATH.")

def main():
    """
    Main function to run the grid addition and image conversion processes.
    """
    input_pdf = "example.pdf"  # Default input PDF name
    output_pdf = "example_grid_patterned.pdf" # Default output PDF name
    image_prefix = "example_grid_patterned" # Prefix for image filenames
    image_format = "png" # Image format for AI analysis

    # Basic check if input file exists
    if not os.path.exists(input_pdf):
        print(f"[WARNING] Input file '{input_pdf}' not found in the current directory.")
        print("Please make sure 'example.pdf' exists or specify a different input file.")
        # Decide if you want to exit if the input PDF is missing
        # return # Uncomment to exit

    # Add grid to PDF
    add_grid_to_pdf(input_pdf, output_pdf, grid_spacing=50)

    # Convert the newly created gridded PDF to images
    # Check if the PDF was created successfully before converting
    if os.path.exists(output_pdf):
        convert_pdf_to_images(output_pdf, image_prefix, image_format)
    else:
        print(f"[WARNING] Output PDF '{output_pdf}' was not created. Skipping image conversion.")

if __name__ == "__main__":
    main()
