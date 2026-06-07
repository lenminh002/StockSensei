"""Block builder functions: make_*_block() helpers and stock-specific visual builder helpers.

Depends on: stocksensei.core.block_models, stocksensei.core.block_formatting
"""
from __future__ import annotations

from typing import Any

from stocksensei.core.block_formatting import (
    _fmt_change,
    _fmt_compact_number,
    _fmt_market_cap,
    _fmt_pe,
    _fmt_price,
    _is_finite_number,
)
from stocksensei.core.block_models import (
    BarChartBlock,
    CandlestickChartBlock,
    LineChartBlock,
    MetricCardBlock,
    NewsBlock,
    RangeBarBlock,
    TableBlock,
    TextBlock,
    _stringify_cell,
)


# ---------------------------------------------------------------------------
# Generic block builders
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Stock-specific visual builder helpers (used by visual builder tools)
# ---------------------------------------------------------------------------

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
