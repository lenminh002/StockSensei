---
status: code-map
path: stocksensei/core/providers.py
language: python
updated: 2026-05-21
---

## Purpose
Wraps legacy provider configuration functions behind a small core service facade.

## Functions / Sections
- `ProviderService.__init__(config)` - stores config or loads/creates it.
- `ProviderService.current_info()` - returns current provider/model connection details.
- `ProviderService.switch_interactive()` - runs interactive provider/model switching.
- `ProviderService.save()` - persists provider configuration.
- `__all__` - exports provider service and config helper names.

## Imports / Links
- [[config]] - reuses legacy provider configuration helpers and config paths.
