from __future__ import annotations

import json
import math
import re
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, ValidationError, field_validator
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table


def _stringify_cell(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


def _sparkline(values: list[float]) -> str:
    if not values:
        return ""
    ticks = ".:-=+*#%@"
    low = min(values)
    high = max(values)
    if math.isclose(low, high):
        return ticks[0] * len(values)
    return "".join(ticks[min(int((value - low) / (high - low) * (len(ticks) - 1)), len(ticks) - 1)] for value in values)


def _fmt_market_cap(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return "N/A"
    return f"${value / 1_000_000_000_000:.2f}T" if value >= 1_000_000_000_000 else f"${value / 1_000_000_000:.2f}B"


def _fmt_price(value: Any) -> str:
    return f"${value:,.2f}" if isinstance(value, (int, float)) else "N/A"


def _fmt_change(value: Any) -> str:
    return f"{value:+.2f}%" if isinstance(value, (int, float)) else "N/A"


def _fmt_pe(value: Any) -> str:
    return f"{value:.2f}" if isinstance(value, (int, float)) else "N/A"


class TextBlock(BaseModel):
    type: Literal["text"]
    title: str | None = None
    content: str


class MetricItem(BaseModel):
    label: str
    value: str
    tone: str | None = None


class MetricCardBlock(BaseModel):
    type: Literal["metric_card"]
    title: str
    subtitle: str | None = None
    items: list[MetricItem]
    footer: str | None = None


class TableBlock(BaseModel):
    type: Literal["table"]
    title: str | None = None
    columns: list[str]
    rows: list[list[str]]

    @field_validator("rows")
    @classmethod
    def _validate_rows(cls, rows: list[list[str]], info):
        columns = info.data.get("columns") or []
        width = len(columns)
        if width and any(len(row) != width for row in rows):
            raise ValueError("Each table row must match number of columns.")
        return rows


class SparklineBlock(BaseModel):
    type: Literal["sparkline"]
    title: str | None = None
    label: str | None = None
    points: list[float]
    x_labels: list[str] = Field(default_factory=list)
    summary: str | None = None


class BarChartItem(BaseModel):
    label: str
    value: float
    display_value: str
    color: str | None = None


class BarChartBlock(BaseModel):
    type: Literal["barchart"]
    title: str | None = None
    items: list[BarChartItem]
    unit: str | None = None
    summary: str | None = None


class RangeBarBlock(BaseModel):
    type: Literal["range_bar"]
    title: str
    minimum_label: str
    maximum_label: str
    current_label: str
    position: float = Field(ge=0.0, le=1.0)
    summary: str | None = None


class NewsBlock(BaseModel):
    type: Literal["news"]
    title: str | None = None
    ticker: str | None = None
    headlines: list[str]


UIBlock = Annotated[
    TextBlock | MetricCardBlock | TableBlock | SparklineBlock | BarChartBlock | RangeBarBlock | NewsBlock,
    Field(discriminator="type"),
]


class AIResponse(BaseModel):
    message: str = ""
    blocks: list[UIBlock] = Field(default_factory=list)


AI_RESPONSE_SCHEMA = {
    "name": "AIResponse",
    "schema": AIResponse.model_json_schema(),
}


class RenderToolPayload(BaseModel):
    block: UIBlock


def make_text_block(content: str, title: str | None = None) -> dict[str, Any]:
    return TextBlock(type="text", title=title, content=content).model_dump()


def make_metric_card_block(
    title: str,
    items: list[dict[str, str]],
    subtitle: str | None = None,
    footer: str | None = None,
) -> dict[str, Any]:
    return MetricCardBlock(type="metric_card", title=title, subtitle=subtitle, items=items, footer=footer).model_dump()


def make_table_block(columns: list[str], rows: list[list[Any]], title: str | None = None) -> dict[str, Any]:
    return TableBlock(
        type="table",
        title=title,
        columns=[str(column) for column in columns],
        rows=[[_stringify_cell(cell) for cell in row] for row in rows],
    ).model_dump()


def make_sparkline_block(
    points: list[float],
    title: str | None = None,
    label: str | None = None,
    x_labels: list[str] | None = None,
    summary: str | None = None,
) -> dict[str, Any]:
    return SparklineBlock(
        type="sparkline",
        title=title,
        label=label,
        points=points,
        x_labels=x_labels or [],
        summary=summary,
    ).model_dump()


def make_barchart_block(
    items: list[dict[str, Any]],
    title: str | None = None,
    unit: str | None = None,
    summary: str | None = None,
) -> dict[str, Any]:
    return BarChartBlock(type="barchart", title=title, items=items, unit=unit, summary=summary).model_dump()


def make_range_bar_block(
    title: str,
    minimum_label: str,
    maximum_label: str,
    current_label: str,
    position: float,
    summary: str | None = None,
) -> dict[str, Any]:
    return RangeBarBlock(
        type="range_bar",
        title=title,
        minimum_label=minimum_label,
        maximum_label=maximum_label,
        current_label=current_label,
        position=max(0.0, min(1.0, position)),
        summary=summary,
    ).model_dump()


def make_news_block(headlines: list[str], ticker: str | None = None, title: str | None = None) -> dict[str, Any]:
    return NewsBlock(type="news", title=title, ticker=ticker, headlines=headlines).model_dump()


def make_snapshot_card_block(snapshot: dict[str, Any]) -> dict[str, Any]:
    price = snapshot.get("price")
    change = snapshot.get("change_percent")
    pe = snapshot.get("pe_ratio")
    forward_pe = snapshot.get("forward_pe")
    market_cap = snapshot.get("market_cap")

    change_tone = "bright_green" if isinstance(change, (int, float)) and change >= 0 else "bright_red"
    items = [
        {"label": "Price",        "value": _fmt_price(price),          "tone": "bright_cyan"},
        {"label": "Daily change", "value": _fmt_change(change),        "tone": change_tone},
        {"label": "Market cap",   "value": _fmt_market_cap(market_cap), "tone": "bright_magenta"},
        {"label": "P/E",          "value": _fmt_pe(pe),                "tone": "bright_yellow"},
        {"label": "Forward P/E",  "value": _fmt_pe(forward_pe),        "tone": "bright_yellow"},
    ]
    footer = None
    if snapshot.get("sector") or snapshot.get("industry"):
        footer = f"{snapshot.get('sector') or 'Unknown sector'} / {snapshot.get('industry') or 'Unknown industry'}"
    return make_metric_card_block(
        title=f"{snapshot.get('ticker', '?')} snapshot",
        subtitle=snapshot.get("company_name"),
        items=items,
        footer=footer,
    )


def make_52w_range_block(snapshot: dict[str, Any]) -> dict[str, Any]:
    low = snapshot.get("week_52_low")
    high = snapshot.get("week_52_high")
    price = snapshot.get("price")
    if not all(isinstance(v, (int, float)) for v in [low, high, price]) or high == low:
        return make_range_bar_block(
            title=f"{snapshot.get('ticker', '?')} 52-week range",
            minimum_label="Low: N/A",
            maximum_label="High: N/A",
            current_label="Current: N/A",
            position=0.0,
            summary="52-week range data unavailable.",
        )
    position = (price - low) / (high - low)
    return make_range_bar_block(
        title=f"{snapshot.get('ticker', '?')} 52-week range",
        minimum_label=f"Low ${low:.2f}",
        maximum_label=f"High ${high:.2f}",
        current_label=f"Current ${price:.2f}",
        position=position,
        summary=f"Current price sits at {position * 100:.0f}% of the 52-week range.",
    )


def make_price_comparison_block(stocks: list[dict[str, Any]], title: str | None = None) -> dict[str, Any]:
    columns = ["Ticker", "Price", "Daily Chg", "Market Cap", "P/E", "Forward P/E", "52W High", "52W Low"]
    rows = [
        [
            stock.get("ticker"),
            _fmt_price(stock.get("price")),
            _fmt_change(stock.get("change_percent")),
            _fmt_market_cap(stock.get("market_cap")),
            _fmt_pe(stock.get("pe_ratio")),
            _fmt_pe(stock.get("forward_pe")),
            _fmt_price(stock.get("week_52_high")),
            _fmt_price(stock.get("week_52_low")),
        ]
        for stock in stocks
    ]
    return make_table_block(columns, rows, title or "Comparison")


def make_summary_comparison_block(stocks: list[dict[str, Any]], title: str | None = None) -> dict[str, Any]:
    columns = ["Ticker", "Company", "Sector", "Industry"]
    rows = [[stock.get("ticker"), stock.get("company_name") or "N/A", stock.get("sector") or "N/A", stock.get("industry") or "N/A"] for stock in stocks]
    return make_table_block(columns, rows, title or "Company summary")


def make_change_barchart_block(stocks: list[dict[str, Any]], title: str | None = None) -> dict[str, Any]:
    items = []
    for stock in stocks:
        change = stock.get("change_percent")
        if isinstance(change, (int, float)):
            items.append({
                "label": stock.get("ticker") or "?",
                "value": float(change),
                "display_value": _fmt_change(change),
                "color": "bright_green" if change >= 0 else "bright_red",
            })
    return make_barchart_block(items, title or "Daily change chart", unit="%", summary="Daily percentage move by ticker")


def make_market_cap_barchart_block(stocks: list[dict[str, Any]], title: str | None = None) -> dict[str, Any]:
    items = []
    for stock in stocks:
        market_cap = stock.get("market_cap")
        if isinstance(market_cap, (int, float)):
            items.append({
                "label": stock.get("ticker") or "?",
                "value": float(market_cap),
                "display_value": _fmt_market_cap(market_cap),
                "color": "bright_cyan",
            })
    return make_barchart_block(items, title or "Market cap chart", unit="market cap", summary="Relative company size")


def make_history_chart_block(history: dict[str, Any]) -> dict[str, Any]:
    points = [row["close"] for row in history.get("data", []) if isinstance(row.get("close"), (int, float))]
    labels = [row["date"] for row in history.get("data", [])]
    summary = f"{history.get('ticker', '')} closing trend for {history.get('period', '')}".strip()
    return make_sparkline_block(
        points=points,
        title=f"{history.get('ticker', '')} trend",
        label=history.get("ticker"),
        x_labels=labels,
        summary=summary,
    )


def make_json_fallback_response(raw_text: str, error: str | None = None) -> AIResponse:
    message = "I could not produce a fully structured response, so here is a safe fallback."
    if error:
        message += f" ({error})"
    text = raw_text.strip() or "No response available."
    return AIResponse(message=message, blocks=[TextBlock(type="text", title="Fallback", content=text)])


_JSON_BLOCK_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def parse_ai_response(raw: Any) -> AIResponse:
    if isinstance(raw, AIResponse):
        return raw
    if isinstance(raw, BaseModel):
        return AIResponse.model_validate(raw.model_dump())
    if isinstance(raw, dict):
        return AIResponse.model_validate(raw)
    if isinstance(raw, str):
        stripped = raw.strip()
        candidates = [stripped]
        match = _JSON_BLOCK_RE.search(stripped)
        if match:
            candidates.insert(0, match.group(1))
        for candidate in candidates:
            try:
                return AIResponse.model_validate(json.loads(candidate))
            except (json.JSONDecodeError, ValidationError):
                continue
        return make_json_fallback_response(stripped)
    return make_json_fallback_response(str(raw))


def render_block(console: Console, block: UIBlock | dict[str, Any]) -> None:
    block_obj = block if isinstance(block, BaseModel) else AIResponse.model_validate({"message": "", "blocks": [block]}).blocks[0]

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

    if isinstance(block_obj, SparklineBlock):
        spark = _sparkline(block_obj.points)
        body = []
        label = f"[bold bright_cyan]{block_obj.label}[/bold bright_cyan]: " if block_obj.label else ""
        body.append(f"{label}[bold bright_magenta]{spark}[/bold bright_magenta]")
        if block_obj.x_labels:
            body.append(f"[bright_black]Range:[/bright_black] [cyan]{block_obj.x_labels[0]}[/cyan] [bright_white]->[/bright_white] [cyan]{block_obj.x_labels[-1]}[/cyan]")
        if block_obj.summary:
            body.append(f"[bright_white]{block_obj.summary}[/bright_white]")
        console.print(Panel("\n".join(body), title=block_obj.title or "Trend", title_align="left", border_style="bright_magenta", expand=False))
        return

    if isinstance(block_obj, BarChartBlock):
        max_abs = max((abs(item.value) for item in block_obj.items), default=1.0)
        lines = []
        for item in block_obj.items:
            width = max(1, int((abs(item.value) / max_abs) * 24)) if max_abs else 1
            bar = "#" * width
            color = item.color or "bright_cyan"
            lines.append(f"[bold bright_cyan]{item.label:>6}[/bold bright_cyan]  [{color}]{bar}[/{color}] [bold {color}]{item.display_value}[/bold {color}]")
        if block_obj.summary:
            lines.extend(["", f"[bright_white]{block_obj.summary}[/bright_white]"])
        console.print(Panel("\n".join(lines) if lines else "No chart data.", title=block_obj.title or "Chart", title_align="left", border_style="bright_green", expand=False))
        return

    if isinstance(block_obj, RangeBarBlock):
        width = 28
        pointer_index = min(width - 1, max(0, int(block_obj.position * (width - 1))))
        cells = ["-"] * width
        cells[pointer_index] = "|"
        bar = "".join(cells)
        lines = [
            f"[bright_cyan]{block_obj.minimum_label}[/bright_cyan] [bright_black]{bar}[/bright_black] [bright_magenta]{block_obj.maximum_label}[/bright_magenta]",
            f"[bold bright_white]{block_obj.current_label}[/bold bright_white]",
        ]
        if block_obj.summary:
            lines.append(f"[bright_black]{block_obj.summary}[/bright_black]")
        console.print(Panel("\n".join(lines), title=block_obj.title, title_align="left", border_style="bright_yellow", expand=False))
        return

    if isinstance(block_obj, NewsBlock):
        items = "\n".join(f"- {headline}" for headline in block_obj.headlines) or "- No headlines available"
        console.print(Panel(Markdown(items), title=block_obj.title or f"News{f' for {block_obj.ticker}' if block_obj.ticker else ''}", title_align="left", border_style="bright_yellow", expand=False))
        return


def render_response(console: Console, response: AIResponse | dict[str, Any]) -> None:
    response_obj = response if isinstance(response, AIResponse) else AIResponse.model_validate(response)
    if response_obj.message:
        console.print(Panel(Markdown(response_obj.message), title="StockSensei", title_align="left", border_style="bright_blue", expand=False))
    for block in response_obj.blocks:
        render_block(console, block)
