---
status: code-map
path: stocksensei/ui/terminal/renderers.py
language: python
updated: 2026-05-21
---

## Purpose
Owns terminal renderer dispatch while the concrete Rich renderers remain in `ui_blocks.py` during staged migration.

## Functions / Sections
- `Renderer` - callable type for terminal block renderers.
- `TERMINAL_RENDERERS` - maps supported block types to terminal rendering functions.
- `render_block(console, block)` - chooses a renderer based on block type and renders the block.
- `render_response(console, response)` - delegates full response rendering.

## Imports / Links
- [[ui_blocks]] - supplies block models and current Rich rendering implementations.
- external: rich - provides the terminal console type.
- external: typing - annotates renderer callables and dynamic blocks.
