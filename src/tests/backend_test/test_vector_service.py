import os
from src.backend.database_vector import SessionLocal, Document, DocumentChunk
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

    from src.backend.vector_service import store_document
    from src.backend.database_vector import SessionLocal, DocumentChunk

    with open(sample_file, "r") as f:
        content = f.read()

    store_document("multi_chunk.txt", "txt", "pytest", content)
    db = SessionLocal()
    chunks = db.query(DocumentChunk).all()
    assert len(chunks) > 1, "Should create multiple chunks for long text"

def test_store_empty_text():
    from src.backend.vector_service import store_document
    from src.backend.database_vector import SessionLocal, Document

    store_document("empty.txt", "txt", "pytest", "")
    db = SessionLocal()
    doc = db.query(Document).filter_by(file_name="empty.txt").first()
    assert doc is not None
    assert len(doc.chunks) == 0


