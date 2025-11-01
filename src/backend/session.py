"""Session management for the CLI."""

import json
from pathlib import Path
from typing import Dict, Optional

SESSION_FILE = Path.home() / ".mda-session.json"

def save_session(username: str) -> None:
    """Save session data to file."""
    session_data = {
        "logged_in": True,
        "username": username
    }
    SESSION_FILE.write_text(json.dumps(session_data))

def clear_session() -> None:
    """Clear the session data."""
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()

def get_session() -> Dict:
    """Get the current session data."""
    if not SESSION_FILE.exists():
        return {"logged_in": False, "username": None}
    try:
        return json.loads(SESSION_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        clear_session()
        return {"logged_in": False, "username": None}