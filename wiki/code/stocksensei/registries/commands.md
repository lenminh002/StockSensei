---
status: code-map
path: stocksensei/registries/commands.py
language: python
updated: 2026-05-21
---

## Purpose
Registers slash-command metadata for built-in and future command handlers.

## Functions / Sections
- `CommandSpec` - dataclass storing command name, description, and optional handler.
- `CommandRegistry.__init__()` - initializes command storage.
- `CommandRegistry.register(name, description, handler)` - registers a slash command.
- `CommandRegistry.specs()` - returns command descriptions keyed by command name.
- `CommandRegistry.entries()` - returns full command specs.
- `create_builtin_command_registry()` - seeds the registry from terminal command specs and ensures `/extensions`.

## Imports / Links
- [[command_prompt]] - supplies built-in command descriptions.
- external: dataclasses - defines command specs.
- external: typing - annotates optional command handlers.
