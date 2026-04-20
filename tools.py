import yfinance as yf
from langchain.tools import tool


@tool
def get_price(ticker: str) -> dict:
    """Get the current stock price and percentage change for a given ticker symbol."""
    try:
        info = yf.Ticker(ticker).info
        return {
            "ticker": ticker.upper(),
            "price": round(info["currentPrice"], 2),
            "change_percent": round(info["regularMarketChangePercent"], 4),
        }
    except Exception as e:
        return {"error": str(e), "ticker": ticker.upper()}


@tool
def get_stock_summary(ticker: str) -> dict:
    """Get a summary of a stock including market cap, P/E ratio, and 52-week high/low."""
    try:
        info = yf.Ticker(ticker).info
        return {
            "ticker": ticker.upper(),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "week_52_high": info.get("fiftyTwoWeekHigh"),
            "week_52_low": info.get("fiftyTwoWeekLow"),
        }
    except Exception as e:
        return {"error": str(e), "ticker": ticker.upper()}


@tool
def get_company_summary(ticker: str) -> dict:
    """Get a brief description of the company associated with the given stock ticker symbol."""
    try:
        info = yf.Ticker(ticker).info
        return {
            "ticker": ticker.upper(),
            "summary": info.get("longBusinessSummary", "No summary available."),
        }
    except Exception as e:
        return {"error": str(e), "ticker": ticker.upper()}


@tool
def get_historical_data(ticker: str, period: str = "1mo") -> dict:
    """Get historical OHLC stock price data for a given ticker symbol."""
    try:
        hist = yf.Ticker(ticker).history(period=period)
        if hist.empty:
            return {"ticker": ticker.upper(), "period": period, "data": []}
        df = hist[["Open", "High", "Low", "Close"]].round(2).tail(10)
        df.index = df.index.strftime("%Y-%m-%d")
        records = [
            {"date": date, "open": row.Open, "high": row.High, "low": row.Low, "close": row.Close}
            for date, row in df.iterrows()
        ]
        return {"ticker": ticker.upper(), "period": period, "data": records}
    except Exception as e:
        return {"error": str(e), "ticker": ticker.upper()}


@tool
def get_news(ticker: str) -> dict:
    """Get the latest news headlines for a given stock ticker symbol."""
    try:
        news = yf.Ticker(ticker).news
        headlines = [item["content"]["title"] for item in (news or [])[:10]]
        return {"ticker": ticker.upper(), "headlines": headlines}
    except Exception as e:
        return {"error": str(e), "ticker": ticker.upper()}


@tool
def compare_stocks(tickers: str) -> dict:
    """Compare current price and daily change for multiple stocks. Pass tickers as comma-separated values e.g. 'AAPL,TSLA'."""
    stocks = []
    for ticker in tickers.split(","):
        ticker = ticker.strip().upper()
        try:
            info = yf.Ticker(ticker).info
            stocks.append({
                "ticker": ticker,
                "price": round(info["currentPrice"], 2),
                "change_percent": round(info["regularMarketChangePercent"], 4),
            })
        except Exception as e:
            stocks.append({"ticker": ticker, "error": str(e)})
    return {"stocks": stocks}


@tool
def compare_stocks_summary(tickers: str) -> dict:
    """Compare market cap, P/E ratio, and 52-week high/low for multiple stocks. Pass tickers as comma-separated values e.g. 'AAPL,TSLA'."""
    stocks = []
    for ticker in tickers.split(","):
        ticker = ticker.strip().upper()
        try:
            info = yf.Ticker(ticker).info
            stocks.append({
                "ticker": ticker,
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "week_52_high": info.get("fiftyTwoWeekHigh"),
                "week_52_low": info.get("fiftyTwoWeekLow"),
            })
        except Exception as e:
            stocks.append({"ticker": ticker, "error": str(e)})
    return {"stocks": stocks}
