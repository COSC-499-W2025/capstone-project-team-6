import os

from dotenv import load_dotenv
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

load_dotenv()

# Get connection string from .env
DATABASE_URL = os.getenv("VECTOR_DB_URL")

if not DATABASE_URL:
    raise ValueError("VECTOR_DB_URL not found in .env file")

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# Define the tables
class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    file_name = Column(String)
    file_type = Column(String)
    category = Column(String)
    extracted_text = Column(String)
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    chunk_text = Column(String)
    embedding = Column(Vector(1024))  # Cohere embed-v3 = 1024 dims
    document = relationship("Document", back_populates="chunks")


# Create tables if they don't exist
def init_db():
    Base.metadata.create_all(engine)
    print("Connected successfully and verified tables exist.")


if __name__ == "__main__":
    init_db()
