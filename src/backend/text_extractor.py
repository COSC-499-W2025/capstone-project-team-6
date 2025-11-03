"""This file handles OCR and general text extraction"""

from pathlib import Path
import pytesseract
from PIL import Image


from io import BytesIO
from pdf2image import convert_from_bytes
import re
import csv

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
