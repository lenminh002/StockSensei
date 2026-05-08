from __future__ import annotations

import warnings
from uuid import uuid4

warnings.filterwarnings("ignore", message=".*non-text parts.*", category=UserWarning)

from dotenv import find_dotenv, load_dotenv
from rich.console import Console
from rich.markdown import Markdown

from agent import get_agent
from command_prompt import CommandPrompt
from config import current_provider_info, ensure_config, switch_model_interactive
from runner import run_agent
from ui_blocks import render_response
from utils import CYAN, GREEN, RESET, YELLOW

console = Console()


# ---------------------------------------------------------------------------
# Agent / session helpers
# ---------------------------------------------------------------------------

def _build_agent(config: dict):
    """Construct LangChain agent instance using active configuration."""
    name, model, lc_provider, base_url, api_key = current_provider_info(config)
    agent = get_agent(model, lc_provider, api_key, base_url)
    label = f"{name} / {model}"
    return agent, label


def _new_run_config() -> dict:
    """Create fresh conversation thread id for session."""
    return {"configurable": {"thread_id": f"stocksensei_{uuid4()}"}}


# ---------------------------------------------------------------------------
# Help display
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Main CLI loop
# ---------------------------------------------------------------------------

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
            response = run_agent(agent, user_input, run_config, console)
        except KeyboardInterrupt:
            print(f"\n{YELLOW}Interrupted.{RESET}\n")
            continue

        render_response(console, response)


if __name__ == "__main__":
    main()
