from __future__ import annotations

from typing import Any, Callable

from rich.console import Console

from ui_blocks import (
    BarChartBlock,
    MetricCardBlock,
    NewsBlock,
    RangeBarBlock,
    SparklineBlock,
    TableBlock,
    TextBlock,
    render_block as _render_block,
    render_response as _render_response,
)

Renderer = Callable[[Console, Any], None]

# Terminal UI-owned native renderer mapping. The current renderer implementation
# remains in ui_blocks during staged migration; this map is the UI-owned dispatch seam.
TERMINAL_RENDERERS: dict[str, Renderer] = {
    "text": _render_block,
    "metric_card": _render_block,
    "table": _render_block,
    "sparkline": _render_block,
    "barchart": _render_block,
    "range_bar": _render_block,
    "news": _render_block,
}


def render_block(console: Console, block: Any) -> None:
    block_type = getattr(block, "type", None) or (block.get("type") if isinstance(block, dict) else None)
    renderer = TERMINAL_RENDERERS.get(block_type, _render_block)
    renderer(console, block)


def render_response(console: Console, response: Any) -> None:
    _render_response(console, response)
