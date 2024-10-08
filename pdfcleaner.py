# -*- coding: utf-8 -*-

# Import necessary libraries with error handling
try:
    from PyPDF2 import PdfReader, PdfWriter
    from PyPDF2.generic import RectangleObject
    from reportlab.pdfgen import canvas
    from io import BytesIO
except ImportError as e:
    missing_lib = str(e).split("'")[1]
    print(f"{missing_lib} library is not installed. Install it by running:")
    if missing_lib == 'PyPDF2':
        print("pip install PyPDF2 reportlab")
    elif missing_lib == 'reportlab':
        print("pip install reportlab")
    exit(1)

import argparse
import os

def parse_page_ranges(page_range_str):
    """Parse the string of page ranges into a list of individual page numbers."""
    pages_to_delete = set()
    ranges = page_range_str.split(',')
    
    for part in ranges:
        if '-' in part:
            start, end = map(int, part.split('-'))
            pages_to_delete.update(range(start-1, end))  # Pages are zero-indexed in PyPDF2
        else:
            pages_to_delete.add(int(part) - 1)  # Pages are zero-indexed in PyPDF2
    
    return sorted(pages_to_delete)

def create_redacted_page(media_box):
    """Create a single-page PDF with 'Redacted' text, matching the original PDF page size."""
    # Create a buffer for the redacted page
    buffer = BytesIO()
    
    # Get the exact width and height of the page to be redacted
    width = media_box.width
    height = media_box.height
    
    # Create a new canvas with the same size as the page to be redacted
    c = canvas.Canvas(buffer, pagesize=(width, height))
    c.setFont("Helvetica", 40)
    
    # Draw "Redacted" text centered on the page
    c.drawCentredString(width / 2, height / 2, "Redacted")
    c.save()

    # Move buffer pointer back to the beginning
    buffer.seek(0)

    # Return the redacted page as a PDF object
    reader = PdfReader(buffer)
    return reader.pages[0]

def delete_or_replace_pages(input_file, page_range_str, replace_with_redacted):
    """Remove specified pages or replace with 'Redacted' page from the input PDF file."""
    # Check if file exists
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        return

    # Parse the page range string
    pages_to_delete = parse_page_ranges(page_range_str)
    print(f"Pages to delete: {pages_to_delete}")

    # Read the PDF
    try:
        reader = PdfReader(input_file)
    except Exception as e:
        print(f"Error reading PDF file: {e}")
        return

    # Create a PDF writer to write the cleaned file
    writer = PdfWriter()

    # Loop through the pages and either delete or replace with 'Redacted'
    num_pages = len(reader.pages)
    for i in range(num_pages):
        if i in pages_to_delete:
            if replace_with_redacted:
                print(f"Replacing page {i+1} with 'Redacted' page.")
                media_box = reader.pages[i].mediabox
                redacted_page = create_redacted_page(RectangleObject(media_box))
                writer.add_page(redacted_page)
            else:
                print(f"Deleting page {i+1}.")
        else:
            writer.add_page(reader.pages[i])

    # Generate the output filename
    output_file = os.path.splitext(input_file)[0] + ".redacted.pdf"

    # Write the cleaned PDF
    with open(output_file, "wb") as f:
        writer.write(f)

    print(f"Output saved to '{output_file}'.")

def main():
    # Argument parser
    parser = argparse.ArgumentParser(description="Delete specific pages from a PDF file or replace them with 'Redacted'.")
    parser.add_argument("inputfile", help="The input PDF file")
    parser.add_argument("page_filter", help="Pages to delete in the format '12,15-18,22'")
    parser.add_argument("--replace", action="store_true", help="Replace deleted pages with 'Redacted' instead of removing them")

    # Parse the arguments
    args = parser.parse_args()

    # Delete or replace the specified pages
    delete_or_replace_pages(args.inputfile, args.page_filter, args.replace)

if __name__ == "__main__":
    main()
