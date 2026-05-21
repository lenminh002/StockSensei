---
status: code-map
path: utils.py
language: python
updated: 2026-05-21
---

## Purpose
Provides terminal color constants, interactive input helpers, menu selection, and message-content stringification.

## Functions / Sections
- `CYAN`, `YELLOW`, `GREEN`, `RED`, `RESET` - ANSI escape constants used by terminal output.
- `_plain(text)` - strips ANSI escape codes from prompts.
- `ask_text(prompt, default)` - reads text from prompt-toolkit in TTYs or stdin in non-interactive contexts.
- `pick_option(prompt, options)` - displays a numbered menu and returns the selected index.
- `stringify_message_content(raw)` - collapses LangChain message content into plain text.

## Imports / Links
- external: re - strips ANSI control sequences.
- external: sys - detects TTY state.
- external: prompt_toolkit - reads interactive text.
- external: typing - annotates dynamic message content.
