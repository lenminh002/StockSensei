---
status: code-map
path: stocksensei/core/events.py
language: python
updated: 2026-05-21
---

## Purpose
Defines typed events emitted by StockSensei Core for UI-independent streaming.

## Functions / Sections
- `CoreEvent` - base event with type and session id.
- `StatusEvent` - progress/status message event.
- `ToolStartEvent` - tool-call start event.
- `ToolEndEvent` - tool-call completion event.
- `BlockEvent` - eager visual block event.
- `FinalEvent` - final structured response event.
- `ErrorEvent` - error event with optional fallback response.
- `StockSenseiEvent` - union of all core event types.

## Imports / Links
- external: pydantic - defines event models.
- external: typing - annotates dynamic payloads and literal types.
