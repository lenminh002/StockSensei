import yfinance as yf
from langchain.tools import tool

# ANSI color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"  
YELLOW = "\033[93m"
RESET = "\033[0m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
GRAY = "\033[37m" 


"""Tools:

    - get_price: Get the current stock price and percentage change for a given ticker symbol.
    - get_stock_summary: Get a summary of a stock including market cap, P/E ratio, and 52-week high/low.
    - get_company_summary: Get a brief summary of the company associated with the given stock ticker symbol.
    - get_historical_data: Get historical stock price data for a given ticker symbol.
    - get_news: Get the latest news headlines for a given stock ticker symbol.
    - compare_stocks: Compare current price and daily change for multiple stocks. 
        Pass tickers as comma-separated values e.g. 'AAPL,TSLA'.

"""


@tool(return_direct=True)
def get_price(ticker: str) -> str:
    """
    Get the current stock price and percentage change for a given ticker symbol.
    
    Args:
        ticker (str): The stock ticker symbol (e.g., 'AAPL' for Apple Inc.).
    
    Returns:
        str: The current stock price and percentage change as a string.
    """
    try:
        stock = yf.Ticker(ticker)
        price = stock.info['currentPrice']
        change = stock.info['regularMarketChangePercent']
        direction = "▲" if change > 0 else "▼"
        change_color = GREEN if change > 0 else RED
        return f"{BLUE}{ticker.upper()}: {YELLOW}${price:.2f} {change_color}{direction}{abs(change):.2f}%{RESET}"
    except Exception as e:
        return f"Error fetching stock price for {ticker.upper()}: \n{str(e)}"
        

@tool(return_direct=True)
def get_stock_summary(ticker: str) -> str:
    """
    Get a summary of a stock including market cap, P/E ratio, and 52-week high/low.

    Args:
        ticker (str): The stock ticker symbol (e.g., 'AAPL' for Apple Inc.).
    
    Returns:
        str: A brief market summary for the stock.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return (
            f"{BLUE}{ticker.upper()} {MAGENTA}Summary{RESET}:\n"
            f"  {YELLOW}Market Cap{RESET} : ${info['marketCap']:,}{RESET}\n"
            f"  {YELLOW}P/E Ratio  {RESET}: {info.get('trailingPE', 'N/A')}\n"
            f"  {YELLOW}52w High   {RESET}: ${info['fiftyTwoWeekHigh']:.2f}\n"
            f"  {YELLOW}52w Low    {RESET}: ${info['fiftyTwoWeekLow']:.2f}"
        )
    except Exception as e:
        return f"Error fetching stock summary for {ticker.upper()}: \n{str(e)}"


@tool
def get_company_summary(ticker: str) -> str:
    """
    Get a brief summary of the company associated with the given stock ticker symbol.
    
    Args:
        ticker (str): The stock ticker symbol (e.g., 'AAPL' for Apple Inc.).
    
    Returns:
        str: A brief summary of the company.
    """
    try:
        stock = yf.Ticker(ticker)
        summary = stock.info.get('longBusinessSummary', 'No summary available.')
        return f"{MAGENTA}Company Summary for {BLUE}{ticker.upper()}:{RESET}\n{summary}"
    except Exception as e:
        return f"Error fetching company summary for {ticker.upper()}: \n{str(e)}"

@tool
def get_historical_data(ticker: str, period: str = "1mo") -> str:
    """
    Get historical stock price data for a given ticker symbol.

    Args:
        ticker (str): The stock ticker symbol (e.g., 'AAPL' for Apple Inc.).
        period (str): The time period for the historical data (e.g., '1mo', '1y').

    Returns:
        str: Historical stock price data as a string.
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        if hist.empty:
            return f"No historical data found for {ticker.upper()}."
        return f"{MAGENTA}Historical data for {BLUE}{ticker.upper()}:{RESET}\n{YELLOW}{hist}{RESET}"
    except Exception as e:
        return f"Error fetching historical data for {ticker.upper()}: \n{str(e)}"

@tool
def get_news(ticker: str) -> str:
    """
    Get the latest news headlines for a given stock ticker symbol.
    
    Args:
        ticker (str): The stock ticker symbol (e.g., 'AAPL' for Apple Inc.).
    
    Returns:
        str: A list of the latest news headlines related to the stock.
    """
    try:
        stock = yf.Ticker(ticker)
        news = stock.news
        if not news:
            return f"No news found for {ticker}."
        
        headlines = []
        for item in news[:10]: # Get the top 10 news items

            title = item.get("content").get("title")
            headlines.append(f"{GRAY}- {title}{RESET}")
        return f"{MAGENTA}Latest news for {BLUE}{ticker.upper()}:{RESET}\n" + "\n".join(headlines)
    except Exception as e:
        return f"Error fetching news for {ticker.upper()}: \n{str(e)}"
    

@tool(return_direct=True)
def compare_stocks(tickers: str) -> str:
    """Compare current price and daily change for multiple stocks. Pass tickers as comma-separated values e.g. 'AAPL,TSLA'."""
    try:
        results = []
        for ticker in tickers.split(","):
            ticker = ticker.strip()

            stock = yf.Ticker(ticker)
            price = stock.info['currentPrice']
            change = stock.info['regularMarketChangePercent']
            direction = "▲" if change > 0 else "▼"
            change_color = GREEN if change > 0 else RED


            results.append(f"{BLUE}{ticker.upper()}{RESET}: {YELLOW}${price:.2f}{RESET} {change_color}{direction} {abs(change):.2f}%{RESET}")
        return "\n".join(results)
    except Exception as e:
        return f"Could not compare stocks: {str(e)}"
    
@tool(return_direct=True)
def compare_stocks_summary(tickers: str) -> str:
    """Compare stock summaries (Market Cap, P/E Ratio, 52-week High/Low) for multiple stocks. Pass tickers as comma-separated values e.g. 'AAPL,TSLA'."""
    try:
        results = []
        for ticker in tickers.split(","):
            ticker = ticker.strip()
            stock = yf.Ticker(ticker)
            info = stock.info
            
            market_cap = info.get('marketCap')
            market_cap_str = f"${market_cap:,}" if isinstance(market_cap, (int, float)) else "N/A"
            
            high = info.get('fiftyTwoWeekHigh')
            high_str = f"${high:.2f}" if isinstance(high, (int, float)) else "N/A"
            
            low = info.get('fiftyTwoWeekLow')
            low_str = f"${low:.2f}" if isinstance(low, (int, float)) else "N/A"
            
            summary = (
                f"{BLUE}{ticker.upper()} {MAGENTA}Summary{RESET}:\n"
                f"  {YELLOW}Market Cap{RESET} : {market_cap_str}\n"
                f"  {YELLOW}P/E Ratio  {RESET}: {info.get('trailingPE', 'N/A')}\n"
                f"  {YELLOW}52w High   {RESET}: {high_str}\n"
                f"  {YELLOW}52w Low    {RESET}: {low_str}"
            )
            results.append(summary)
            
        return "\n\n".join(results)
    except Exception as e:
        return f"Could not compare stocks summary: {str(e)}"

