"""Backward-compatibility re-export facade for providers.py.

All preset maps and functions have been moved to stocksensei.core.providers.
"""
from __future__ import annotations

from stocksensei.core.providers import (
    LANGCHAIN_PROVIDER_MAP,
    PROVIDER_PRESETS,
    get_langchain_provider,
)

__all__ = [
    "PROVIDER_PRESETS",
    "LANGCHAIN_PROVIDER_MAP",
    "get_langchain_provider",
]
