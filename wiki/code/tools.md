---
status: code-map
path: tools.py
language: python
updated: 2026-05-21
---

## Purpose
Defines stock data tools and visual builder tools exposed to the LangChain agent.

## Functions / Sections
- `normalize_ticker(ticker)` - normalizes ticker symbols for downstream lookups.
- `parse_ticker_list(tickers)` - parses comma-separated ticker input.
- `_safe_round(value, digits)` - rounds numeric values defensively.
- `_ticker_info(ticker)` - fetches Yahoo Finance info for a ticker.
- `fetch_stock_snapshot(ticker)` - returns normalized stock snapshot data.
- `fetch_historical_records(ticker, period)` - returns normalized recent OHLC records.
- `fetch_news_headlines(ticker, limit)` - returns normalized headline strings.
- `_price_row(snapshot)` - extracts price comparison fields from a snapshot.
- `_summary_row(snapshot)` - extracts valuation and company fields from a snapshot.
- `get_price(ticker)` - LangChain tool for current price and daily change.
- `get_stock_summary(ticker)` - LangChain tool for valuation and 52-week data.
- `get_company_summary(ticker)` - LangChain tool for company description data.
- `get_historical_data(ticker, period)` - LangChain tool for historical OHLC data.
- `get_news(ticker)` - LangChain tool for latest headlines.
- `compare_stocks(tickers)` - LangChain tool for price/change comparisons.
- `compare_stocks_summary(tickers)` - LangChain tool for valuation comparisons.
- `build_snapshot_card_visual(ticker)` - builds a metric-card visual block.
- `build_52w_range_visual(ticker)` - builds a 52-week range visual block.
- `build_price_comparison_visual(tickers)` - builds a price comparison table block.
- `build_summary_comparison_visual(tickers)` - builds a valuation table block.
- `build_change_chart_visual(tickers)` - builds a daily-change bar chart block.
- `build_market_cap_chart_visual(tickers)` - builds a market-cap bar chart block.
- `build_price_chart_visual(tickers)` - builds a share-price bar chart block.
- `build_history_chart_visual(ticker, period)` - builds a trend sparkline block.
- `build_news_visual(ticker)` - builds a news-list block.

## Imports / Links
- [[ui_blocks]] - supplies visual block builder functions.
- external: yfinance - fetches market data and news.
- external: langchain - decorates functions as tools.
- external: typing - annotates dynamic market data payloads.
