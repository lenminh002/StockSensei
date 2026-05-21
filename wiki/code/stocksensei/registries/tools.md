---
status: code-map
path: stocksensei/registries/tools.py
language: python
updated: 2026-05-21
---

## Purpose
Registers built-in and extension-provided LangChain tools with collision handling and extension namespacing.

## Functions / Sections
- `RegisteredTool` - dataclass storing registered tool metadata.
- `ToolRegistry.__init__()` - initializes the registry store.
- `ToolRegistry.register(tool, name, extension_id)` - registers a tool and namespaces extension collisions.
- `ToolRegistry.register_many(tools, extension_id)` - registers multiple tools.
- `ToolRegistry.tools()` - returns the tool objects for agent construction.
- `ToolRegistry.entries()` - returns registry metadata entries.
- `create_builtin_tool_registry()` - seeds the registry from `agent.TOOLS`.

## Imports / Links
- [[agent]] - supplies built-in `TOOLS`.
- external: dataclasses - defines registry entries.
- external: typing - annotates arbitrary tool objects and iterables.
