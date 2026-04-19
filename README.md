# StockSensei 📈

StockSensei is an intelligent, AI-powered **terminal CLI application** that acts as your personal expert financial analyst — running entirely inside your terminal. Built with Python, LangChain, and `yfinance`, it lets you query real-time stock data, compare companies, generate ASCII price charts, and read market news using plain natural language. No browser. No dashboard. Just your terminal.

---

## ✨ Features

- **🖥️ Runs Entirely in Your Terminal** — A first-class command-line experience built for developers and traders who live in the terminal. Launch it globally with one command from any directory.
- **💬 Natural Language Interaction** — Ask questions the way you think: *"Is NVDA a better buy than AAPL right now?"* or *"Show me Tesla's trend over the last 3 months."*
- **📊 ASCII Price Charts** — Visualize historical price trends right in your terminal with a generated scatter chart, sparkline trend indicator, and annotated date range.
- **📋 Beautiful Data Tables** — Side-by-side stock comparisons are rendered as clean, properly aligned tables using `rich` — no more ugly pipe characters.
- **📡 Real-Time Market Data** — Live prices, daily % changes, market caps, P/E ratios, 52-week highs/lows, and more via `yfinance`.
- **📰 News Integration** — Fetch the latest headlines for any stock or company.
- **🧠 Conversational Memory** — The agent remembers context within your session, so follow-up questions just work.
- **🔐 Zero-Config API Setup** — On first launch, StockSensei securely prompts you for your OpenAI key, validates it live, and saves it globally so you never have to set it again.

---

## 📸 Visual Examples

Here are a few examples of StockSensei's terminal UI in action:

![StockSensei Demonstration 1](./assets/demo.png)
![StockSensei Demonstration 2](./assets/demo2.png)
![StockSensei Demonstration 5](./assets/demo5.png) 

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Language | Python >= 3.13 | Core runtime |
| Financial Data | [yfinance](https://github.com/ranaroussi/yfinance) | Real-time prices, OHLC history, news, company info |
| AI Framework | [LangChain](https://github.com/langchain-ai/langchain) | LLM abstractions, prompt templates, tool-calling agent |
| LLM Provider | [OpenAI](https://openai.com) via `langchain-openai` | GPT model powering the analyst reasoning |
| Agent State | [LangGraph](https://github.com/langchain-ai/langgraph) | Conversation memory and session checkpointing |
| Terminal UI | [Rich](https://github.com/Textualize/rich) | Beautiful markdown tables and formatted output |
| Environment | `python-dotenv` | Secure `.env` loading for local development |
| Package Manager | `uv` | Fast dependency resolution and global CLI installation |

---

## 🚀 Installation & Setup

**The Easiest Way (Global Install)**  
Install StockSensei in a single command directly from GitHub. No cloning required:

```bash
uv tool install git+https://github.com/lenminh002/StockSensei.git
```

Then just run it from anywhere:
```bash
stocksensei
```

On first launch, StockSensei will prompt you for your **OpenAI API Key**, validate it live, and save it permanently — so you only ever need to do this once.

---

**Developer Setup (Local Cloning)**  
To modify the code or contribute:
```bash
git clone https://github.com/lenminh002/StockSensei.git
cd StockSensei
uv sync
uv run main.py
```
*(Place your OpenAI API key in a `.env` file for local development.)*

---

## 💡 Usage

Once running, just type your questions in plain English:

```
You: nvidia vs apple
StockSensei: [Renders a comparison table with price, P/E, market cap, 52w range]

You: show me nvda's chart for the last 3 months
StockSensei: [Draws an ASCII price chart with date range and trend indicator]

You: what's the latest news on tesla?
StockSensei: [Lists the 10 most recent headlines]
```

Type `exit`, `quit`, or `q` to close the app.

---

## 📝 Notes

- **API Key:** Requires an [OpenAI API Key](https://platform.openai.com/account/api-keys). StockSensei handles the setup automatically on first launch.
- **Cross-Platform:** Works on macOS, Linux, and Windows (PowerShell).

---

## 🗑️ Uninstall

To completely remove StockSensei from your system:

**1. Uninstall the CLI tool:**
```bash
uv tool uninstall stocksensei
```

**2. Remove the saved API key** *(optional — only if you want a full clean removal):*

Mac/Linux:
```bash
rm ~/.stocksensei_env
```

Windows (PowerShell):
```powershell
Remove-Item "$HOME\.stocksensei_env"
```

