"""Mining Digital Artifacts (MDA) package initialization."""

from .traversal import Folder_traversal_fs
from .database import (
    initialize,
    create_user,
    authenticate_user,
    get_user,
    UserAlreadyExistsError,
    set_db_path,
    get_db_path,
)
from .shell import MDAShell

__all__ = [
    # Traversal functionality
    'Folder_traversal_fs',
    
    # Database functionality
    'initialize',
    'create_user',
    'authenticate_user',
    'get_user',
    'UserAlreadyExistsError',
    'set_db_path',
    'get_db_path',
    
    # Shell
    'MDAShell',
]
