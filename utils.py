from __future__ import annotations

import re
import sys
from typing import Any

from prompt_toolkit import prompt as pt_prompt

CYAN = "\033[96m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _plain(text: str) -> str:
    return ANSI_RE.sub("", text)


def ask_text(prompt: str, default: str | None = None) -> str:
    """Read interactive text in shells including nushell.

    Prefer prompt-toolkit for real TTYs because nushell can behave poorly with
    Rich prompts in some terminal setups. Fall back to plain stdin for pipes.
    """
    suffix = f" [{default}]" if default is not None else ""
    text = f"{_plain(prompt)}{suffix}: "
    if sys.stdin.isatty() and sys.stdout.isatty():
        value = pt_prompt(text)
        return value if value or default is None else default
    try:
        print(text, end="", flush=True)
        value = sys.stdin.readline().rstrip("\n")
        return value if value or default is None else default
    except (EOFError, OSError) as exc:
        raise RuntimeError("No interactive input stream available. Run StockSensei in a real terminal.") from exc


def pick_option(prompt: str, options: list[str]) -> int:
    """Display a numbered menu and return the 0-based index of the user's choice."""
    for i, opt in enumerate(options, 1):
        print(f"  {CYAN}{i}.{RESET} {opt}")
    while True:
        raw = ask_text(f"{CYAN}{prompt}{RESET}").strip()
        try:
            choice = int(raw)
        except ValueError:
            print(f"{RED}Please enter a number between 1 and {len(options)}.{RESET}")
            continue
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
