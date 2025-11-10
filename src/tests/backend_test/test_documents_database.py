"""Tests for the documents database helper module."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

from src.backend import documents_database as docs_db


@pytest.fixture
def temp_documents_db(tmp_path: Path):
    db_file = tmp_path / "documents.db"
    previous = docs_db.set_db_path(db_file)
    docs_db.reset_db()
    yield db_file
    docs_db.set_db_path(previous)


def test_initialize_creates_documents_table(temp_documents_db: Path):
    with sqlite3.connect(temp_documents_db) as conn:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Documents';")
        assert cur.fetchone() is not None


def test_save_document_stores_counts_and_text(temp_documents_db: Path):
    counts = {"code": 5, "docs": 2, "tests": 1, "configs": 3, "other": 4}
    doc_id = docs_db.save_document(
        "archive.zip",
        "Sample extracted text",
        category_counts=counts,
        uploaded_at=datetime.now().isoformat(),
    )
    assert isinstance(doc_id, int)

    with docs_db.get_connection() as conn:
        row = conn.execute(
            """
            SELECT file_name, extracted_text, code_files, doc_files, test_files,
                   config_files, other_files
            FROM Documents
            WHERE id = ?
            """,
            (doc_id,),
        ).fetchone()

        assert row["file_name"] == "archive.zip"
        assert "sample" in row["extracted_text"].lower()
        assert row["code_files"] == 5
        assert row["doc_files"] == 2
        assert row["test_files"] == 1
        assert row["config_files"] == 3
        assert row["other_files"] == 4

