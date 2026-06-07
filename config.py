"""Backward-compatibility re-export facade for config.py.

All configuration logic has been split into stocksensei.core.config and stocksensei.ui.terminal.config.
"""
from __future__ import annotations

from stocksensei.core.config import (
    CONFIG_DIR,
    CONFIG_PATH,
    LEGACY_CONFIG_PATH,
    current_provider_info,
    ensure_config,
    load_config,
    save_config,
)
from stocksensei.ui.terminal.config import switch_model_interactive

__all__ = [
    "CONFIG_DIR",
    "CONFIG_PATH",
    "LEGACY_CONFIG_PATH",
    "load_config",
    "save_config",
    "ensure_config",
    "current_provider_info",
    "switch_model_interactive",
]
