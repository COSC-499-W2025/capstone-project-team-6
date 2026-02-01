"""Shared token storage for authentication across all modules."""

from typing import Any, Dict

# Single source of truth for active authentication tokens
active_tokens: Dict[str, Dict[str, Any]] = {}
