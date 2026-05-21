---
status: code-map
path: config.py
language: python
updated: 2026-05-21
---

## Purpose
Loads, saves, validates, and interactively updates provider/model configuration.

## Functions / Sections
- `CONFIG_DIR`, `CONFIG_PATH`, `LEGACY_CONFIG_PATH` - define current and legacy config locations.
- `load_config()` - reads user configuration from the new path or legacy file.
- `save_config(config)` - writes config JSON with restricted file permissions.
- `_validate_api_key(provider_name, base_url, api_key)` - validates API keys where possible while tolerating network failures.
- `_add_provider_interactive(config)` - prompts for a provider, base URL, API key, and default model.
- `ensure_config()` - returns existing config or starts first-run setup.
- `current_provider_info(config)` - returns display name, model, LangChain provider, base URL, and API key.
- `switch_model_interactive(config)` - prompts for provider/model switching and persists the result.

## Imports / Links
- [[providers]] - supplies provider presets and provider-name mapping.
- [[utils]] - supplies color constants and terminal input helpers.
- external: json - reads and writes config JSON.
- external: os - resolves config paths and permissions.
- external: openai - validates OpenAI-compatible credentials.
- external: httpx - validates Anthropic and Gemini credentials when selected.
- external: typing - annotates optional config return values.
