"""Shared token storage for authentication across all modules.
"""

from datetime import datetime
from typing import Any, Dict, Iterator, Tuple


class _PersistentTokenStorage:
    """Dict-like token store backed by SQLite."""

    def __init__(self) -> None:
        self._data: Dict[str, Dict[str, Any]] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            try:
                from backend.database import (init_db,
                                              load_active_tokens_from_db)

                init_db()
                self._data = load_active_tokens_from_db()
            except Exception:
                pass
            self._loaded = True

    def __contains__(self, token: object) -> bool:
        self._ensure_loaded()
        return token in self._data

    def __getitem__(self, token: str) -> Dict[str, Any]:
        self._ensure_loaded()
        return self._data[token]

    def __setitem__(self, token: str, data: Dict[str, Any]) -> None:
        self._ensure_loaded()
        self._data[token] = data
        try:
            from backend.database import save_token_to_db

            save_token_to_db(
                token,
                data["username"],
                data["created_at"].isoformat() if isinstance(data["created_at"], datetime) else str(data["created_at"]),
                data["expires_at"].isoformat() if isinstance(data["expires_at"], datetime) else str(data["expires_at"]),
            )
        except Exception:
            pass

    def __delitem__(self, token: str) -> None:
        self._ensure_loaded()
        del self._data[token]
        try:
            from backend.database import delete_token_from_db

            delete_token_from_db(token)
        except Exception:
            pass

    def clear(self) -> None:
        self._ensure_loaded()
        self._data.clear()
        try:
            from backend.database import clear_tokens_from_db

            clear_tokens_from_db()
        except Exception:
            pass

    def items(self) -> Iterator[Tuple[str, Dict[str, Any]]]:
        self._ensure_loaded()
        return self._data.items()


active_tokens: _PersistentTokenStorage = _PersistentTokenStorage()
