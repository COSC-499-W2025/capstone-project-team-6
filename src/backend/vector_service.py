import os

from sqlalchemy.orm import Session
from backend.database_vector import Document, DocumentChunk, SessionLocal
from sentence_transformers import SentenceTransformer

_model = None               # loaded model (loaded once, reused each time)


def chunk_text(text, chunk_size=400):
    """Splits text into small chunks."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i : i + chunk_size])
        chunks.append(chunk)
    return chunks


def get_embedding_model():
    """
    Loads the embedding model on first call.
    Reuses it for all future embeddings to save time and memory.
    """
    global _model
    if _model is None:
        print("Loading embedding model for the first time...")
        _model = SentenceTransformer( "jinaai/jina-embeddings-v3", trust_remote_code=True)
        print("Model loaded successfully.")
    return _model


def generate_embedding(text: str):
    """
    Generates a 1024-dimensional embedding using Jina v3 (local Hugging Face model).
    """
    # Handle empty input
    #if not text or not text.strip():
     #   return [0.0] * 1024

    model = get_embedding_model()
    embedding = model.encode(text, convert_to_tensor=False)

    #  Ensure correct vector size
    if len(embedding) != 1024:
        print(f"Warning: Expected 1024 dims, got {len(embedding)}")
    
    return embedding.tolist()


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
    sample_text = "This is a sample text that will be split into multiple chunks for testing."
    store_document("test.txt", "txt", "sample", sample_text)

    sample_path = "/Users/harjotsahota/Desktop/sample.txt"
    if os.path.exists(sample_path):
        with open(sample_path, "r") as f:
            content = f.read()
        store_document("sample.txt", "txt", "manual-test", content)