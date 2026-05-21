---
status: code-map
path: providers.py
language: python
updated: 2026-05-21
---

## Purpose
Stores built-in AI provider presets and maps StockSensei provider names to LangChain provider identifiers.

## Functions / Sections
- `PROVIDER_PRESETS` - provider base URLs and default model lists.
- `LANGCHAIN_PROVIDER_MAP` - mapping from StockSensei provider keys to LangChain provider names.
- `get_langchain_provider(provider_name)` - returns the LangChain provider identifier, defaulting to OpenAI-compatible behavior.
