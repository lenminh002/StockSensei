import os
from dotenv import load_dotenv, find_dotenv
from agent import get_agent

CYAN = "\033[96m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

import re

from rich.console import Console
from rich.markdown import Markdown

console = Console()

def format_output(text: str) -> str:
    # 1. Strip LangChain metadata
    text = re.sub(r'^(?:Final Answer|Thought|Action|Observation):\s*', '', text, flags=re.IGNORECASE).strip()

    # 2. Convert <TAG> style color tags to ANSI escape codes
    color_map = {
        "<BLUE>": "\033[94m", "<YELLOW>": "\033[93m",
        "<GREEN>": "\033[92m", "<RED>": "\033[91m",
        "<RESET>": "\033[0m",
    }
    for tag, code in color_map.items():
        text = text.replace(tag, code)

    return text


def main():
    # Try finding an API key (local first, then global)
    load_dotenv(find_dotenv(usecwd=True))
    global_env_path = os.path.expanduser("~/.stocksensei_env")
    if os.path.exists(global_env_path):
        load_dotenv(global_env_path)
        
    # If there's still no key, interactively ask for one and validate it!
    if not os.getenv("OPENAI_API_KEY"):
        import openai
        print(f"\n{YELLOW}Welcome to StockSensei!{RESET}")
        print("It looks like you haven't set an OpenAI API Key yet.")
        
        api_key = ""
        while True:
            api_key = input(f"{CYAN}Please enter your API Key to save it globally: {RESET}").strip()
            
            if not api_key:
                print(f"{RED}An API key is required to use StockSensei. Exiting...{RESET}")
                return
                
            print(f"{YELLOW}Validating key with OpenAI...{RESET}")
            try:
                # Try to initialize the client and list models to validate the key
                client = openai.OpenAI(api_key=api_key)
                client.models.list()
                break
            except openai.AuthenticationError:
                print(f"{RED}✗ Invalid API Key! Please double-check and try again.{RESET}\n")
            except Exception as e:
                print(f"{RED}✗ Network error or OpenAI is down. Please check your connection and try again.{RESET}\n")
                return
            
        with open(global_env_path, "w") as f:
            f.write(f"OPENAI_API_KEY={api_key}\n")
        
        os.environ["OPENAI_API_KEY"] = api_key
        print(f"{GREEN}✓ Key securely saved to {global_env_path}{RESET}\n")
        print("-" * 50)

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
        
        print(f"\n{CYAN}StockSensei:{RESET}")
        console.print(Markdown(output_text))

if __name__ == "__main__":
    main()