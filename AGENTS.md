# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

StockSensei is a Python stock research assistant with a first-class terminal CLI today and a planned Web UI over the same shared core. It uses a LangChain/LangGraph agent with pluggable AI providers (OpenAI, Anthropic, Gemini, Groq, DeepSeek, OpenRouter, Ollama, or any OpenAI-compatible endpoint) to answer financial questions using real-time yfinance data.

## Commands

```bash
# Install dependencies
uv sync

# Run locally (development)
uv run main.py

# Install globally as CLI tool
uv tool install git+https://github.com/lenminh002/StockSensei.git
stocksensei

# Upgrade global install
uv tool upgrade stocksensei
# Force reinstall if upgrade misses latest changes:
uv tool install --force git+https://github.com/lenminh002/StockSensei.git

# Build distributable wheel
uv build
```

No test suite or linter is configured.

## Architecture

```
Current flat-module architecture:

main.py → config.py     (provider/model selection, currently ~/.stocksensei_config.json)
        → providers.py  (PROVIDER_PRESETS, LANGCHAIN_PROVIDER_MAP)
        → agent.py      (LangGraph agent construction, system prompt)
        → runner.py     (async streaming loop, status animation, block deduplication)
        → tools.py      (yfinance data tools + visual builder tools)
        → ui_blocks.py  (Pydantic block models, block builders, terminal rendering)
        → utils.py      (ANSI constants, pick_option, stringify_message_content)
        → command_prompt.py  (prompt-toolkit REPL with slash-command completion)

Target extensible architecture:

stocksensei/                 (new package, introduced with staged compatibility wrappers)
  core/                      (StockSensei Core service, sessions, provider service, typed event stream)
  registries/                (tool registry, Visual Block schema/fallback registry, command registry)
  extensions/                (trusted Python extension discovery/activation/API)
  ui/terminal/               (Terminal UI commands, status rendering, Rich block renderers)
  ui/web/                    (future FastAPI + SSE Web UI)

Terminal UI and Web UI must consume the same StockSensei Core. Do not add web-only stock logic or duplicate agent/tool behavior in a UI layer.
```

**`main.py`** — CLI entry point and REPL loop. On startup: loads config, builds the agent, creates a fresh thread ID. Commands (`/models`, `/clear`, `/help`, `/quit`) are currently handled before the agent is invoked. `/clear` resets memory by generating a new thread ID via `_new_run_config()` and clears the terminal. Switching providers (`/models`) also rebuilds the agent and resets the thread. Agent invocation is delegated to `run_agent()` in `runner.py`. Target direction: move semantic commands and provider/session behavior into StockSensei Core so CLI and future Web UI share them.

**`runner.py`** — Async streaming and agent invocation. `run_agent()` is the public entry point called from `main.py`. Internally, `_invoke_agent_stream` streams LangGraph events via `astream_events`, renders visual blocks eagerly as tool calls complete, and returns the final state. `_animate_status` cycles a status line while the agent works. `TOOL_MESSAGES` maps each tool name to its start/end status strings. Target direction: extract a UI-agnostic async event stream from StockSensei Core (`status`, `tool_start`, `tool_end`, `block`, `final`, `error`) and let Terminal UI render events.

**`providers.py`** — Static provider data only: `PROVIDER_PRESETS` (base URLs and model lists) and `LANGCHAIN_PROVIDER_MAP` (provider name → LangChain provider string). Providers absent from the map default to `"openai"` (OpenAI-compatible). To add a built-in provider, add entries to both dicts here.

**`config.py`** — Provider/model management logic. Currently persists config to `~/.stocksensei_config.json` (chmod 600) with structure `{default_provider, providers: {name: {base_url, api_key, default_model, models[]}}}`. Target direction: migrate user config to `~/.config/stocksensei/config.json` with backward-compatible reads from the legacy path. Provider config belongs in StockSensei Core; CLI/Web only present selection flows. API key validation calls `openai.OpenAI.models.list()`; network errors are silently accepted to avoid blocking users.

**`agent.py`** — Builds the LangGraph-backed agent via `langchain.agents.create_agent`. Key details:
- Module-level `MemorySaver()` checkpointer; thread ID (`stocksensei_{uuid4()}`) is regenerated on provider switch or `/clear` to reset memory.
- Gemini requires `google_api_key` kwarg instead of `api_key`/`base_url`; Ollama requires only `base_url`.
- `SYSTEM_PROMPT` encodes all output-formatting rules and visual guidance (which visual tools to prefer for which query types).
- `AI_RESPONSE_SCHEMA` (from `ui_blocks.py`) is passed as `response_format` to enforce structured output.

**`tools.py`** — Two layers of LangChain `@tool` functions, all returning dicts (never raise):
- **Data tools**: `get_price`, `get_stock_summary`, `get_company_summary`, `get_historical_data`, `get_news`, `compare_stocks`, `compare_stocks_summary` — wrap yfinance and return normalized dicts.
- **Visual builder tools**: `build_snapshot_card_visual`, `build_52w_range_visual`, `build_price_comparison_visual`, `build_summary_comparison_visual`, `build_price_chart_visual`, `build_change_chart_visual`, `build_market_cap_chart_visual`, `build_history_chart_visual`, `build_news_visual` — call block-builder functions from `ui_blocks.py` and return `{"block": ...}`.
- `compare_stocks` / `compare_stocks_summary` accept comma-separated ticker strings (e.g. `"AAPL,TSLA"`).
- Current tool additions require editing `tools.py`, `agent.py`, and `runner.py`. Target direction: built-in tools and extension tools register through a core tool registry; extension tool names are namespaced as `extension_id.tool_name` when needed.

**`ui_blocks.py`** — Current central rendering module:
- Pydantic models for each block type: `TextBlock`, `MetricCardBlock`, `TableBlock`, `SparklineBlock`, `BarChartBlock`, `RangeBarBlock`, `NewsBlock`.
- `AIResponse` is the top-level structured output schema (`message: str`, `blocks: list[UIBlock]`). `AI_RESPONSE_SCHEMA` is its JSON schema dict, passed to the agent.
- `make_*_block()` builder functions construct validated block dicts.
- `_fmt_price`, `_fmt_change`, `_fmt_market_cap`, `_fmt_pe` — shared formatting helpers used across all block builders.
- `render_block(console, block)` — dispatches on block type and renders to the Rich console.
- `render_response(console, response)` — renders the message panel then all blocks.
- `parse_ai_response(raw)` — accepts `AIResponse`, `BaseModel`, `dict`, or raw `str` (with JSON-in-markdown fallback).
- Target direction: core owns Visual Block schemas and fallback rendering; each UI owns native renderer mappings. Custom extension block type strings are namespaced like `extension_id/block_name` and use Pydantic validation.

**`command_prompt.py`** — Wraps `prompt-toolkit` to provide slash-command autocomplete (fuzzy, column-style) in interactive TTY sessions. `COMMAND_SPECS` is the single source of truth for command names and descriptions shown in the dropdown.

**`utils.py`** — ANSI color constants (`CYAN`, `YELLOW`, `GREEN`, `RED`, `RESET`), `pick_option()` for numbered terminal menus, `stringify_message_content()` for collapsing LangChain message content to plain text.

## Key Conventions

- **Structured output pipeline**: agent returns `AIResponse` JSON → `parse_ai_response()` validates it → `render_response()` renders message + blocks. Visual builder tools return `{"block": ...}`; the agent copies the inner block into its `blocks` array. Blocks rendered eagerly during streaming are deduplicated before the final render pass.
- **Error handling in tools**: all data tools catch exceptions and return `{"error": "...", "ticker": "..."}` — never raise. The agent is instructed to report errors plainly rather than guess.
- **Provider extensibility now**: add a new preset to `PROVIDER_PRESETS` in `providers.py` and optionally to `LANGCHAIN_PROVIDER_MAP`. Custom providers can also be added interactively at runtime via `/models`.
- **Provider extensibility target**: provider config and switching move into StockSensei Core so CLI/Web share behavior.
- **Extension model target**: trusted Python extensions use a Pi-like `activate(api)` API with required extension id and API version. Discovery sources: project `.stocksensei/extensions/`, global `~/.config/stocksensei/extensions/`, configured paths, and Python package entry points (`stocksensei.extensions`). All discovered extensions load by default; project-local extensions should use a trust-on-first-use prompt. Extension failures should warn, disable that extension for the session, and continue.
- **Extension surface v1**: tools and custom Visual Blocks. Keep lifecycle hooks minimal: `on_startup`, `before_agent_run`, `after_agent_run`, `on_shutdown`. `before_agent_run` may block/short-circuit with a structured response; `after_agent_run` may mutate the response. Future surfaces may include prompt contributors, commands, UI affordances, custom renderers, and broader events.
- **Command model target**: semantic commands live in a core command registry; Terminal UI exposes slash commands and Web UI can expose equivalent actions.
- **Web UI target**: FastAPI + SSE over the core typed event stream. Do not build Web UI by scraping terminal output or duplicating CLI logic.
- **Python 3.13+** required. Use `uv` for all dependency management — not pip.
- The project entry point is declared in `pyproject.toml` as `stocksensei = "main:main"`.
