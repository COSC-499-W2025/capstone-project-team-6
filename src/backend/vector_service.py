import os

import ollama
from sqlalchemy.orm import Session

from backend.database_vector import Document, DocumentChunk, SessionLocal

_model = None  # loaded model (loaded once, reused each time)


def chunk_text(text, chunk_size=400):
    """Splits text into small chunks."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i : i + chunk_size])
        chunks.append(chunk)
    return chunks


def generate_embedding(text: str):
    """Generates a 768-dimensional embedding using Ollama (nomic-embed-text:latest)."""
    if not text or not text.strip():
        return [0.0] * 768
    try:
        response = ollama.embeddings(model="nomic-embed-text:latest", prompt=text)
        embedding = response["embedding"]

        if len(embedding) != 768:
            print(f"Warning: Expected 768 dims, got {len(embedding)}")

        return embedding

    except Exception as e:
        print(f"Embedding generation failed: {e}")
        return [0.0] * 768


# Insert document + chunks
def store_document(file_name, file_type, category, extracted_text):
    db: Session = SessionLocal()
    try:
        # Create new document entry
        doc = Document(file_name=file_name, file_type=file_type, category=category, extracted_text=extracted_text)
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Split into chunks
        chunks = chunk_text(extracted_text)
        for chunk_text_part in chunks:
            emb = generate_embedding(chunk_text_part)
            db.add(DocumentChunk(document_id=doc.id, chunk_text=chunk_text_part, embedding=emb))

        db.commit()
        print(f" Stored {len(chunks)} chunks for {file_name}")
    except Exception as e:
        print(f"Error storing document {file_name}: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    from backend.vector_service import store_document

    text = "This is a test document for verifying pgvector integration."
    store_document("test_doc.txt", "txt", "manual-test", text)
    print("Inserted test_doc.txt into database.")
