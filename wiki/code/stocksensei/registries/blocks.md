---
status: code-map
path: stocksensei/registries/blocks.py
language: python
updated: 2026-05-21
---

## Purpose
Registers Visual Block schemas and fallback metadata for built-in and extension-provided block types.

## Functions / Sections
- `RegisteredBlock` - dataclass storing block type, model, fallback field, and extension id.
- `BlockRegistry.__init__()` - initializes the registry store.
- `BlockRegistry.register(block_type, model, fallback_field, extension_id)` - registers and namespaces a block type.
- `BlockRegistry.validate(block)` - validates known block types and passes unknown blocks through.
- `BlockRegistry.entries()` - returns registered block metadata.
- `create_builtin_block_registry()` - seeds the registry with built-in UI block schemas.

## Imports / Links
- [[ui_blocks]] - supplies built-in Visual Block models.
- external: dataclasses - defines registry entries.
- external: pydantic - types block schema models.
- external: typing - annotates dynamic block payloads.
