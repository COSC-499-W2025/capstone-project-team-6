"""Tests for in-memory OCR and text extraction functions."""
from io import BytesIO
from PIL import Image, ImageDraw
from src.backend import text_extractor
from fpdf import FPDF
from io import BytesIO


def test_extract_text_from_plain_text():
    """Should extract text directly from in-memory .txt bytes."""
    sample_bytes = b"Direct text read test"
    text = text_extractor.extract_text_from_bytes(sample_bytes, "simple.txt")
    assert "Direct text" in text


def test_extract_text_from_csv():
    """Should correctly join CSV content into readable text."""
    csv_bytes = b"name,age\nAlice,30\nBob,25"
    text = text_extractor.extract_text_from_bytes(csv_bytes, "data.csv")
    assert "Alice" in text and "Bob" in text


def test_extract_text_from_xml():
    """Should clean extra spaces in XML."""
    xml_bytes = b"<root>\n   <msg>Hello XML!</msg>\n</root>"
    text = text_extractor.extract_text_from_bytes(xml_bytes, "sample.xml")
    assert "<msg>Hello XML!</msg>" in text


def test_extract_text_from_json():
    """Should decode JSON as plain text."""
    json_bytes = b'{"message": "Hello JSON!"}'
    text = text_extractor.extract_text_from_bytes(json_bytes, "sample.json")
    assert "Hello JSON" in text


def test_extract_text_from_image():
    """Should extract text from an image using OCR (in-memory)."""
    # create a white image with text
    img = Image.new("RGB", (200, 80), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((10, 25), "OCR TEST", fill="black")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    text = text_extractor.extract_text_from_bytes(buffer.getvalue(), "ocr_image.png")
    assert isinstance(text, str)
    assert len(text) > 0, "OCR should extract some text"
    assert "test" in text.lower() or "ocr" in text.lower()

def test_extract_text_from_pdf(tmp_path):
    """Should convert a real generated PDF to images and extract text."""
    # Creates a temporary PDF file with text
    pdf_path = tmp_path / "ocr_test.pdf"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=14)  # built-in font, avoids warnings
    pdf.cell(200, 10, "PDF OCR Extraction Works!", ln=1)
    pdf.output(str(pdf_path))
    # Read PDF back into memory as bytes
    pdf_bytes = pdf_path.read_bytes()
    # Pass bytes to extractor
    text = text_extractor.extract_text_from_bytes(pdf_bytes, "ocr_test.pdf")
    assert isinstance(text, str)
    assert "pdf" in text.lower() or "works" in text.lower()
