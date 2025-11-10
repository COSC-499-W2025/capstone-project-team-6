import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine, JSON
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

try:
    from pgvector.sqlalchemy import Vector as PgVector
except ImportError:  # pragma: no cover
    PgVector = None

load_dotenv()

DEFAULT_SQLITE_PATH = Path(__file__).resolve().parent.parent / "vector.db"

DATABASE_URL = os.getenv("VECTOR_DB_URL")
if not DATABASE_URL:
    DATABASE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH}"

USE_SQLITE = DATABASE_URL.startswith("sqlite")

if not USE_SQLITE and PgVector is None:
    raise ImportError("pgvector is required when using a non-SQLite vector database")

VECTOR_DIMENSION = 1024
VECTOR_COLUMN_TYPE = JSON if USE_SQLITE else PgVector(VECTOR_DIMENSION)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


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
    embedding = Column(VECTOR_COLUMN_TYPE)
    document = relationship("Document", back_populates="chunks")


def init_db() -> None:
    Base.metadata.create_all(engine)
    print("Connected successfully and verified tables exist.")


init_db()


if __name__ == "__main__":
    init_db()
