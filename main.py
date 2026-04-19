from agent import get_agent

CYAN = "\033[96m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"

import re

def format_output(text: str) -> str:
    # 1. Strip LangChain metadata
    text = re.sub(r'^(?:Final Answer|Thought|Action|Observation):\s*', '', text, flags=re.IGNORECASE).strip()

    # 2. Convert custom tags to ANSI
    color_map = {
        "{BLUE}": "\033[94m", "{YELLOW}": "\033[93m",
        "{GREEN}": "\033[92m", "{RED}": "\033[91m",
        "{RESET}": "\033[0m", # ... include others
    }
    
    for tag, code in color_map.items():
        text = text.replace(tag, code)
        
    return text


def main():
    agent = get_agent()
    config = {"configurable": {"thread_id": "stocksensei_chat_v1"}}

    print(f"\n{GREEN}Hello, I'm StockSensei! {RESET}")
    print(f"{CYAN}Ask me anything about stocks. Type 'exit', 'quit', or 'q' to quit.{RESET}\n")

    while True:
        user_input = input(f"{YELLOW}You: {RESET}").strip()
        
        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit", "q"]:
            print(f"\n{GREEN}Goodbye! Happy investing! {RESET}\n")
            break
        
        response = agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]}, 
            config=config
        )
        output_text = format_output(response['messages'][-1].content)
        
        print(f"\n{CYAN}StockSensei:{RESET} {output_text}\n")

if __name__ == "__main__":
    main()