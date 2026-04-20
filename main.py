import re

from dotenv import find_dotenv, load_dotenv
from rich.console import Console
from rich.markdown import Markdown

from agent import get_agent
from config import current_provider_info, ensure_config, switch_model_interactive

CYAN = "\033[96m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

console = Console()


def format_output(text: str) -> str:
    text = re.sub(r'^(?:Final Answer|Thought|Action|Observation):\s*', '', text, flags=re.IGNORECASE).strip()
    color_map = {
        "<BLUE>": "\033[94m", "<YELLOW>": "\033[93m",
        "<GREEN>": "\033[92m", "<RED>": "\033[91m",
        "<RESET>": "\033[0m",
    }
    for tag, code in color_map.items():
        text = text.replace(tag, code)
    return text


def _build_agent(config: dict):
    name, model, lc_provider, base_url, api_key = current_provider_info(config)
    agent = get_agent(model, lc_provider, api_key, base_url)
    label = f"{name} / {model}"
    return agent, label


def main():
    load_dotenv(find_dotenv(usecwd=True))

    config = ensure_config()
    agent, label = _build_agent(config)
    thread_counter = 0
    run_config = {"configurable": {"thread_id": f"stocksensei_chat_v1_{thread_counter}"}}

    print(f"\n{GREEN}Hello, I'm StockSensei!{RESET}")
    print(f"{CYAN}Using: {YELLOW}{label}{RESET}")
    print(f"{CYAN}Ask me anything about stocks. Type {YELLOW}/models{CYAN} to switch provider/model, or 'exit' to quit.{RESET}\n")

    while True:
        user_input = input(f"{YELLOW}You: {RESET}").strip()

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit", "q"]:
            print(f"\n{GREEN}Goodbye! Happy investing!{RESET}\n")
            break

        if user_input.lower() in ["/models", "/model"]:
            config = switch_model_interactive(config)
            agent, label = _build_agent(config)
            thread_counter += 1
            run_config = {"configurable": {"thread_id": f"stocksensei_chat_v1_{thread_counter}"}}
            print(f"{CYAN}Now using: {YELLOW}{label}{RESET}\n")
            continue

        response = agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config=run_config,
        )
        output_text = format_output(response["messages"][-1].content)

        print(f"\n{CYAN}StockSensei:{RESET}")
        console.print(Markdown(output_text))


if __name__ == "__main__":
    main()
