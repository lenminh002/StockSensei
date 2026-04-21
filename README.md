# StockSensei 📈

StockSensei is an intelligent, AI-powered **terminal CLI application** that acts as your personal expert stock research assistant — running entirely inside your terminal. Built with Python, LangChain, and `yfinance`, it lets you query real-time stock data, compare companies, render structured terminal visuals, and read market news using plain natural language. No browser. No dashboard. Just your terminal.

---

## ✨ Features

- **🖥️ Runs Entirely in Your Terminal** — A first-class command-line experience built for developers and traders who live in the terminal.
- **💬 Natural Language Interaction** — Ask questions like *"price of nvda"*, *"compare nvda and aapl"*, or *"show me tesla's latest news"*.
- **📊 Structured Visual Blocks** — Cards, bars, tables, and news lists are rendered from structured UI blocks instead of fragile model-authored markdown.
- **📋 Deterministic Terminal Visuals** — Comparison views and stock snapshots render consistently with Rich.
- **📡 Real-Time Market Data** — Live prices, daily % changes, market caps, P/E ratios, 52-week highs/lows, and more via `yfinance`.
- **📰 News Integration** — Fetch the latest headlines for any stock or company.
- **🧠 Conversational Memory** — The agent remembers context within your session, so follow-up questions work naturally.
- **🧱 JSON Output Contract** — The AI returns a structured response schema with a message plus ordered UI blocks, making rendering and fallback behavior safer.
- **⚡ Animated Status Feedback** — StockSensei shows a single animated status line while it works.
- **⌨️ Slash-Command Dropdowns** — In interactive terminals, typing `/` shows command completion suggestions.
- **🤖 Multi-Provider AI Support** — Choose from OpenAI, Anthropic, Gemini, Groq, DeepSeek, OpenRouter, Ollama, or any custom OpenAI-compatible endpoint. Switch providers mid-session with `/models`.
- **🔐 Zero-Config Setup** — On first launch, StockSensei walks you through picking a provider and saving your API key globally.

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Language | Python >= 3.13 | Core runtime |
| Financial Data | [yfinance](https://github.com/ranaroussi/yfinance) | Real-time prices, history, news, company info |
| AI Framework | [LangChain](https://github.com/langchain-ai/langchain) | Tool-calling agent and structured output |
| LLM Providers | OpenAI, Anthropic, Gemini, Groq, DeepSeek, OpenRouter, Ollama | Swappable AI backends via `/models` |
| Agent State | [LangGraph](https://github.com/langchain-ai/langgraph) | Conversation memory and checkpointing |
| Terminal UI | [Rich](https://github.com/Textualize/rich) | Cards, tables, panels, and live status |
| Interactive Input | `prompt-toolkit` | Slash-command completion and terminal prompt UX |
| Environment | `python-dotenv` | Secure `.env` loading for local development |
| Package Manager | `uv` | Fast dependency resolution and CLI installation |

---

## 🚀 Installation & Setup

```bash
uv tool install git+https://github.com/lenminh002/StockSensei.git
stocksensei
```

On first launch, StockSensei will walk you through selecting an AI provider and entering your API key.

For local development:

```bash
git clone https://github.com/lenminh002/StockSensei.git
cd StockSensei
uv sync
uv run main.py
```

---

## 💡 Usage

Example prompts:

```text
price of nvda
compare nvda and aapl
show me apple's latest news
which looks cheaper, msft or googl?
```

Commands:

```text
/help
/models
/quit
```

Type `exit`, `quit`, `q`, or `/quit` to close the app.

### Structured Output Contract

The final AI response follows a schema shaped like:

```json
{
  "message": "Short explanation for the user.",
  "blocks": [
    {
      "type": "metric_card",
      "title": "AAPL snapshot",
      "subtitle": "Apple Inc.",
      "items": [
        {"label": "Price", "value": "$201.68", "tone": "bright_cyan"}
      ]
    },
    {
      "type": "range_bar",
      "title": "AAPL 52-week range",
      "minimum_label": "Low $170",
      "maximum_label": "High $220",
      "current_label": "Current $201.68",
      "position": 0.73
    }
  ]
}
```

### Streaming & Interactive Commands

- StockSensei shows a single animated status line while it works.
- In an interactive TTY session, typing `/` triggers slash-command completion suggestions with descriptions for commands like `/help`, `/models`, and `/quit`.

### Switching Providers & Models

Type `/models` at any time during a session to switch your AI provider or model. Your selection is saved to `~/.stocksensei_config.json` and remembered across sessions.

---

## 📝 Notes

- **Config file:** Provider settings and API keys are stored in `~/.stocksensei_config.json`.
- **Tool architecture:** Market-data tools return clean structured data; visual builder tools return render-ready block payloads; terminal rendering is handled in the CLI layer.
- **Structured rendering:** The CLI validates a JSON response schema and renders supported block types such as text, metric cards, tables, bars, range bars, sparklines, and news lists.
- **Cross-Platform:** Works on macOS, Linux, and Windows (PowerShell).

---

## 🗑️ Uninstall

```bash
uv tool uninstall stocksensei
```

Optional config cleanup:

Mac/Linux:
```bash
rm ~/.stocksensei_config.json
```

Windows (PowerShell):
```powershell
Remove-Item "$HOME\.stocksensei_config.json"
```
