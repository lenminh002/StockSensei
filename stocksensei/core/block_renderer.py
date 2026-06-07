"""Fallback Rich terminal renderer for all built-in Visual Block types.

This module provides a self-contained ``render_block`` / ``render_response``
implementation that uses only Rich and ASCII — no plotext.  It is imported by:
  - ``stocksensei.ui.terminal.renderers`` as ``_render_block`` (fallback when plotext fails)
  - ``ui_blocks`` (the root facade) re-exports ``render_block`` / ``render_response``
    pointing here so that legacy callers that did ``from ui_blocks import render_block``
    get the same function they always did.
"""
from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ValidationError
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from stocksensei.core.block_formatting import _grid_positions
from stocksensei.core.block_models import (
    BarChartBlock,
    CandlestickChartBlock,
    LineChartBlock,
    MetricCardBlock,
    NewsBlock,
    RangeBarBlock,
    TableBlock,
    TextBlock,
    UIBlock,
    UI_BLOCK_ADAPTER,
)
from stocksensei.core.responses import AIResponse


def render_block(console: Console, block: "UIBlock | dict[str, Any]") -> None:
    """Render a single block to the Rich console using ASCII/Rich only (no plotext)."""
    try:
        block_obj = block if isinstance(block, BaseModel) else UI_BLOCK_ADAPTER.validate_python(block)
    except ValidationError:
        if isinstance(block, dict):
            fallback = block.get("fallback") or block.get("text") or block.get("content")
            title = block.get("title") or block.get("type") or "Visual Block"
            if fallback:
                console.print(Panel(Markdown(str(fallback)), title=str(title), title_align="left", border_style="bright_cyan", expand=False))
            else:
                console.print(Panel(json.dumps(block, indent=2, default=str), title=f"Unsupported block: {title}", title_align="left", border_style="yellow", expand=False))
            return
        raise

    if isinstance(block_obj, TextBlock):
        renderable = Markdown(block_obj.content)
        if block_obj.title:
            console.print(Panel(renderable, title=block_obj.title, title_align="left", border_style="bright_cyan", expand=False))
        else:
            console.print(renderable)
        return

    if isinstance(block_obj, MetricCardBlock):
        lines = []
        for item in block_obj.items:
            tone = item.tone or "bright_white"
            lines.append(f"[bold bright_white]{item.label:<14}[/bold bright_white] [{tone}]{item.value}[/{tone}]")
        if block_obj.subtitle:
            lines.insert(0, f"[bright_cyan]{block_obj.subtitle}[/bright_cyan]")
            lines.insert(1, "")
        if block_obj.footer:
            lines.extend(["", f"[bright_black]{block_obj.footer}[/bright_black]"])
        console.print(Panel("\n".join(lines), title=block_obj.title, title_align="left", border_style="bright_magenta", expand=False))
        return

    if isinstance(block_obj, TableBlock):
        table = Table(
            title=block_obj.title,
            title_style="bold magenta",
            header_style="bold bright_cyan",
            border_style="bright_blue",
            row_styles=["", "on #101828"],
        )
        numeric_columns = {"Price", "Daily Chg", "Market Cap", "P/E", "Forward P/E", "52W High", "52W Low"}
        for column in block_obj.columns:
            table.add_column(column, justify="right" if column in numeric_columns else "left", style="bold bright_cyan" if column == "Ticker" else None)
        for row in block_obj.rows:
            styled = list(row)
            if block_obj.columns and "Daily Chg" in block_obj.columns:
                idx = block_obj.columns.index("Daily Chg")
                if isinstance(styled[idx], str):
                    color = "bright_green" if not styled[idx].startswith("-") else "bright_red"
                    styled[idx] = f"[{color}]{styled[idx]}[/{color}]"
            table.add_row(*styled)
        console.print(table)
        return

    if isinstance(block_obj, (LineChartBlock, BarChartBlock, CandlestickChartBlock)):
        body = [
            "⚠  Chart cannot be rendered.",
            "[dim]Terminal environment does not support graphical plotting.[/dim]"
        ]
        if block_obj.summary:
            body.append("")
            body.append(f"[bright_white]{block_obj.summary}[/bright_white]")
        title = getattr(block_obj, "title", None) or "Chart"
        console.print(Panel("\n".join(body), title=title, title_align="left", border_style="red", expand=False))
        return

    if isinstance(block_obj, RangeBarBlock):
        width = 41
        pointer_index = min(width - 1, max(0, int(block_obj.position * (width - 1))))
        tick_positions = set(_grid_positions(width))
        cells = ["+" if index in tick_positions else "=" for index in range(width)]
        cells[pointer_index] = "^"
        bar = "".join(cells)
        marker = " " * pointer_index + "^"
        lines = [
            f"[bright_cyan]{block_obj.minimum_label}[/bright_cyan] [bright_black]{bar}[/bright_black] [bright_magenta]{block_obj.maximum_label}[/bright_magenta]",
            f"[bright_black]{'':{len(block_obj.minimum_label) + 1}}{marker}[/bright_black]",
            f"[bold bright_white]{block_obj.current_label}[/bold bright_white] [bright_black]position {block_obj.position * 100:.1f}% of range[/bright_black]",
            "[bright_black]Grid: 0% | 25% | 50% | 75% | 100%[/bright_black]",
        ]
        if block_obj.summary:
            lines.append(f"[bright_black]{block_obj.summary}[/bright_black]")
        console.print(Panel("\n".join(lines), title=block_obj.title, title_align="left", border_style="bright_yellow", expand=False))
        return

    if isinstance(block_obj, NewsBlock):
        items = "\n".join(f"- {headline}" for headline in block_obj.headlines) or "- No headlines available"
        console.print(Panel(Markdown(items), title=block_obj.title or f"News{f' for {block_obj.ticker}' if block_obj.ticker else ''}", title_align="left", border_style="bright_yellow", expand=False))
        return


def render_response(console: Console, response: "AIResponse | dict[str, Any]") -> None:
    """Render the message panel and all blocks for a complete AIResponse."""
    response_obj = response if isinstance(response, AIResponse) else AIResponse.model_validate(response)
    if response_obj.message:
        console.print(Panel(Markdown(response_obj.message), title="StockSensei", title_align="left", border_style="bright_blue", expand=False))
    for block in response_obj.blocks:
        render_block(console, block)
