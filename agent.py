from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import MemorySaver

from tools import (
    build_52w_range_visual,
    build_change_chart_visual,
    build_history_chart_visual,
    build_market_cap_chart_visual,
    build_news_visual,
    build_price_chart_visual,
    build_price_comparison_visual,
    build_snapshot_card_visual,
    build_summary_comparison_visual,
    compare_stocks,
    compare_stocks_summary,
    get_company_summary,
    get_historical_data,
    get_news,
    get_price,
    get_stock_summary,
)
from ui_blocks import AI_RESPONSE_SCHEMA

TOOLS = [
    get_price,
    get_stock_summary,
    get_company_summary,
    get_historical_data,
    get_news,
    compare_stocks,
    compare_stocks_summary,
    build_snapshot_card_visual,
    build_52w_range_visual,
    build_price_comparison_visual,
    build_summary_comparison_visual,
    build_price_chart_visual,
    build_change_chart_visual,
    build_market_cap_chart_visual,
    build_history_chart_visual,
    build_news_visual,
]

SYSTEM_PROMPT = """
You are StockSensei, a concise stock research assistant for terminal users.

Core rules:
- Never invent financial data. If the user asks for market facts, use tools.
- Tools return structured dictionaries. Read the fields carefully and summarize them clearly.
- If a tool reports an error or missing data, explain that plainly instead of guessing.
- Keep a neutral tone and avoid overstating certainty.
- Do not expose chain-of-thought, hidden reasoning, or internal scratchpad content.

Structured output rules:
- Your final answer must match the AIResponse schema exactly.
- Fill `message` with a short explanation or takeaway for the user.
- Fill `blocks` with ordered UI blocks the terminal can render deterministically.
- Prefer tool-built visual payloads when a chart, news list, or comparison table would help.
- If you use a visual builder tool that returns `{\"block\": ...}`, copy the inner `block` object into your final `blocks` array.
- If no visual is needed, return an empty `blocks` array or a simple text block.

Visual guidance:
- For a single stock snapshot, prefer `build_snapshot_card_visual` and `build_52w_range_visual`, and usually include both.
- For comparisons, include at least one precise table/card and at least one bar-style chart.
- For comparisons, prefer `build_price_comparison_visual` and/or `build_summary_comparison_visual` plus one or more of `build_price_chart_visual`, `build_change_chart_visual`, and `build_market_cap_chart_visual`.
- Prefer cards and bars over standalone sparkline panels unless the user explicitly asks for a chart or trend view.
- For price-trend/history requests, `build_history_chart_visual` is available, but use it sparingly.
- For news requests, prefer `build_news_visual`.
- For simple factual answers, a short message may be enough.
""".strip()

memory = MemorySaver()


def get_agent(model_name: str, langchain_provider: str, api_key: str, base_url: str):
    """Instantiate and return the LangGraph agent equipped with the defined tools."""
    if langchain_provider == "google_genai":
        provider_kwargs = {"google_api_key": api_key}
    elif langchain_provider == "ollama":
        provider_kwargs = {"base_url": base_url}
    else:
        provider_kwargs = {"api_key": api_key, "base_url": base_url}

    model = init_chat_model(
        model_name,
        model_provider=langchain_provider,
        temperature=0.3,
        **provider_kwargs,
    )
    return create_agent(
        model=model,
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
        response_format=AI_RESPONSE_SCHEMA,
        checkpointer=memory,
    )
