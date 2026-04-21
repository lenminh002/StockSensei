from __future__ import annotations

from typing import Any

from rich.prompt import IntPrompt

CYAN = "\033[96m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


def pick_option(prompt: str, options: list[str]) -> int:
    """Display a numbered menu and return the 0-based index of the user's choice."""
    for i, opt in enumerate(options, 1):
        print(f"  {CYAN}{i}.{RESET} {opt}")
    while True:
        choice = IntPrompt.ask(f"{CYAN}{prompt}{RESET}")
        if 1 <= choice <= len(options):
            return choice - 1
        print(f"{RED}Please enter a number between 1 and {len(options)}.{RESET}")


def stringify_message_content(raw: Any) -> str:
    """Collapse LangChain message content into plain text for fallback rendering."""
    if isinstance(raw, str):
        return raw
    if isinstance(raw, list):
        parts = []
        for part in raw:
            if isinstance(part, dict):
                parts.append(part.get("text", ""))
            else:
                parts.append(str(part))
        return " ".join(p for p in parts if p)
    return str(raw)
