---
status: code-map
path: stocksensei/core/service.py
language: python
updated: 2026-05-21
---

## Purpose
Coordinates configuration, registries, extensions, agent construction, and UI-agnostic event streaming.

## Functions / Sections
- `block_key(block)` - creates stable JSON keys for rendered-block deduplication.
- `StockSenseiService.__init__(...)` - initializes config, registries, extensions, hooks, and the agent.
- `StockSenseiService._build_agent()` - builds the agent from current provider info and registered tools.
- `StockSenseiService.new_session()` - creates a new core session.
- `StockSenseiService.rebuild_agent(config)` - updates config and rebuilds the agent.
- `StockSenseiService.ask_events(user_input, session)` - streams status, tool, block, final, and error events.
- `StockSenseiService.shutdown()` - runs extension shutdown hooks.
- `StockSenseiService.ask(user_input, session)` - returns only the final `AIResponse` from the event stream.

## Imports / Links
- [[agent]] - builds LangChain agents.
- [[config]] - supplies current provider details and initial config.
- [[runner]] - reuses status labels, tool messages, response extraction, and error classification.
- [[ui_blocks]] - supplies response and fallback models.
- [[utils]] - imports message stringification helper.
- [[events]] - defines emitted core event types.
- [[session]] - defines core session state.
- [[manager]] - loads and runs extensions.
- [[blocks]] - creates the visual block registry.
- [[commands]] - creates the command registry.
- [[tools]] - creates the tool registry.
- external: asyncio - supports async event and hook handling.
- external: json - serializes block keys.
- external: random - picks initial status labels.
- external: traceback - logs unexpected agent failures.
- external: typing - annotates dynamic values.
