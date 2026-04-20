from dotenv import find_dotenv, load_dotenv
from rich.console import Console
from rich.markdown import Markdown

from agent import get_agent
from config import current_provider_info, ensure_config, switch_model_interactive
from utils import CYAN, GREEN, RED, RESET, YELLOW, format_output

console = Console()


def _build_agent(config: dict):
    """Construct the LangChain agent instance using the user's active configuration."""
    name, model, lc_provider, base_url, api_key = current_provider_info(config)
    agent = get_agent(model, lc_provider, api_key, base_url)
    label = f"{name} / {model}"
    return agent, label


def main():
    """Start the main StockSensei application and terminal chat loop."""
    load_dotenv(find_dotenv(usecwd=True))

    config = ensure_config()
    agent, label = _build_agent(config)
    thread_counter = 0
    run_config = {"configurable": {"thread_id": f"stocksensei_chat_v1_{thread_counter}"}}

    print(f"\n{GREEN}Hello, I'm StockSensei!{RESET}")
    print(f"{CYAN}Using: {YELLOW}{label}{RESET}")
    print(f"{CYAN}Ask me anything about stocks. Type {YELLOW}/models{CYAN} to switch provider/model, or 'exit' to quit.{RESET}\n")

    while True:
        try:
            user_input = input(f"{YELLOW}You: {RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{GREEN}Goodbye! Happy investing!{RESET}\n")
            break

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

        try:
            response = agent.invoke(
                {"messages": [{"role": "user", "content": user_input}]},
                config=run_config,
            )
        except KeyboardInterrupt:
            print(f"\n{YELLOW}Interrupted.{RESET}\n")
            continue

        raw = response["messages"][-1].content
        if isinstance(raw, list):
            raw = " ".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in raw)
        output_text = format_output(raw)

        print(f"\n{CYAN}StockSensei:{RESET}")
        console.print(Markdown(output_text))


if __name__ == "__main__":
    main()
