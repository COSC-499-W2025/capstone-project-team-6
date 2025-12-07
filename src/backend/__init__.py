"""Mining Digital Artifacts (MDA) package initialization."""

from .database import (UserAlreadyExistsError, authenticate_user, create_user,
                       get_db_path, get_user, initialize, set_db_path)
from .shell import MDAShell
from .traversal import Folder_traversal_fs

__all__ = [
    # Traversal functionality
    "Folder_traversal_fs",
    # Database functionality
    "initialize",
    "create_user",
    "authenticate_user",
    "get_user",
    "UserAlreadyExistsError",
    "set_db_path",
    "get_db_path",
    # Shell
    "MDAShell",
]
