from __future__ import annotations

import sys
import traceback
from typing import Any, Callable

from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from stocksensei.core.block_models import (
    BarChartBlock,
    CandlestickChartBlock,
    LineChartBlock,
)
from stocksensei.core.responses import AIResponse

# Import the fallback renderer from core (avoids circular import with the root ui_blocks facade).
from stocksensei.core.block_renderer import render_block as _render_block

Renderer = Callable[[Console, Any], None]

# Terminal UI-owned native renderer mapping. The current renderer implementation
# remains in ui_blocks during staged migration; this map is the UI-owned dispatch seam.
TERMINAL_RENDERERS: dict[str, Renderer] = {
    "text": _render_block,
    "metric_card": _render_block,
    "table": _render_block,
    "line_chart": lambda console, block: _render_line_chart(console, block),
    "barchart": lambda console, block: _render_column_chart(console, block),
    "candlestick_chart": lambda console, block: _render_candlestick_chart(console, block),
    "range_bar": _render_block,
    "news": _render_block,
}


def _configure_plotext(plt: Any, console: Console, *, height: int = 22) -> None:
    width = max(48, min(console.width - 12, 112))
    plt.theme("dark")
    plt.canvas_color("black")
    plt.axes_color("black")
    plt.ticks_color("white")
    plt.plotsize(width, height)
    plt.grid(True, True)


def _date_tick_labels(dates: list[str]) -> tuple[list[str], list[str]]:
    if not dates:
        return [], []
    tick_indexes = sorted({0, len(dates) // 2, len(dates) - 1})
    tick_dates = [dates[index] for index in tick_indexes]
    tick_labels = [dates[index][5:] if len(dates[index]) >= 10 else dates[index] for index in tick_indexes]
    return tick_dates, tick_labels


def _plotext_candlestick_canvas(console: Console, block: CandlestickChartBlock) -> str:
    import plotext as plt

    dates = [point.date for point in block.points]
    data = {
        "Open": [point.open for point in block.points],
        "High": [point.high for point in block.points],
        "Low": [point.low for point in block.points],
        "Close": [point.close for point in block.points],
    }

    plt.clear_figure()
    try:
        plt.date_form("Y-m-d", "m/d")
        _configure_plotext(plt, console, height=22)
        plt.title(f"{block.ticker or 'Ticker'} {block.period or ''} OHLC".strip())
        plt.ylabel("Price")
        plt.candlestick(dates, data, colors=["green+", "red+"])

        tick_dates, tick_labels = _date_tick_labels(dates)
        if tick_dates:
            plt.xticks(tick_dates, tick_labels)

        return plt.build().rstrip()
    finally:
        plt.clear_figure()


def _plotext_line_canvas(console: Console, block: LineChartBlock) -> str:
    import plotext as plt

    series = block.series or []
    dates = [point.date for point in block.points]
    values = [point.value for point in block.points]

    plt.clear_figure()
    try:
        plt.date_form("Y-m-d", "m/d")
        _configure_plotext(plt, console, height=18)
        plt.title(block.title or f"{block.ticker or 'Ticker'} {block.period or ''} close".strip())
        if block.unit == "%":
            y_label = "Percent return (%)"
        else:
            y_label = "Price" if block.unit == "price" else block.unit or "Value"
        plt.ylabel(y_label)

        if series:
            dates_for_ticks: list[str] = []
            for index, item in enumerate(series):
                item_dates = [point.date for point in item.points]
                item_values = [point.value for point in item.points]
                if not item_dates:
                    continue
                if len(item_dates) > len(dates_for_ticks):
                    dates_for_ticks = item_dates
                color = item.color or ["cyan+", "green+", "magenta+", "yellow+", "blue+", "red+"][index % 6]
                try:
                    plt.plot(item_dates, item_values, color=color, label=item.label)
                except TypeError:
                    plt.plot(item_dates, item_values, color=color)
            dates = dates_for_ticks
        else:
            plt.plot(dates, values, color="cyan+")

        tick_dates, tick_labels = _date_tick_labels(dates)
        if tick_dates:
            plt.xticks(tick_dates, tick_labels)

        return plt.build().rstrip()
    finally:
        plt.clear_figure()


def _plotext_column_canvas(console: Console, block: BarChartBlock) -> str:
    import plotext as plt

    labels = [item.label for item in block.items]
    if block.unit == "market cap":
        values = [item.value / 1_000_000_000_000 for item in block.items]
        y_label = "Market Cap ($T)"
    elif block.unit == "volume":
        max_value = max((abs(item.value) for item in block.items), default=0.0)
        divisor = 1_000_000_000 if max_value >= 1_000_000_000 else 1_000_000
        suffix = "B" if divisor == 1_000_000_000 else "M"
        values = [item.value / divisor for item in block.items]
        y_label = f"Volume ({suffix})"
    else:
        values = [item.value for item in block.items]
        y_label = "Percent" if block.unit == "%" else "Price ($)" if block.unit == "price" else block.unit or "Value"
    x_positions = list(range(1, len(labels) + 1))

    plt.clear_figure()
    try:
        _configure_plotext(plt, console, height=18)
        plt.title(block.title or "Column chart")
        plt.ylabel(y_label)
        plt.xlim(0, 2) if len(x_positions) == 1 else plt.xlim(0.5, len(x_positions) + 0.5)
        if block.unit == "%":
            positives = [value if value > 0 else 0 for value in values]
            negatives = [value if value < 0 else 0 for value in values]
            if any(value > 0 for value in positives):
                plt.bar(x_positions, positives, color="green+", width=0.25, reset_ticks=False)
            if any(value < 0 for value in negatives):
                plt.bar(x_positions, negatives, color="red+", width=0.25, reset_ticks=False)
            if not any(values):
                plt.bar(x_positions, values, color="white", width=0.25, reset_ticks=False)
        else:
            plt.bar(x_positions, values, color="cyan+", width=0.25, reset_ticks=False)
        plt.xticks(x_positions, labels)
        return plt.build().rstrip()
    finally:
        plt.clear_figure()


def _values_line(block: BarChartBlock | LineChartBlock) -> Text:
    if isinstance(block, BarChartBlock):
        values = " | ".join(f"{item.label}: {item.display_value}" for item in block.items)
    elif block.series:
        values = " | ".join(
            f"{item.label}: {_line_value(item.points[-1].value, block.unit)}"
            for item in block.series
            if item.points
        )
    else:
        values = " | ".join(f"{point.date}: {_line_value(point.value, block.unit)}" for point in block.points)
    return Text(values, style="bright_white on black")


def _line_value(value: float, unit: str | None) -> str:
    if unit == "price":
        return f"${value:,.2f}"
    if unit == "%":
        return f"{value:+.2f}%"
    return f"{value:,.2f}"


def _render_chart_error(console: Console, title: str, reason: str, summary: str | None = None) -> None:
    """Render a styled error panel when a chart cannot be displayed."""
    lines = [f"[bright_red]\u26a0  Chart cannot be rendered.[/bright_red]"]
    if reason:
        lines.append(f"[dim]{reason}[/dim]")
    if summary:
        lines.append("")
        lines.append(f"[bright_black]{summary}[/bright_black]")
    console.print(Panel(
        "\n".join(lines),
        title=title,
        title_align="left",
        border_style="red",
        expand=False,
    ))


def _render_candlestick_chart(console: Console, block: Any) -> None:
    block_obj = block if isinstance(block, CandlestickChartBlock) else CandlestickChartBlock.model_validate(block)
    title = block_obj.title or f"{block_obj.ticker or 'Ticker'} OHLC chart"

    if not block_obj.points:
        _render_chart_error(console, title, "No OHLC data available.", block_obj.summary)
        return

    try:
        canvas = _plotext_candlestick_canvas(console, block_obj)
    except Exception as exc:
        traceback.print_exc(file=sys.stderr)
        _render_chart_error(console, title, f"{type(exc).__name__}: {exc}", block_obj.summary)
        return

    parts = [Text.from_ansi(canvas)]
    if block_obj.summary:
        parts.append(Text(block_obj.summary, style="bright_white on black"))
    console.print(Panel(Group(*parts), title=title, title_align="left", border_style="bright_green", style="on black", expand=False))


def _render_line_chart(console: Console, block: Any) -> None:
    block_obj = block if isinstance(block, LineChartBlock) else LineChartBlock.model_validate(block)
    title = block_obj.title or f"{block_obj.ticker or 'Ticker'} line chart"

    if not block_obj.points and not block_obj.series:
        _render_chart_error(console, title, "No data points available.", block_obj.summary)
        return

    try:
        canvas = _plotext_line_canvas(console, block_obj)
    except Exception as exc:
        traceback.print_exc(file=sys.stderr)
        _render_chart_error(console, title, f"{type(exc).__name__}: {exc}", block_obj.summary)
        return

    parts = [Text.from_ansi(canvas), _values_line(block_obj)]
    if block_obj.summary:
        parts.append(Text(block_obj.summary, style="bright_white on black"))
    console.print(Panel(Group(*parts), title=title, title_align="left", border_style="bright_green", style="on black", expand=False))


def _render_column_chart(console: Console, block: Any) -> None:
    block_obj = block if isinstance(block, BarChartBlock) else BarChartBlock.model_validate(block)
    title = block_obj.title or "Column chart"

    if not block_obj.items:
        _render_chart_error(console, title, "No data items available.", block_obj.summary)
        return

    try:
        canvas = _plotext_column_canvas(console, block_obj)
    except Exception as exc:
        traceback.print_exc(file=sys.stderr)
        _render_chart_error(console, title, f"{type(exc).__name__}: {exc}", block_obj.summary)
        return

    parts = [Text.from_ansi(canvas), _values_line(block_obj)]
    if block_obj.summary:
        parts.append(Text(block_obj.summary, style="bright_white on black"))
    console.print(Panel(Group(*parts), title=title, title_align="left", border_style="bright_green", style="on black", expand=False))


def render_block(console: Console, block: Any) -> None:
    block_type = getattr(block, "type", None) or (block.get("type") if isinstance(block, dict) else None)
    renderer = TERMINAL_RENDERERS.get(block_type, _render_block)
    renderer(console, block)


def render_response(console: Console, response: Any) -> None:
    response_obj = response if isinstance(response, AIResponse) else AIResponse.model_validate(response)
    if response_obj.message:
        console.print(Panel(Markdown(response_obj.message), title="StockSensei", title_align="left", border_style="bright_blue", expand=False))
    for block in response_obj.blocks:
        render_block(console, block)
