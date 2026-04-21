from __future__ import annotations

import asyncio
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
from ui_blocks import AIResponse, make_json_fallback_response, parse_ai_response, render_response
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


async def _animate_status(stop_event: asyncio.Event, live: Live) -> None:
    frames = [".", "..", "..."]
    index = 0
    label = random.choice(STATUS_LABELS)
    while not stop_event.is_set():
        if index and index % 9 == 0:
            label = random.choice(STATUS_LABELS)
        frame = frames[index % len(frames)]
        live.update(Text(f"StockSensei {label}{frame}", style="dim cyan"))
        index += 1
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=0.28)
        except TimeoutError:
            pass


async def _invoke_agent_stream(agent, user_input: str, run_config: dict, live: Live) -> dict:
    payload = {"messages": [{"role": "user", "content": user_input}]}
    final_state: dict | None = None
    stop_event = asyncio.Event()
    status_task = asyncio.create_task(_animate_status(stop_event, live))

    try:
        async for event in agent.astream_events(payload, config=run_config, version="v2"):
            if event.get("event") == "on_chain_end":
                output = (event.get("data") or {}).get("output")
                if isinstance(output, dict) and ("structured_response" in output or "messages" in output):
                    final_state = output

        if final_state is None:
            final_state = agent.invoke(payload, config=run_config)
        return final_state
    finally:
        stop_event.set()
        await status_task


def _run_agent(agent, user_input: str, run_config: dict) -> AIResponse:
    try:
        with Live(Text("StockSensei thinking.", style="dim cyan"), console=console, refresh_per_second=12, transient=True) as live:
            state = asyncio.run(_invoke_agent_stream(agent, user_input, run_config, live))
        return _extract_response_from_state(state)
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
        f"{YELLOW}/help{CYAN} for commands, or 'exit' to quit.{RESET}\n"
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
