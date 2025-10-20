import os
import sqlite3
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))
from database import create_database, DB_NAME  

DB_PATH = "src/backend/myapp.db"

def test_database_creation():
    """Check if database file is created."""
    create_database()
    assert os.path.exists(DB_NAME), "Database file should be created."

def test_table_exists():
    """Verify that the test_table is created in the database."""
    create_database()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_table';")
    result = cursor.fetchone()
    conn.close()
    assert result is not None, "test_table should exist in the database."
