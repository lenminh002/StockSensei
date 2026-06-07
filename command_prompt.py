"""Backward-compatibility re-export facade for command_prompt.py.

All prompt-toolkit REPL logic has been moved to stocksensei.ui.terminal.command_prompt.
"""
from __future__ import annotations

from stocksensei.ui.terminal.command_prompt import COMMAND_SPECS, CommandPrompt

__all__ = [
    "COMMAND_SPECS",
    "CommandPrompt",
]
