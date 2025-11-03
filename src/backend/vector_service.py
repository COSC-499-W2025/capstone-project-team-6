import os

from sqlalchemy.orm import Session

from backend.database_vector import Document, DocumentChunk, SessionLocal


def chunk_text(text, chunk_size=500):
    """Splits text into small chunks."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i : i + chunk_size])
        chunks.append(chunk)
    return chunks


# Placeholder for embeddings (we will replace it with a real embedding model later)
def generate_embedding(text):
    """
    Placeholder embedding generator.
    Replace later with Cohere / OpenAI / LlamaStack embedding API.
    """
    return [0.0] * 1024  # Dummy vector with 1024 dimensions


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
    finally:
        db.close()


# Manual tests
if __name__ == "__main__":
    sample_text = "This is a sample text that will be split into multiple chunks for testing."
    store_document("test.txt", "txt", "sample", sample_text)

if __name__ == "__main__":
    with open("/Users/harjotsahota/Desktop/sample.txt", "r") as f:
        content = f.read()
    store_document("sample.txt", "txt", "manual-test", content)
