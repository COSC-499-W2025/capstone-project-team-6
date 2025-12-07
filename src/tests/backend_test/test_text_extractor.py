"""Tests for text_extractor OCR functions."""

from pathlib import Path

import pytest
from fpdf import FPDF
from PIL import Image, ImageDraw

from backend import database
from src.backend import text_extractor


def test_extract_text_from_plain_text(tmp_path):
    """Should read text directly from a .txt file."""
    txt_file = tmp_path / "simple.txt"
    txt_file.write_text("Direct text read test")
    text = text_extractor.extract_text(str(txt_file))
    assert "Direct text" in text


def test_extract_text_from_image(tmp_path):
    """Should extract text from an image using Tesseract."""
    img_path = tmp_path / "ocr_image.png"
    img = Image.new("RGB", (200, 80), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((10, 25), "OCR TEST", fill="black")
    img.save(img_path)

    text = text_extractor.extract_text(str(img_path))
    assert isinstance(text, str)
    assert len(text) > 0, "OCR should extract some text"
    # OCR may not be perfect, so check for parts of the expected text
    assert "test" in text.lower() or "ocr" in text.lower() or "rtest" in text.lower()


def test_extract_text_from_pdf(tmp_path):
    """Should convert PDF to images to OCR text."""
    pdf_path = tmp_path / "ocr_test.pdf"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt="PDF OCR Extraction Works!", ln=True)
    pdf.output(str(pdf_path))

    text = text_extractor.extract_text(str(pdf_path))
    assert isinstance(text, str)
    assert "pdf" in text.lower() or "works" in text.lower()


def test_extract_text_from_json_and_xml(tmp_path):
    """Should read text from text-based formats."""
    json_path = tmp_path / "sample.json"
    xml_path = tmp_path / "sample.xml"

    json_path.write_text('{"message": "Hello JSON!"}')
    xml_path.write_text("<root><msg>Hello XML!</msg></root>")

    json_text = text_extractor.extract_text(str(json_path))
    xml_text = text_extractor.extract_text(str(xml_path))

    assert "json" in json_text.lower()
    assert "xml" in xml_text.lower()
