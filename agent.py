"""Backward-compatibility re-export facade for agent.py.

All agent construction logic has been split into stocksensei.core.agent.
"""
from __future__ import annotations

from stocksensei.core.agent import SYSTEM_PROMPT, TOOLS, get_agent, memory

__all__ = [
    "get_agent",
    "TOOLS",
    "SYSTEM_PROMPT",
    "memory",
]
