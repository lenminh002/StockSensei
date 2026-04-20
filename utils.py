import re
from rich.prompt import IntPrompt

CYAN = "\033[96m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def pick_option(prompt: str, options: list[str]) -> int:
    """Display a numbered menu and return the 0-based index of the user's choice."""
    for i, opt in enumerate(options, 1):
        print(f"  {CYAN}{i}.{RESET} {opt}")
    while True:
        choice = IntPrompt.ask(f"{CYAN}{prompt}{RESET}")
        if 1 <= choice <= len(options):
            return choice - 1
        print(f"{RED}Please enter a number between 1 and {len(options)}.{RESET}")

def format_output(text: str) -> str:
    """Clean up agent prefixes and map internal color tags to terminal ANSI sequence codes."""
    text = re.sub(r'^(?:Final Answer|Thought|Action|Observation):\s*', '', text, flags=re.IGNORECASE).strip()
    color_map = {
        "<BLUE>": "\033[94m", "<YELLOW>": "\033[93m",
        "<GREEN>": "\033[92m", "<RED>": "\033[91m",
        "<RESET>": "\033[0m",
    }
    for tag, code in color_map.items():
        text = text.replace(tag, code)
    return text
