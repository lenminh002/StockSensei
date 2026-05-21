---
status: code-map
path: stocksensei/extensions/manager.py
language: python
updated: 2026-05-21
---

## Purpose
Loads, trusts, activates, tracks, and runs StockSensei extensions while isolating failures.

## Functions / Sections
- `ExtensionRecord` - dataclass storing extension diagnostics and hook state.
- `ExtensionManager.__init__(config, tool_registry, block_registry)` - stores registries and initializes lifecycle hook buckets.
- `ExtensionManager._project_trusted(source)` - prompts for project-local extension trust and persists the choice.
- `ExtensionManager.load_all()` - discovers, loads, activates, de-duplicates, disables, or records failed extensions.
- `ExtensionManager.run_hook_sync(hook_name, ...)` - runs a hook synchronously through asyncio.
- `ExtensionManager.run_hook(hook_name, ...)` - runs registered hook handlers and disables extensions that fail.
- `ExtensionManager.diagnostics()` - returns loaded, disabled, and failed extension records.

## Imports / Links
- [[config]] - persists trust decisions.
- [[api]] - creates extension API objects and checks API compatibility.
- [[discovery]] - discovers and loads extension sources.
- [[utils]] - prompts for project-local extension trust.
- external: asyncio - runs async activation and hooks.
- external: dataclasses - defines diagnostic records.
- external: pathlib - resolves project extension trust paths.
- external: typing - annotates dynamic registry and hook values.
