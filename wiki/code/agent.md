---
status: code-map
path: agent.py
language: python
updated: 2026-05-21
---

## Purpose
Builds the LangGraph-backed agent with provider-specific model initialization, built-in tools, memory, and structured response schema.

## Functions / Sections
- `TOOLS` - default list of LangChain tool objects exposed to the agent.
- `SYSTEM_PROMPT` - instructs the model on financial data usage, structured responses, and visual block preferences.
- `memory` - process-level `MemorySaver` checkpointer for conversation state.
- `get_agent(model_name, langchain_provider, api_key, base_url, tools)` - creates and returns a configured LangChain agent.

## Imports / Links
- [[tools]] - supplies built-in market-data and visual-builder tools.
- [[ui_blocks]] - supplies the AI response JSON schema.
- external: langchain - creates agents and initializes chat models.
- external: langgraph - provides in-memory checkpointing.
