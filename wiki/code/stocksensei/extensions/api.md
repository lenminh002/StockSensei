---
status: code-map
path: stocksensei/extensions/api.py
language: python
updated: 2026-05-21
---

## Purpose
Defines the public API object trusted extensions use to register tools, visual blocks, and lifecycle hooks.

## Functions / Sections
- `SUPPORTED_API_MAJOR` - supported extension API major version.
- `HookResult` - dataclass for hook outcomes that can block or return a response.
- `Hook` - callable type for sync or async hook handlers.
- `ExtensionAPI` - dataclass passed to extension `activate(api)` functions.
- `ExtensionAPI.register_tool(tool, name)` - registers a tool with extension-aware namespacing.
- `ExtensionAPI.register_block(block_type, model, fallback_field)` - registers a custom Visual Block schema.
- `ExtensionAPI.on(hook_name, handler)` - registers a lifecycle hook handler.
- `assert_api_compatible(api_version)` - rejects unsupported extension API major versions.

## Imports / Links
- external: dataclasses - defines API dataclasses.
- external: pydantic - types custom block schema models.
- external: typing - annotates callables and dynamic values.
