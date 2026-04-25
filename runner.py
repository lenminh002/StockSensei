from __future__ import annotations

import asyncio
import json
import random

from rich.console import Console
from rich.live import Live
from rich.text import Text

from ui_blocks import AIResponse, make_json_fallback_response, parse_ai_response, render_block
from utils import stringify_message_content

# ---------------------------------------------------------------------------
# Status animation labels — shown while the agent is working
# ---------------------------------------------------------------------------

STATUS_LABELS = [
    "cooking",
    "drawing",
    "mewing",
    "brewing",
    "thinking",
    "plotting",
    "scheming",
    "vibing",
    "whisking",
    "forging",
    "mixing",
    "stirring",
]

# ---------------------------------------------------------------------------
# Tool-specific status messages — shown during individual tool calls
# ---------------------------------------------------------------------------

TOOL_MESSAGES = {
    "get_price": ("Fetching live price", "Fetched live price"),
    "get_stock_summary": ("Pulling stock summary", "Stock summary ready"),
    "get_company_summary": ("Reading company profile", "Company profile ready"),
    "get_historical_data": ("Loading price history", "Price history ready"),
    "get_news": ("Scanning latest headlines", "Headlines ready"),
    "compare_stocks": ("Comparing live quotes", "Quote comparison ready"),
    "compare_stocks_summary": ("Comparing valuation data", "Valuation comparison ready"),
    "build_snapshot_card_visual": ("Building snapshot card", "Snapshot card ready"),
    "build_52w_range_visual": ("Building 52-week range", "52-week range ready"),
    "build_price_comparison_visual": ("Building comparison table", "Comparison table ready"),
    "build_summary_comparison_visual": ("Building company summary table", "Company summary table ready"),
    "build_price_chart_visual": ("Drawing price bars", "Price bars ready"),
    "build_change_chart_visual": ("Drawing daily change bars", "Daily change bars ready"),
    "build_market_cap_chart_visual": ("Drawing market-cap bars", "Market-cap bars ready"),
    "build_history_chart_visual": ("Drawing trend view", "Trend view ready"),
    "build_news_visual": ("Formatting news list", "News list ready"),
}


def _tool_message(name: str, phase: str) -> str:
    """Return the appropriate status label for a tool call start or end."""
    start, end = TOOL_MESSAGES.get(name, (f"Running {name}", f"Finished {name}"))
    return start if phase == "start" else end


def _block_key(block: dict) -> str:
    """Stable deduplication key for a rendered UI block."""
    return json.dumps(block, sort_keys=True)


# ---------------------------------------------------------------------------
# Response extraction
# ---------------------------------------------------------------------------

def _extract_response_from_state(state: dict) -> AIResponse:
    """Pull the AI response out of the agent's final state dict."""
    structured = state.get("structured_response")
    if structured:
        return parse_ai_response(structured)

    messages = state.get("messages") or []
    if messages:
        content = stringify_message_content(messages[-1].content)
        return parse_ai_response(content)

    return make_json_fallback_response("No response available from the agent.")


# ---------------------------------------------------------------------------
# Async streaming helpers
# ---------------------------------------------------------------------------

async def _animate_status(stop_event: asyncio.Event, live: Live, status_ref: dict[str, str]) -> None:
    """Animate a cycling status line in the terminal while the agent works."""
    frames = [".", "..", "..."]
    index = 0
    fallback = random.choice(STATUS_LABELS)
    while not stop_event.is_set():
        if index and index % 12 == 0 and status_ref.get("label", fallback) == fallback:
            fallback = random.choice(STATUS_LABELS)
        label = status_ref.get("label", fallback)
        frame = frames[index % len(frames)]
        live.update(Text(f"StockSensei {label}{frame}", style="dim cyan"))
        index += 1
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=0.28)
        except TimeoutError:
            pass


async def _invoke_agent_stream(agent, user_input: str, run_config: dict, live: Live) -> tuple[dict, set[str]]:
    """Stream agent events, render UI blocks eagerly, and return the final state."""
    payload = {"messages": [{"role": "user", "content": user_input}]}
    final_state: dict | None = None
    rendered_blocks: set[str] = set()
    stop_event = asyncio.Event()
    status_ref = {"label": random.choice(STATUS_LABELS)}
    status_task = asyncio.create_task(_animate_status(stop_event, live, status_ref))

    try:
        async for event in agent.astream_events(payload, config=run_config, version="v2"):
            event_name = event.get("event")
            name = event.get("name") or "tool"
            data = event.get("data") or {}

            if event_name == "on_tool_start":
                status_ref["label"] = _tool_message(name, "start")
            elif event_name == "on_tool_end":
                status_ref["label"] = _tool_message(name, "end")
                output = data.get("output")
                if isinstance(output, dict) and isinstance(output.get("block"), dict):
                    block = output["block"]
                    key = _block_key(block)
                    if key not in rendered_blocks:
                        live.console.print()
                        render_block(live.console, block)
                        rendered_blocks.add(key)
                        await asyncio.sleep(0.18)
            elif event_name == "on_chain_end":
                output = data.get("output")
                if isinstance(output, dict) and ("structured_response" in output or "messages" in output):
                    final_state = output

        if final_state is None:
            raise RuntimeError("Agent stream completed without final state.")
        return final_state, rendered_blocks
    finally:
        stop_event.set()
        await status_task


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_agent(agent, user_input: str, run_config: dict, console: Console) -> AIResponse:
    """Invoke the agent and return a fully parsed AIResponse, handling errors gracefully."""
    try:
        with Live(Text("StockSensei thinking.", style="dim cyan"), console=console, refresh_per_second=12, transient=True) as live:
            state, rendered_blocks = asyncio.run(_invoke_agent_stream(agent, user_input, run_config, live))
        response = _extract_response_from_state(state)
        response.blocks = [
            block for block in response.blocks
            if _block_key(block if isinstance(block, dict) else block.model_dump()) not in rendered_blocks
        ]
        return response
    except KeyboardInterrupt:
        raise
    except Exception as exc:
        return make_json_fallback_response(
            f"The agent failed while producing a structured response.\n\nError: {exc}",
            error="structured-output fallback",
        )
