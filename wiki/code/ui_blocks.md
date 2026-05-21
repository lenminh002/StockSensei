---
status: code-map
path: ui_blocks.py
language: python
updated: 2026-05-21
---

## Purpose
Defines visual block schemas, block builder helpers, structured response parsing, and Rich terminal rendering.

## Functions / Sections
- `_stringify_cell(value)` - formats table cell values.
- `_sparkline(values)` - converts numeric points into ASCII sparkline characters.
- `_fmt_market_cap(value)` - formats market-cap values.
- `_fmt_price(value)` - formats prices.
- `_fmt_change(value)` - formats percentage changes.
- `_fmt_pe(value)` - formats P/E ratios.
- `TextBlock` - schema for markdown text blocks.
- `MetricItem` - schema for metric card items.
- `MetricCardBlock` - schema for summary metric cards.
- `TableBlock` - schema and row-width validation for tables.
- `SparklineBlock` - schema for trend sparklines.
- `BarChartItem` - schema for bar chart items.
- `BarChartBlock` - schema for bar charts.
- `RangeBarBlock` - schema for 52-week range visuals.
- `NewsBlock` - schema for headline lists.
- `UIBlock` - discriminated union of supported visual block schemas.
- `AIResponse` - top-level structured response model.
- `AI_RESPONSE_SCHEMA` - JSON schema passed to the agent.
- `RenderToolPayload` - schema for tool-returned block payloads.
- `make_*_block(...)` - builder helpers for validated visual block dictionaries.
- `make_json_fallback_response(raw_text, error)` - builds a safe fallback response.
- `_normalize_response_dict(data)` - normalizes serialized block payloads in responses.
- `parse_ai_response(raw)` - parses model, dict, JSON string, or markdown-fenced JSON responses.
- `render_block(console, block)` - renders each supported block type with Rich.
- `render_response(console, response)` - renders the response message and blocks.

## Imports / Links
- external: json - parses structured response JSON and fallback payloads.
- external: math - scales sparkline values.
- external: re - extracts fenced JSON blocks.
- external: pydantic - defines and validates response/block schemas.
- external: rich - renders markdown, panels, and tables.
- external: typing - defines annotated unions and literals.
