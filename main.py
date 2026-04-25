from __future__ import annotations

import asyncio
import json
import random
from uuid import uuid4

from dotenv import find_dotenv, load_dotenv
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.text import Text

from agent import get_agent
from command_prompt import CommandPrompt
from config import current_provider_info, ensure_config, switch_model_interactive
from ui_blocks import AIResponse, make_json_fallback_response, parse_ai_response, render_block, render_response
from utils import CYAN, GREEN, RESET, YELLOW, stringify_message_content

console = Console()


def _build_agent(config: dict):
    """Construct LangChain agent instance using active configuration."""
    name, model, lc_provider, base_url, api_key = current_provider_info(config)
    agent = get_agent(model, lc_provider, api_key, base_url)
    label = f"{name} / {model}"
    return agent, label


def _new_run_config() -> dict:
    """Create fresh conversation thread id for session."""
    return {"configurable": {"thread_id": f"stocksensei_{uuid4()}"}}


def _show_help() -> None:
    console.print(
        Markdown(
            """
## Commands

- `/models` — switch AI provider or model
- `/clear` — clear conversation history
- `/help` — show this help
- `/quit` — exit StockSensei

### Interactive input
- Typing `/` in an interactive terminal opens slash-command completion suggestions.
- StockSensei shows a single animated status line while it works.

### Natural-language examples
- `price of nvda`
- `compare nvda and amd`
- `show me apple's latest news`
- `show me tesla's chart for 3 months`
- `which looks cheaper, msft or googl?`
""".strip()
        )
    )


def _extract_response_from_state(state: dict) -> AIResponse:
    structured = state.get("structured_response")
    if structured:
        return parse_ai_response(structured)

    messages = state.get("messages") or []
    if messages:
        content = stringify_message_content(messages[-1].content)
        return parse_ai_response(content)

    return make_json_fallback_response("No response available from the agent.")


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
    start, end = TOOL_MESSAGES.get(name, (f"Running {name}", f"Finished {name}"))
    return start if phase == "start" else end


def _block_key(block: dict) -> str:
    return json.dumps(block, sort_keys=True)


async def _animate_status(stop_event: asyncio.Event, live: Live, status_ref: dict[str, str]) -> None:
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


def _run_agent(agent, user_input: str, run_config: dict) -> AIResponse:
    try:
        with Live(Text("StockSensei thinking.", style="dim cyan"), console=console, refresh_per_second=12, transient=True) as live:
            state, rendered_blocks = asyncio.run(_invoke_agent_stream(agent, user_input, run_config, live))
        response = _extract_response_from_state(state)
        response.blocks = [block for block in response.blocks if _block_key(block if isinstance(block, dict) else block.model_dump()) not in rendered_blocks]
        return response
    except KeyboardInterrupt:
        raise
    except Exception as exc:
        return make_json_fallback_response(
            f"The agent failed while producing a structured response.\n\nError: {exc}",
            error="structured-output fallback",
        )


def main():
    """Start main StockSensei application and terminal chat loop."""
    load_dotenv(find_dotenv(usecwd=True))

    config = ensure_config()
    agent, label = _build_agent(config)
    run_config = _new_run_config()
    prompt = CommandPrompt()

    print(f"\n{GREEN}Hello, I'm StockSensei!{RESET}")
    print(f"{CYAN}Using: {YELLOW}{label}{RESET}")
    print(
        f"{CYAN}Ask me anything about stocks. Type {YELLOW}/models{CYAN} to switch provider/model, "
        f"{YELLOW}/clear{CYAN} to clear conversation history and reset the terminal, "
        f"{YELLOW}/help{CYAN} for commands, or {YELLOW}/quit{CYAN} to quit.{RESET}\n"
    )

    while True:
        try:
            user_input = prompt.prompt("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{GREEN}Goodbye! Happy investing!{RESET}\n")
            break

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit", "q", "/quit"]:
            print(f"\n{GREEN}Goodbye! Happy investing!{RESET}\n")
            break

        if user_input.lower() in ["/models", "/model"]:
            config = switch_model_interactive(config)
            agent, label = _build_agent(config)
            run_config = _new_run_config()
            print(f"{CYAN}Now using: {YELLOW}{label}{RESET}\n")
            continue

        if user_input.lower() == "/clear":
            run_config = _new_run_config()
            console.clear()
            print(f"{GREEN}Conversation cleared.{RESET}\n")
            continue

        if user_input.lower() in ["/help", "help"]:
            _show_help()
            continue

        try:
            response = _run_agent(agent, user_input, run_config)
        except KeyboardInterrupt:
            print(f"\n{YELLOW}Interrupted.{RESET}\n")
            continue

        render_response(console, response)


if __name__ == "__main__":
    main()
