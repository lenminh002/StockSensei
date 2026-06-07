"""Backward-compatibility re-export facade for ui_blocks.

All symbols previously defined here are now implemented in focused core modules:

  - stocksensei.core.block_models   — Pydantic block models, UIBlock, UI_BLOCK_ADAPTER, RenderToolPayload
  - stocksensei.core.block_formatting — formatting helpers, ASCII chart primitives
  - stocksensei.core.responses      — AIResponse, AI_RESPONSE_SCHEMA, parse_ai_response, make_json_fallback_response
  - stocksensei.core.block_builders — make_*_block() builders and stock-specific visual helpers
  - stocksensei.ui.terminal.renderers — Rich terminal render_block / render_response

``from ui_blocks import ...`` remains valid for all existing symbols.
New internal code should import directly from the core modules above.
"""
from __future__ import annotations

# --- Block models -----------------------------------------------------------
from stocksensei.core.block_models import (
    BarChartBlock,
    BarChartItem,
    CandlestickChartBlock,
    CandlestickPoint,
    LineChartBlock,
    LineChartPoint,
    LineChartSeries,
    MetricCardBlock,
    MetricItem,
    NewsBlock,
    RangeBarBlock,
    RenderToolPayload,
    TableBlock,
    TextBlock,
    UIBlock,
    UI_BLOCK_ADAPTER,
    _stringify_cell,
)

# --- Formatting helpers ------------------------------------------------------
from stocksensei.core.block_formatting import (
    _fmt_axis_value,
    _fmt_change,
    _fmt_compact_number,
    _fmt_market_cap,
    _fmt_pe,
    _fmt_price,
)

# --- Response parsing --------------------------------------------------------
from stocksensei.core.responses import (
    AI_RESPONSE_SCHEMA,
    AIResponse,
    make_json_fallback_response,
    parse_ai_response,
)

# --- Block builders ----------------------------------------------------------
from stocksensei.core.block_builders import (
    make_52w_range_block,
    make_barchart_block,
    make_candlestick_chart_block,
    make_change_barchart_block,
    make_history_chart_block,
    make_history_line_chart_block,
    make_line_chart_block,
    make_market_cap_barchart_block,
    make_metric_card_block,
    make_news_block,
    make_price_barchart_block,
    make_price_comparison_block,
    make_range_bar_block,
    make_snapshot_card_block,
    make_summary_comparison_block,
    make_table_block,
    make_text_block,
    make_time_comparison_line_chart_block,
    make_volume_chart_block,
)

# --- Terminal rendering (re-export for backward compatibility) ---------------
# NOTE: We re-export the fallback ASCII renderer from stocksensei.core.block_renderer
# rather than from stocksensei.ui.terminal.renderers to avoid a circular import
# (renderers.py imports from the core modules that ui_blocks.py also imports).
# Callers that want the plotext-enhanced renderer should import from
# stocksensei.ui.terminal.renderers directly.
from stocksensei.core.block_renderer import (
    render_block,
    render_response,
)

__all__ = [
    # block_models
    "BarChartBlock",
    "BarChartItem",
    "CandlestickChartBlock",
    "CandlestickPoint",
    "LineChartBlock",
    "LineChartPoint",
    "LineChartSeries",
    "MetricCardBlock",
    "MetricItem",
    "NewsBlock",
    "RangeBarBlock",
    "RenderToolPayload",
    "TableBlock",
    "TextBlock",
    "UIBlock",
    "UI_BLOCK_ADAPTER",
    "_stringify_cell",
    # block_formatting
    "_fmt_axis_value",
    "_fmt_change",
    "_fmt_compact_number",
    "_fmt_market_cap",
    "_fmt_pe",
    "_fmt_price",
    # responses
    "AI_RESPONSE_SCHEMA",
    "AIResponse",
    "make_json_fallback_response",
    "parse_ai_response",
    # block_builders
    "make_52w_range_block",
    "make_barchart_block",
    "make_candlestick_chart_block",
    "make_change_barchart_block",
    "make_history_chart_block",
    "make_history_line_chart_block",
    "make_line_chart_block",
    "make_market_cap_barchart_block",
    "make_metric_card_block",
    "make_news_block",
    "make_price_barchart_block",
    "make_price_comparison_block",
    "make_range_bar_block",
    "make_snapshot_card_block",
    "make_summary_comparison_block",
    "make_table_block",
    "make_text_block",
    "make_time_comparison_line_chart_block",
    "make_volume_chart_block",
    # terminal renderers
    "render_block",
    "render_response",
]
