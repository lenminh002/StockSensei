---
status: code-map
path: command_prompt.py
language: python
updated: 2026-05-21
---

## Purpose
Defines the interactive prompt wrapper and slash-command completion metadata for the terminal CLI.

## Functions / Sections
- `COMMAND_SPECS` - maps slash commands to descriptions shown in autocomplete.
- `PROMPT_STYLE` - defines prompt-toolkit styling for the completion menu.
- `CommandPrompt.__init__()` - configures interactive prompt-toolkit sessions when running in a TTY.
- `CommandPrompt.prompt(prompt_text)` - reads user input with completion in TTY mode or plain input otherwise.

## Imports / Links
- external: sys - detects interactive stdin/stdout.
- external: prompt_toolkit - provides prompt sessions, completion, styling, and toolbar rendering.
