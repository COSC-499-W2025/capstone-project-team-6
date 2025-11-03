"""This file handles OCR and general text extraction"""

from pathlib import Path
import pytesseract
from pdf2image import convert_from_path
from PIL import Image


from io import BytesIO
from pdf2image import convert_from_bytes
import json
import re
import csv

# OLD ---------------------------------------------------------------------------------------------------

# Supported file types
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif"}
PDF_EXTS = {".pdf"}
TEXT_EXTS = {".txt", ".csv", ".json", ".xml"}

def extract_text(file_path: str) -> str:
    """ Decide how to extract text based on file extension. """
    ext = Path(file_path).suffix.lower()            # gets file type
    if ext in IMAGE_EXTS:
        return extract_text_from_image(file_path)
    elif ext in PDF_EXTS:
        return extract_text_from_pdf(file_path)
    elif ext in TEXT_EXTS:
        return read_text_file(file_path)

def extract_text_from_image(file_path: str) -> str:
    """Use Tesseract to extract text from an image"""
    try:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        print(f"Image extraction failed: {e}")
        return ""

def extract_text_from_pdf(file_path: str) -> str:
    """Convert PDF pages to images and run OCR on each."""
    try:
        pages = convert_from_path(file_path)
        all_text = ""
        for page in pages:
            text = pytesseract.image_to_string(page)
            all_text += text + "\n"
        return all_text.strip()
    except Exception as e:
        print(f"PDF extraction failed: {e}")
        return ""

def read_text_file(file_path: str) -> str:
    """Read plain text-based files directly."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    except Exception as e:
        print(f"Text file read failed: {e}")
        return ""

# ---------------------------------------------------------------------------------------------------

def extract_text_from_bytes(file_bytes: bytes, filename: str) -> str:
    """ Extracts readable text from in memory bytes """
    ext = Path(filename).suffix.lower()

    # Text-based formats
    if ext in [".txt", ".csv", ".json", ".xml"]:
        text = file_bytes.decode("utf-8", errors="ignore")      # Converts bytes into readable text
        if ext == ".xml":
            cleaned = re.sub(r">\s+<", "><", text)
            return cleaned.strip()
        elif ext == ".csv":
            return "\n".join(
                [" ".join(row) for row in csv.reader(text.splitlines())]
            )
        return text.strip()

    elif ext == ".pdf":
        pages = convert_from_bytes(file_bytes)
        text = ""
        for page in pages:
            text += pytesseract.image_to_string(page)
        return text.strip()

    elif ext in [".jpg", ".jpeg", ".png", ".gif"]:
        image = Image.open(BytesIO(file_bytes))
        return pytesseract.image_to_string(image).strip()
