from __future__ import annotations

import json
import math
import re
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, TypeAdapter, ValidationError, field_validator
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


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


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
    if not _is_finite_number(value):
        return "N/A"
    return f"${value / 1_000_000_000_000:.2f}T" if value >= 1_000_000_000_000 else f"${value / 1_000_000_000:.2f}B"


def _fmt_compact_number(value: Any) -> str:
    if not _is_finite_number(value):
        return "N/A"
    value = float(value)
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.2f}K"
    return f"{value:,.0f}"


def _fmt_price(value: Any) -> str:
    return f"${value:,.2f}" if _is_finite_number(value) else "N/A"


def _fmt_change(value: Any) -> str:
    return f"{value:+.2f}%" if _is_finite_number(value) else "N/A"


def _fmt_pe(value: Any) -> str:
    return f"{value:.2f}" if _is_finite_number(value) else "N/A"


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


class LineChartPoint(BaseModel):
    date: str
    value: float


class LineChartSeries(BaseModel):
    label: str
    points: list[LineChartPoint]
    color: str | None = None


class LineChartBlock(BaseModel):
    type: Literal["line_chart"]
    title: str | None = None
    ticker: str | None = None
    period: str | None = None
    label: str | None = None
    points: list[LineChartPoint] = Field(default_factory=list)
    series: list[LineChartSeries] = Field(default_factory=list)
    unit: str | None = None
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


class CandlestickPoint(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float


class CandlestickChartBlock(BaseModel):
    type: Literal["candlestick_chart"]
    title: str | None = None
    ticker: str | None = None
    period: str | None = None
    points: list[CandlestickPoint]
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
    TextBlock
    | MetricCardBlock
    | TableBlock
    | SparklineBlock
    | LineChartBlock
    | BarChartBlock
    | CandlestickChartBlock
    | RangeBarBlock
    | NewsBlock,
    Field(discriminator="type"),
]
UI_BLOCK_ADAPTER = TypeAdapter(UIBlock)


class AIResponse(BaseModel):
    message: str = ""
    blocks: list[Any] = Field(default_factory=list)


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


def make_line_chart_block(
    points: list[dict[str, Any]],
    title: str | None = None,
    ticker: str | None = None,
    period: str | None = None,
    label: str | None = None,
    series: list[dict[str, Any]] | None = None,
    unit: str | None = None,
    summary: str | None = None,
) -> dict[str, Any]:
    return LineChartBlock(
        type="line_chart",
        title=title,
        ticker=ticker,
        period=period,
        label=label,
        points=points,
        series=series or [],
        unit=unit,
        summary=summary,
    ).model_dump()


def make_barchart_block(
    items: list[dict[str, Any]],
    title: str | None = None,
    unit: str | None = None,
    summary: str | None = None,
) -> dict[str, Any]:
    return BarChartBlock(type="barchart", title=title, items=items, unit=unit, summary=summary).model_dump()


def make_candlestick_chart_block(
    points: list[dict[str, Any]],
    title: str | None = None,
    ticker: str | None = None,
    period: str | None = None,
    summary: str | None = None,
) -> dict[str, Any]:
    return CandlestickChartBlock(
        type="candlestick_chart",
        title=title,
        ticker=ticker,
        period=period,
        points=points,
        summary=summary,
    ).model_dump()


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
    if not all(_is_finite_number(v) for v in [low, high, price]) or high == low:
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
    columns = ["Ticker", "Market Cap", "P/E", "Forward P/E", "52W High", "52W Low", "Sector", "Industry"]
    rows = [
        [
            stock.get("ticker"),
            _fmt_market_cap(stock.get("market_cap")),
            _fmt_pe(stock.get("pe_ratio")),
            _fmt_pe(stock.get("forward_pe")),
            _fmt_price(stock.get("week_52_high")),
            _fmt_price(stock.get("week_52_low")),
            stock.get("sector") or "N/A",
            stock.get("industry") or "N/A",
        ]
        for stock in stocks
    ]
    return make_table_block(columns, rows, title or "Valuation summary")


def make_change_barchart_block(stocks: list[dict[str, Any]], title: str | None = None) -> dict[str, Any]:
    items = []
    for stock in stocks:
        change = stock.get("change_percent")
        if _is_finite_number(change):
            items.append({
                "label": stock.get("ticker") or "?",
                "value": float(change),
                "display_value": _fmt_change(change),
                "color": "bright_green" if change >= 0 else "bright_red",
            })
    return make_barchart_block(items, title or "Daily change chart", unit="%", summary="Daily percentage move by ticker")


def make_price_barchart_block(stocks: list[dict[str, Any]], title: str | None = None) -> dict[str, Any]:
    items = []
    for stock in stocks:
        price = stock.get("price")
        if _is_finite_number(price):
            items.append({
                "label": stock.get("ticker") or "?",
                "value": float(price),
                "display_value": _fmt_price(price),
                "color": "bright_cyan",
            })
    return make_barchart_block(items, title or "Price chart", unit="price", summary="Relative share price by ticker")


def make_market_cap_barchart_block(stocks: list[dict[str, Any]], title: str | None = None) -> dict[str, Any]:
    items = []
    for stock in stocks:
        market_cap = stock.get("market_cap")
        if _is_finite_number(market_cap):
            items.append({
                "label": stock.get("ticker") or "?",
                "value": float(market_cap),
                "display_value": _fmt_market_cap(market_cap),
                "color": "bright_cyan",
            })
    return make_barchart_block(items, title or "Market cap chart", unit="market cap", summary="Relative company size")


def make_volume_chart_block(history: dict[str, Any]) -> dict[str, Any]:
    rows = history.get("data", [])
    items = []
    for row in rows:
        volume = row.get("volume")
        if _is_finite_number(volume):
            items.append({
                "label": str(row.get("date") or ""),
                "value": float(volume),
                "display_value": _fmt_compact_number(volume),
                "color": "bright_cyan",
            })
    ticker = history.get("ticker") or ""
    period = history.get("period") or ""
    if items:
        average = sum(item["value"] for item in items) / len(items)
        summary = f"{ticker} {period}: average volume {_fmt_compact_number(average)}, latest {items[-1]['display_value']}".strip()
    else:
        summary = history.get("error") or f"No volume data available for {ticker} {period}".strip()
    return make_barchart_block(
        items,
        title=f"{ticker} volume chart".strip(),
        unit="volume",
        summary=summary,
    )


def make_history_chart_block(history: dict[str, Any]) -> dict[str, Any]:
    rows = history.get("data", [])
    points = [
        {
            "date": str(row.get("date") or ""),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
        }
        for row in rows
        if all(_is_finite_number(row.get(key)) for key in ["open", "high", "low", "close"])
    ]
    ticker = history.get("ticker") or ""
    period = history.get("period") or ""
    if points:
        first_close = points[0]["close"]
        latest_close = points[-1]["close"]
        high = max(point["high"] for point in points)
        low = min(point["low"] for point in points)
        change = ((latest_close - first_close) / first_close * 100) if first_close else 0.0
        summary = (
            f"{ticker} {period}: close {_fmt_price(first_close)} -> {_fmt_price(latest_close)} "
            f"({_fmt_change(change)}), high {_fmt_price(high)}, low {_fmt_price(low)}"
        )
    else:
        summary = history.get("error") or f"No OHLC data available for {ticker} {period}".strip()
    return make_candlestick_chart_block(
        points=points,
        title=f"{ticker} OHLC chart".strip(),
        ticker=ticker,
        period=period,
        summary=summary,
    )


def make_history_line_chart_block(history: dict[str, Any]) -> dict[str, Any]:
    rows = history.get("data", [])
    points = [
        {
            "date": str(row.get("date") or ""),
            "value": float(row["close"]),
        }
        for row in rows
        if _is_finite_number(row.get("close"))
    ]
    ticker = history.get("ticker") or ""
    period = history.get("period") or ""
    if points:
        first_close = points[0]["value"]
        latest_close = points[-1]["value"]
        high = max(point["value"] for point in points)
        low = min(point["value"] for point in points)
        change = ((latest_close - first_close) / first_close * 100) if first_close else 0.0
        summary = (
            f"{ticker} {period}: close {_fmt_price(first_close)} -> {_fmt_price(latest_close)} "
            f"({_fmt_change(change)}), close high {_fmt_price(high)}, close low {_fmt_price(low)}"
        )
    else:
        summary = history.get("error") or f"No close-price data available for {ticker} {period}".strip()
    return make_line_chart_block(
        points=points,
        title=f"{ticker} close line chart".strip(),
        ticker=ticker,
        period=period,
        label="Close",
        unit="price",
        summary=summary,
    )


def make_time_comparison_line_chart_block(
    histories: list[dict[str, Any]],
    period: str | None = None,
    mode: str = "percent",
) -> dict[str, Any]:
    normalized_mode = (mode or "percent").strip().lower()
    use_price = normalized_mode in {"price", "raw", "close", "closing_price", "raw_price"}
    unit = "price" if use_price else "%"
    label = "Close" if use_price else "Percent return"
    colors = ["cyan+", "green+", "magenta+", "yellow+", "blue+", "red+"]
    series = []
    summary_parts = []
    errors = []

    for index, history in enumerate(histories):
        ticker = history.get("ticker") or "?"
        rows = history.get("data", [])
        closes = [
            (str(row.get("date") or ""), float(row["close"]))
            for row in rows
            if _is_finite_number(row.get("close"))
        ]
        if not closes:
            errors.append(f"{ticker}: {history.get('error') or 'no close-price data'}")
            continue

        first_close = closes[0][1]
        if not use_price and first_close == 0:
            errors.append(f"{ticker}: first close is zero")
            continue

        points = []
        for date, close in closes:
            value = close if use_price else ((close - first_close) / first_close * 100)
            points.append({"date": date, "value": value})

        latest_value = points[-1]["value"]
        series.append({
            "label": ticker,
            "points": points,
            "color": colors[index % len(colors)],
        })
        if use_price:
            summary_parts.append(f"{ticker} {_fmt_price(first_close)} -> {_fmt_price(latest_value)}")
        else:
            summary_parts.append(f"{ticker} {_fmt_change(latest_value)}")

    actual_period = period or next((history.get("period") for history in histories if history.get("period")), "")
    if summary_parts:
        summary = f"{actual_period}: " if actual_period else ""
        summary += " | ".join(summary_parts)
        if errors:
            summary += f" | Unavailable: {'; '.join(errors)}"
    else:
        summary = f"No close-price comparison data available. {'; '.join(errors)}".strip()

    tickers = ", ".join(item["label"] for item in series)
    return make_line_chart_block(
        points=[],
        series=series,
        title=f"{tickers or 'Tickers'} {label.lower()} comparison".strip(),
        ticker=tickers or None,
        period=actual_period,
        label=label,
        unit=unit,
        summary=summary,
    )


def make_json_fallback_response(raw_text: str, error: str | None = None) -> AIResponse:
    message = "I could not produce a fully structured response, so here is a safe fallback."
    if error:
        message += f" ({error})"
    text = raw_text.strip() or "No response available."
    return AIResponse(message=message, blocks=[TextBlock(type="text", title="Fallback", content=text)])


_JSON_BLOCK_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def _validate_block(block: Any) -> UIBlock | Any:
    if isinstance(block, BaseModel):
        return block
    if isinstance(block, dict):
        try:
            return UI_BLOCK_ADAPTER.validate_python(block)
        except ValidationError:
            return block
    return block


def _normalize_response_dict(data: Any) -> Any:
    if not isinstance(data, dict):
        return data
    blocks = data.get("blocks")
    if isinstance(blocks, list):
        normalized = []
        for block in blocks:
            if isinstance(block, str):
                try:
                    block = json.loads(block)
                except json.JSONDecodeError:
                    pass
            normalized.append(_validate_block(block))
        data = {**data, "blocks": normalized}
    return data


def parse_ai_response(raw: Any) -> AIResponse:
    if isinstance(raw, AIResponse):
        return raw
    if isinstance(raw, BaseModel):
        return AIResponse.model_validate(_normalize_response_dict(raw.model_dump()))
    if isinstance(raw, dict):
        return AIResponse.model_validate(_normalize_response_dict(raw))
    if isinstance(raw, str):
        stripped = raw.strip()
        candidates = [stripped]
        match = _JSON_BLOCK_RE.search(stripped)
        if match:
            candidates.insert(0, match.group(1))
        for candidate in candidates:
            try:
                return AIResponse.model_validate(_normalize_response_dict(json.loads(candidate)))
            except (json.JSONDecodeError, ValidationError):
                continue
        return make_json_fallback_response(stripped)
    return make_json_fallback_response(str(raw))


def _fmt_axis_value(value: float, unit: str | None = None) -> str:
    if unit == "price":
        return _fmt_price(value)
    if unit == "market cap":
        return _fmt_market_cap(value)
    if unit == "%":
        return _fmt_change(value)
    return f"{value:,.2f}"


def _grid_positions(width: int, segments: int = 4) -> list[int]:
    if width <= 1:
        return [0]
    return sorted({round(index * (width - 1) / segments) for index in range(segments + 1)})


def _bar_axis_labels(maximum: float, unit: str | None) -> str:
    values = [maximum * index / 4 for index in range(5)]
    return "Scale: " + " | ".join(_fmt_axis_value(value, unit) for value in values)


def _positive_bar(value: float, maximum: float, width: int = 40) -> str:
    if maximum <= 0:
        return ""
    filled = max(1, round((value / maximum) * (width - 1))) if value > 0 else 0
    grid = set(_grid_positions(width))
    chars = []
    for index in range(width):
        if index <= filled and value > 0:
            chars.append("=")
        elif index in grid:
            chars.append("|")
        else:
            chars.append(".")
    return "".join(chars)


def _change_bar(value: float, maximum: float, width: int = 19) -> str:
    if maximum <= 0:
        return "." * width + "|" + "." * width
    left_grid = set(_grid_positions(width)) - {width - 1}
    right_grid = set(_grid_positions(width)) - {0}
    left = ["|" if index in left_grid else "." for index in range(width)]
    right = ["|" if index in right_grid else "." for index in range(width)]
    fill = min(width, round((abs(value) / maximum) * width))
    if value < 0:
        for index in range(width - fill, width):
            left[index] = "="
    elif value > 0:
        for index in range(fill):
            right[index] = "="
    return "".join(left) + "|" + "".join(right)


def _value_to_row(value: float, low: float, high: float, rows: int) -> int:
    if rows <= 1 or math.isclose(low, high):
        return 0
    ratio = (high - value) / (high - low)
    return min(rows - 1, max(0, round(ratio * (rows - 1))))


def _render_candlestick_lines(block_obj: CandlestickChartBlock) -> list[str]:
    points = block_obj.points
    if not points:
        return ["No chart data."]

    raw_low = min(point.low for point in points)
    raw_high = max(point.high for point in points)
    span = raw_high - raw_low
    padding = span * 0.08 if span else max(abs(raw_high) * 0.02, 1.0)
    low = raw_low - padding
    high = raw_high + padding
    rows = 14
    x_step = 3
    chart_width = max(1, ((len(points) - 1) * x_step) + 1)
    grid_rows = set(_grid_positions(rows))
    lines = []

    for row in range(rows):
        price = high - ((high - low) * row / (rows - 1) if rows > 1 else 0)
        cells: dict[int, tuple[str, str]] = {}
        for index, point in enumerate(points):
            x = index * x_step
            high_row = _value_to_row(point.high, low, high, rows)
            low_row = _value_to_row(point.low, low, high, rows)
            open_row = _value_to_row(point.open, low, high, rows)
            close_row = _value_to_row(point.close, low, high, rows)
            body_top = min(open_row, close_row)
            body_bottom = max(open_row, close_row)
            color = "bright_green" if point.close >= point.open else "bright_red"

            if high_row <= row <= low_row:
                cells[x] = ("|", color)
            if body_top <= row <= body_bottom:
                cells[x] = ("=" if point.close >= point.open else "x", color)

        body = []
        for column in range(chart_width):
            if column in cells:
                char, color = cells[column]
                body.append(f"[{color}]{char}[/{color}]")
            elif row in grid_rows:
                body.append("[bright_black].[/bright_black]")
            else:
                body.append(" ")
        lines.append(f"[bright_black]{_fmt_price(price):>10} |[/bright_black] {''.join(body)}")

    first = points[0].date
    last = points[-1].date
    lines.append(f"[bright_black]{'':>10} + {'-' * chart_width}[/bright_black]")
    lines.append(f"[bright_black]{'Dates':>10}[/bright_black]   [cyan]{first}[/cyan] [bright_white]->[/bright_white] [cyan]{last}[/cyan]")
    lines.append("[bright_black]Legend:[/bright_black] [bright_green]= close >= open[/bright_green], [bright_red]x close < open[/bright_red], | wick high/low")
    if block_obj.summary:
        lines.append(f"[bright_white]{block_obj.summary}[/bright_white]")
    return lines


def render_block(console: Console, block: UIBlock | dict[str, Any]) -> None:
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

    if isinstance(block_obj, LineChartBlock):
        body = []
        if block_obj.series:
            for item in block_obj.series:
                values = [point.value for point in item.points]
                spark = _sparkline(values)
                body.append(f"[bold bright_cyan]{item.label}[/bold bright_cyan]: [bold bright_magenta]{spark or 'No chart data.'}[/bold bright_magenta]")
            first_points = next((item.points for item in block_obj.series if item.points), [])
            if first_points:
                body.append(f"[bright_black]Range:[/bright_black] [cyan]{first_points[0].date}[/cyan] [bright_white]->[/bright_white] [cyan]{first_points[-1].date}[/cyan]")
        else:
            values = [point.value for point in block_obj.points]
            spark = _sparkline(values)
            label = f"[bold bright_cyan]{block_obj.label or block_obj.ticker}[/bold bright_cyan]: " if (block_obj.label or block_obj.ticker) else ""
            body.append(f"{label}[bold bright_magenta]{spark or 'No chart data.'}[/bold bright_magenta]")
            if block_obj.points:
                body.append(f"[bright_black]Range:[/bright_black] [cyan]{block_obj.points[0].date}[/cyan] [bright_white]->[/bright_white] [cyan]{block_obj.points[-1].date}[/cyan]")
        if block_obj.summary:
            body.append(f"[bright_white]{block_obj.summary}[/bright_white]")
        console.print(Panel("\n".join(body), title=block_obj.title or "Line chart", title_align="left", border_style="bright_magenta", expand=False))
        return

    if isinstance(block_obj, BarChartBlock):
        if not block_obj.items:
            console.print(Panel("No chart data.", title=block_obj.title or "Chart", title_align="left", border_style="bright_green", expand=False))
            return

        lines = []
        if block_obj.unit == "%":
            max_abs = max((abs(item.value) for item in block_obj.items), default=1.0)
            lines.append(f"[bright_black]Scale: {_fmt_axis_value(-max_abs, '%')} | {_fmt_axis_value(0.0, '%')} | {_fmt_axis_value(max_abs, '%')}[/bright_black]")
            lines.append(f"[bright_black]{'':>6}  {'negative':>19}|{'positive':<19}[/bright_black]")
            for item in block_obj.items:
                color = item.color or ("bright_green" if item.value >= 0 else "bright_red")
                bar = _change_bar(item.value, max_abs)
                lines.append(f"[bold bright_cyan]{item.label:>6}[/bold bright_cyan]  [{color}]{bar}[/{color}] [bold {color}]{item.display_value}[/bold {color}]")
        else:
            items = sorted(block_obj.items, key=lambda item: item.value, reverse=True)
            maximum = max((item.value for item in items), default=1.0)
            lines.append(f"[bright_black]{_bar_axis_labels(maximum, block_obj.unit)}[/bright_black]")
            for item in items:
                color = item.color or "bright_cyan"
                bar = _positive_bar(item.value, maximum)
                lines.append(f"[bold bright_cyan]{item.label:>6}[/bold bright_cyan]  [{color}]{bar}[/{color}] [bold {color}]{item.display_value}[/bold {color}]")
        if block_obj.summary:
            lines.extend(["", f"[bright_white]{block_obj.summary}[/bright_white]"])
        console.print(Panel("\n".join(lines), title=block_obj.title or "Chart", title_align="left", border_style="bright_green", expand=False))
        return

    if isinstance(block_obj, CandlestickChartBlock):
        title = block_obj.title or f"{block_obj.ticker or 'Ticker'} OHLC chart"
        console.print(Panel("\n".join(_render_candlestick_lines(block_obj)), title=title, title_align="left", border_style="bright_green", expand=False))
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


def render_response(console: Console, response: AIResponse | dict[str, Any]) -> None:
    response_obj = response if isinstance(response, AIResponse) else AIResponse.model_validate(response)
    if response_obj.message:
        console.print(Panel(Markdown(response_obj.message), title="StockSensei", title_align="left", border_style="bright_blue", expand=False))
    for block in response_obj.blocks:
        render_block(console, block)
