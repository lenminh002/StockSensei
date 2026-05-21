---
status: code-map
path: main.py
language: python
updated: 2026-05-21
---

## Purpose
Runs the terminal CLI loop, handles slash commands, and sends user prompts through the shared StockSensei service.

## Functions / Sections
- `_show_help()` - prints command help and usage examples with Rich Markdown.
- `main()` - initializes configuration, service, session, prompt handling, command routing, and response rendering.

## Imports / Links
- [[command_prompt]] - provides interactive slash-command prompting.
- [[config]] - provides interactive provider/model switching.
- [[runner]] - runs the service event stream from the terminal.
- [[service]] - provides the UI-agnostic StockSensei core service.
- [[renderers]] - renders core responses in the terminal UI.
- [[utils]] - supplies ANSI color constants.
- external: warnings - suppresses selected startup warnings.
- external: dotenv - loads local environment configuration.
- external: rich - renders console and markdown output.
