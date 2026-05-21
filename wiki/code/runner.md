---
status: code-map
path: runner.py
language: python
updated: 2026-05-21
---

## Purpose
Consumes agent/core event streams, renders terminal progress and eager visual blocks, and converts failures into safe structured responses.

## Functions / Sections
- `_get_loop()` - returns a process-lifetime asyncio loop for provider HTTP pool stability.
- `_close_loop()` - closes the shared event loop at process shutdown.
- `STATUS_LABELS` - fallback animated status labels.
- `TOOL_MESSAGES` - tool-specific start/end status messages.
- `_tool_message(name, phase)` - returns status text for a tool phase.
- `_block_key(block)` - creates stable JSON keys for block deduplication.
- `_extract_response_from_state(state)` - extracts a parsed `AIResponse` from final agent state.
- `_animate_status(stop_event, live, status_ref)` - animates the terminal status line.
- `_invoke_agent_stream(agent, user_input, run_config, live)` - streams raw agent events and renders tool-built blocks eagerly.
- `_classify_api_error(exc)` - maps common API failures to user-safe responses.
- `run_service(service, user_input, session, console)` - renders events from `StockSenseiService.ask_events`.
- `run_agent(agent, user_input, run_config, console)` - legacy direct-agent runner with response parsing and error handling.

## Imports / Links
- [[ui_blocks]] - parses responses, builds fallbacks, and renders legacy blocks.
- [[renderers]] - renders terminal-owned block output for core events.
- [[events]] - supplies typed core event classes.
- [[utils]] - stringifies LangChain message content.
- external: asyncio - drives async event streams.
- external: atexit - closes the shared event loop.
- external: json - creates stable block keys.
- external: random - picks status labels.
- external: traceback - logs unexpected failures.
- external: rich - renders live terminal status and text.
