# StockSensei 📈

StockSensei is an intelligent, AI-powered CLI application that serves as your expert financial analyst. Built using Python, LangChain, and `yfinance`, StockSensei allows you to query stock information, fetch real-time prices, analyze historical data, and read the latest news natively in your terminal using natural language.

## Features ✨

- **Natural Language Interaction:** Ask complex questions about stocks like "Which is a better buy?" or "Give me the top 10 stocks that are down right now."
- **Real-Time Data:** Fetches the latest stock prices, daily percentage changes, market caps, P/E ratios, and more.
- **News Integration:** Get the latest headlines for any given company.
- **Historical Analysis:** Review historical price trends over specific periods.
- **Beautiful Terminal Interface:** Clean, formatted output using ANSI colored tags to highlight money (yellow), ticker names (blue), and positive/negative changes (green/red).

## Visual Example 📸

![StockSensei Demo](./assets/demo.png)

## Tech Stack 🛠️

- **Core Language:** Python >= 3.13 (Utilizing modern features and type hinting)
- **Financial Data Aggregation:** [yfinance](https://github.com/ranaroussi/yfinance) (Fetches real-time market data, company summaries, and news)
- **AI & Agent Framework:** [LangChain](https://github.com/langchain-ai/langchain) (Provides core LLM abstractions, prompt templates, and agent orchestration)
- **Model Integration:** `langchain-openai` (Standardizes communication with underlying foundation models)
- **State Management:** [LangGraph](https://github.com/langchain-ai/langgraph) (Employed selectively for session memory and checkpointing via `MemorySaver`)
- **Environment Management:** `python-dotenv` (Secure loading of API keys and configs from `.env`)
- **Package Manager:** `uv` (Extremely fast Python package resolution and virtual environment creation)

## Installation & Setup 🚀

1. **Clone the repository:**

   ```bash
   git clone https://github.com/lenminh002/StockSensei.git
   cd StockSensei
   ```

2. **Set up the environment:**
   This project uses `uv` for lightning-fast package management. Install dependencies from the `pyproject.toml` / `uv.lock`.

   ```bash
   uv sync
   ```

   _(Alternatively, you can just install via pip: `pip install langchain langchain-openai python-dotenv yfinance langgraph`)_

3. **Environment Variables:**
   Make sure to configure your `.env` file! You will likely need your OpenAI (or equivalent model) API keys for LangChain.
   ```bash
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage 💡

Run the main chat application:

```bash
uv run main.py
```

_(Or `python main.py` if using a traditional virtual environment)._

Once running, simply type your queries:

> **You:** "Give me the summary of AAPL"  
> **StockSensei:** _Responds with beautifully formatted market cap, P/E ratio, and 52-week data._

Type `exit`, `quit`, or `q` to terminate the application.
