import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import pytest
from src.backend.database_vector import SessionLocal, Document, DocumentChunk
from src.backend.vector_service import store_document

@pytest.fixture(scope="function", autouse=True)
def clean_db():
    """
    Cleans up the test tables before each test so results are isolated.
    """
    db = SessionLocal()
    db.query(DocumentChunk).delete()
    db.query(Document).delete()
    db.commit()
    db.close()
    yield
import os

from src.backend.database_vector import Document, DocumentChunk, SessionLocal
from src.backend.vector_service import store_document


def test_store_document_creates_entries(tmp_path):
    # Create a temporary text file
    sample_file = tmp_path / "test_doc.txt"
    sample_file.write_text("This is a test document for pgvector integration.")

    # Read file content and store it
    with open(sample_file, "r") as f:
        content = f.read()
    store_document("test_doc.txt", "txt", "pytest", content)

    # Check database entries
    db = SessionLocal()
    doc = db.query(Document).filter_by(file_name="test_doc.txt").first()
    chunks = db.query(DocumentChunk).filter_by(document_id=doc.id).all()
    db.close()

    assert doc is not None, "Document should be stored in the database"
    assert len(chunks) > 0, "At least one chunk should be stored"


def test_store_document_creates_chunks(tmp_path):
    sample_file = tmp_path / "multi_chunk.txt"
    # Make a long text that triggers chunking
    sample_file.write_text("word " * 1200)

    from src.backend.database_vector import DocumentChunk, SessionLocal
    from src.backend.vector_service import store_document

    with open(sample_file, "r") as f:
        content = f.read()

    store_document("multi_chunk.txt", "txt", "pytest", content)
    db = SessionLocal()
    chunks = db.query(DocumentChunk).all()
    assert len(chunks) > 1, "Should create multiple chunks for long text"


def test_store_empty_text():
    from src.backend.database_vector import Document, SessionLocal
    from src.backend.vector_service import store_document

    store_document("empty.txt", "txt", "pytest", "")
    db = SessionLocal()
    doc = db.query(Document).filter_by(file_name="empty.txt").first()
    assert doc is not None
    assert len(doc.chunks) == 0

def test_embedding_vector_dimension(tmp_path):
    """Checks that embeddings are 768-dimensional."""
    sample_file = tmp_path / "embed_test.txt"
    sample_file.write_text("The quick brown fox jumps over the lazy dog.")
    content = sample_file.read_text()

    store_document("embed_test.txt", "txt", "pytest", content)

    db = SessionLocal()
    doc = db.query(Document).filter_by(file_name="embed_test.txt").first()
    chunk = db.query(DocumentChunk).filter_by(document_id=doc.id).first()
    db.close()

    assert chunk is not None, "No chunk found for embed_test.txt"
    assert len(chunk.embedding) == 768, f"Expected 768-dim vector, got {len(chunk.embedding)}"

def test_embedding_consistency(tmp_path):
    """Ensures same input text produces identical embeddings."""
    text = "Consistency test sentence."
    store_document("same1.txt", "txt", "pytest", text)
    store_document("same2.txt", "txt", "pytest", text)

    db = SessionLocal()
    embeddings = [c.embedding for c in db.query(DocumentChunk).order_by(DocumentChunk.id).limit(2).all()]
    db.close()

    assert len(embeddings) == 2
    # Compare element-wise difference
    diff = sum(abs(a - b) for a, b in zip(embeddings[0], embeddings[1]))
    assert diff < 1e-5, f"Embeddings for identical text should match closely (diff={diff})"
