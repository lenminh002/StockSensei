from __future__ import annotations

from typing import Any

import yfinance as yf
from langchain.tools import tool

from ui_blocks import (
    make_52w_range_block,
    make_barchart_block,
    make_change_barchart_block,
    make_history_chart_block,
    make_market_cap_barchart_block,
    make_news_block,
    make_price_comparison_block,
    make_snapshot_card_block,
    make_summary_comparison_block,
)


def normalize_ticker(ticker: str) -> str:
    """Normalize user-supplied ticker symbols for consistent downstream lookups."""
    return ticker.strip().upper().lstrip("$")


def parse_ticker_list(tickers: str) -> list[str]:
    """Parse comma-separated tickers and discard blanks."""
    return [normalize_ticker(t) for t in tickers.split(",") if t.strip()]


def _safe_round(value: Any, digits: int = 2) -> float | None:
    """Round numeric values defensively and preserve missing values as None."""
    if isinstance(value, (int, float)):
        return round(float(value), digits)
    return None


def _ticker_info(ticker: str) -> dict[str, Any]:
    """Fetch Yahoo Finance info dict for a ticker symbol."""
    return yf.Ticker(ticker).info or {}


def fetch_stock_snapshot(ticker: str) -> dict[str, Any]:
    """Return a normalized stock snapshot used by both tools and thesis workflows."""
    symbol = normalize_ticker(ticker)
    if not symbol:
        return {"ticker": symbol, "error": "Ticker is required."}

    try:
        info = _ticker_info(symbol)
    except Exception as exc:
        return {"ticker": symbol, "error": f"Failed to fetch data: {exc}"}

    price = info.get("currentPrice")
    change = info.get("regularMarketChangePercent")
    market_cap = info.get("marketCap")
    summary = {
        "ticker": symbol,
        "company_name": info.get("shortName") or info.get("longName") or symbol,
        "price": _safe_round(price),
        "change_percent": _safe_round(change, 4),
        "market_cap": market_cap if isinstance(market_cap, (int, float)) else None,
        "pe_ratio": _safe_round(info.get("trailingPE"), 4),
        "forward_pe": _safe_round(info.get("forwardPE"), 4),
        "week_52_high": _safe_round(info.get("fiftyTwoWeekHigh")),
        "week_52_low": _safe_round(info.get("fiftyTwoWeekLow")),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "summary": info.get("longBusinessSummary") or "No summary available.",
        "currency": info.get("currency") or "USD",
    }

    if summary["price"] is None and summary["market_cap"] is None and summary["summary"] == "No summary available.":
        summary["error"] = f"No market data found for {symbol}. The ticker may be invalid or temporarily unavailable."

    return summary


def fetch_historical_records(ticker: str, period: str = "1mo") -> dict[str, Any]:
    """Return normalized OHLC history for a ticker."""
    symbol = normalize_ticker(ticker)
    if not symbol:
        return {"ticker": symbol, "period": period, "data": [], "error": "Ticker is required."}

    try:
        hist = yf.Ticker(symbol).history(period=period)
        if hist.empty:
            return {
                "ticker": symbol,
                "period": period,
                "data": [],
                "error": f"No historical data found for {symbol} for period '{period}'.",
            }

        df = hist[["Open", "High", "Low", "Close"]].round(2).tail(10)
        df.index = df.index.strftime("%Y-%m-%d")
        records = [
            {
                "date": date,
                "open": float(row.Open),
                "high": float(row.High),
                "low": float(row.Low),
                "close": float(row.Close),
            }
            for date, row in df.iterrows()
        ]
        return {"ticker": symbol, "period": period, "data": records}
    except Exception as exc:
        return {"ticker": symbol, "period": period, "data": [], "error": f"Failed to fetch history: {exc}"}


def fetch_news_headlines(ticker: str, limit: int = 10) -> dict[str, Any]:
    """Return normalized news headlines for a ticker."""
    symbol = normalize_ticker(ticker)
    if not symbol:
        return {"ticker": symbol, "headlines": [], "error": "Ticker is required."}

    try:
        news_items = yf.Ticker(symbol).news or []
        headlines: list[str] = []
        for item in news_items[:limit]:
            content = item.get("content") or {}
            title = content.get("title")
            if title:
                headlines.append(title)

        if not headlines:
            return {"ticker": symbol, "headlines": [], "error": f"No recent news found for {symbol}."}
        return {"ticker": symbol, "headlines": headlines}
    except Exception as exc:
        return {"ticker": symbol, "headlines": [], "error": f"Failed to fetch news: {exc}"}


def _price_row(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "ticker": snapshot["ticker"],
        "company_name": snapshot.get("company_name"),
        "price": snapshot.get("price"),
        "change_percent": snapshot.get("change_percent"),
        **({"error": snapshot["error"]} if snapshot.get("error") else {}),
    }


def _summary_row(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "ticker": snapshot["ticker"],
        "company_name": snapshot.get("company_name"),
        "market_cap": snapshot.get("market_cap"),
        "pe_ratio": snapshot.get("pe_ratio"),
        "forward_pe": snapshot.get("forward_pe"),
        "week_52_high": snapshot.get("week_52_high"),
        "week_52_low": snapshot.get("week_52_low"),
        "sector": snapshot.get("sector"),
        "industry": snapshot.get("industry"),
        **({"error": snapshot["error"]} if snapshot.get("error") else {}),
    }


@tool
def get_price(ticker: str) -> dict:
    """Get the current stock price and percentage change for a given ticker symbol."""
    return _price_row(fetch_stock_snapshot(ticker))


@tool
def get_stock_summary(ticker: str) -> dict:
    """Get a summary of a stock including market cap, P/E ratio, and 52-week high/low."""
    return _summary_row(fetch_stock_snapshot(ticker))


@tool
def get_company_summary(ticker: str) -> dict:
    """Get a brief description of the company associated with the given stock ticker symbol."""
    snapshot = fetch_stock_snapshot(ticker)
    return {
        "ticker": snapshot["ticker"],
        "company_name": snapshot.get("company_name"),
        "summary": snapshot.get("summary"),
        "sector": snapshot.get("sector"),
        "industry": snapshot.get("industry"),
        **({"error": snapshot["error"]} if snapshot.get("error") else {}),
    }


@tool
def get_historical_data(ticker: str, period: str = "1mo") -> dict:
    """Get historical OHLC stock price data for a given ticker symbol."""
    return fetch_historical_records(ticker, period)


@tool
def get_news(ticker: str) -> dict:
    """Get the latest news headlines for a given stock ticker symbol."""
    return fetch_news_headlines(ticker)


@tool
def compare_stocks(tickers: str) -> dict:
    """Compare current price and daily change for multiple stocks. Pass tickers as comma-separated values e.g. 'AAPL,TSLA'."""
    return {"stocks": [_price_row(fetch_stock_snapshot(ticker)) for ticker in parse_ticker_list(tickers)]}


@tool
def compare_stocks_summary(tickers: str) -> dict:
    """Compare market cap, P/E ratio, and 52-week high/low for multiple stocks. Pass tickers as comma-separated values e.g. 'AAPL,TSLA'."""
    return {"stocks": [_summary_row(fetch_stock_snapshot(ticker)) for ticker in parse_ticker_list(tickers)]}


@tool
def build_snapshot_card_visual(ticker: str) -> dict:
    """Build a render-ready summary card for a single ticker snapshot."""
    snapshot = fetch_stock_snapshot(ticker)
    return {"block": make_snapshot_card_block(snapshot)}


@tool
def build_52w_range_visual(ticker: str) -> dict:
    """Build a render-ready 52-week range bar with current price position."""
    snapshot = fetch_stock_snapshot(ticker)
    return {"block": make_52w_range_block(snapshot)}


@tool
def build_price_comparison_visual(tickers: str) -> dict:
    """Build a render-ready comparison table block for prices and daily change across tickers."""
    data = compare_stocks.func(tickers)
    return {"block": make_price_comparison_block(data.get("stocks", []), title="Price comparison")}


@tool
def build_summary_comparison_visual(tickers: str) -> dict:
    """Build a render-ready comparison table block for valuation and 52-week ranges across tickers."""
    data = compare_stocks_summary.func(tickers)
    return {"block": make_summary_comparison_block(data.get("stocks", []), title="Valuation summary")}


@tool
def build_change_chart_visual(tickers: str) -> dict:
    """Build a render-ready daily percent change bar chart across tickers."""
    data = compare_stocks.func(tickers)
    return {"block": make_change_barchart_block(data.get("stocks", []), title="Daily change chart")}


@tool
def build_market_cap_chart_visual(tickers: str) -> dict:
    """Build a render-ready market-cap bar chart across tickers."""
    data = compare_stocks_summary.func(tickers)
    return {"block": make_market_cap_barchart_block(data.get("stocks", []), title="Market cap chart")}


@tool
def build_price_chart_visual(tickers: str) -> dict:
    """Build a render-ready price bar chart across tickers."""
    data = compare_stocks.func(tickers)
    stocks = data.get("stocks", [])
    items = []
    for stock in stocks:
        price = stock.get("price")
        if isinstance(price, (int, float)):
            items.append({
                "label": stock.get("ticker") or "?",
                "value": float(price),
                "display_value": f"${price:.2f}",
                "color": "bright_magenta",
            })
    return {"block": make_barchart_block(items, title="Price bar chart", unit="price", summary="Relative share price by ticker")}


@tool
def build_history_chart_visual(ticker: str, period: str = "1mo") -> dict:
    """Build a render-ready sparkline chart block from recent historical closing prices."""
    history = fetch_historical_records(ticker, period)
    return {"block": make_history_chart_block(history)}


@tool
def build_news_visual(ticker: str) -> dict:
    """Build a render-ready news list block from recent headlines for a ticker."""
    news = fetch_news_headlines(ticker)
    return {"block": make_news_block(news.get("headlines", []), ticker=news.get("ticker"), title=f"News for {news.get('ticker', normalize_ticker(ticker))}")}
