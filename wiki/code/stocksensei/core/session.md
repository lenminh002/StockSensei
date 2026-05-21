---
status: code-map
path: stocksensei/core/session.py
language: python
updated: 2026-05-21
---

## Purpose
Defines StockSensei core session state and LangGraph thread configuration.

## Functions / Sections
- `StockSenseiSession` - dataclass that owns session id and thread id.
- `StockSenseiSession.__post_init__()` - defaults the thread id to the session id.
- `StockSenseiSession.run_config` - exposes LangGraph thread configuration.
- `StockSenseiSession.reset()` - generates a fresh session/thread id.
- `new_session()` - creates a new `StockSenseiSession`.

## Imports / Links
- external: dataclasses - defines the session dataclass.
- external: uuid - generates unique session ids.
