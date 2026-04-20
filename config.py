import json
import os
from typing import Optional

from rich.prompt import IntPrompt, Prompt

CONFIG_PATH = os.path.expanduser("~/.stocksensei_config.json")

CYAN = "\033[96m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

PROVIDER_PRESETS: dict[str, dict] = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "models": [
            "gpt-5.4",        
            "gpt-5.4-mini",   
            "o3",             
            "o4-mini",        
            "gpt-4o",         
            "gpt-4o-mini"     
        ]
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1",
        "models": [
            "claude-opus-4-7", 
            "claude-opus-4-6",
            "claude-sonnet-4-6", 
            "claude-haiku-4-5-20251001"
        ],
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "models": [
                    "gemini-3.1-pro-preview", 
                    "gemini-3-flash-preview", 
                    "gemini-3.1-flash-lite-preview",
                    "gemini-3-deep-think",
                    "gemini-2.5-pro", 
                    "gemini-2.5-flash"
                ],
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-reasoner"],
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "models": [
            "openai/gpt-4.1-mini", 
            "anthropic/claude-opus-4-7", 
            "google/gemini-2.5-pro", 
            "meta-llama/llama-3.3-70b-instruct"
        ],
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "models": [
            "llama3.2", 
            "qwen2.5", 
            "mistral"
        ],
    },
}

# Maps provider name → langchain model_provider string.
# Providers not listed default to "openai" (OpenAI-compat endpoint).
LANGCHAIN_PROVIDER_MAP: dict[str, str] = {
    "openai": "openai",
    "anthropic": "anthropic",
    "groq": "groq",
    "ollama": "ollama",
}


def get_langchain_provider(provider_name: str) -> str:
    return LANGCHAIN_PROVIDER_MAP.get(provider_name, "openai")


def load_config() -> Optional[dict]:
    if not os.path.exists(CONFIG_PATH):
        return None
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def save_config(config: dict) -> None:
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    try:
        os.chmod(CONFIG_PATH, 0o600)
    except OSError:
        pass


def _validate_api_key(base_url: str, api_key: str) -> bool:
    import openai
    try:
        client = openai.OpenAI(api_key=api_key or "not-needed", base_url=base_url)
        client.models.list()
        return True
    except openai.AuthenticationError:
        return False
    except Exception:
        # Network error or provider doesn't support /models — don't block the user.
        return True


def _pick(prompt: str, options: list[str]) -> int:
    """Display a numbered menu and return the 0-based index of the user's choice."""
    for i, opt in enumerate(options, 1):
        print(f"  {CYAN}{i}.{RESET} {opt}")
    while True:
        choice = IntPrompt.ask(f"{CYAN}{prompt}{RESET}")
        if 1 <= choice <= len(options):
            return choice - 1
        print(f"{RED}Please enter a number between 1 and {len(options)}.{RESET}")


def _add_provider_interactive(config: dict) -> dict:
    preset_names = list(PROVIDER_PRESETS.keys())
    options = [f"{n}  ({PROVIDER_PRESETS[n]['base_url']})" for n in preset_names]
    options.append("Custom  (enter base URL manually)")

    print(f"\n{YELLOW}Select a provider:{RESET}")
    idx = _pick("Your choice", options)

    if idx < len(preset_names):
        provider_name = preset_names[idx]
        base_url = PROVIDER_PRESETS[provider_name]["base_url"]
        models = list(PROVIDER_PRESETS[provider_name]["models"])
    else:
        provider_name = Prompt.ask(f"{CYAN}Provider name{RESET}").strip() or "custom"
        while True:
            base_url = Prompt.ask(f"{CYAN}Base URL (OpenAI-compatible){RESET}").strip()
            if base_url.startswith("http://") or base_url.startswith("https://"):
                break
            print(f"{RED}Base URL must start with http:// or https://{RESET}")
        raw = Prompt.ask(f"{CYAN}Comma-separated model IDs{RESET}").strip()
        models = [m.strip() for m in raw.split(",") if m.strip()]

    while True:
        api_key = Prompt.ask(
            f"{CYAN}API key for {provider_name} (blank if not required){RESET}",
            default="",
        ).strip()
        print(f"{YELLOW}Validating...{RESET}")
        if _validate_api_key(base_url, api_key):
            break
        print(f"{RED}Invalid API key. Try again.{RESET}\n")

    if not models:
        raw = Prompt.ask(f"{CYAN}Comma-separated model IDs{RESET}").strip()
        models = [m.strip() for m in raw.split(",") if m.strip()]

    print(f"\n{YELLOW}Select default model for {provider_name}:{RESET}")
    midx = _pick("Your choice", models)

    config.setdefault("providers", {})
    config["providers"][provider_name] = {
        "base_url": base_url,
        "api_key": api_key,
        "default_model": models[midx],
        "models": models,
    }
    config["default_provider"] = provider_name
    save_config(config)
    print(f"{GREEN}✓ Saved to {CONFIG_PATH}{RESET}")
    return config


def ensure_config() -> dict:
    config = load_config()
    if config:
        return config
    print(f"\n{YELLOW}Welcome to StockSensei!{RESET}")
    print("Let's set up your AI provider.\n")
    return _add_provider_interactive({"providers": {}})


def current_provider_info(config: dict) -> tuple[str, str, str, str, str]:
    """Returns (display_name, model, langchain_provider, base_url, api_key)."""
    name = config["default_provider"]
    provider = config["providers"][name]
    model = provider["default_model"]
    lc_provider = get_langchain_provider(name)
    return name, model, lc_provider, provider["base_url"], provider["api_key"]


def switch_model_interactive(config: dict) -> dict:
    provider_names = list(config.get("providers", {}).keys())
    options = [
        f"{n}  (default: {config['providers'][n]['default_model']})"
        for n in provider_names
    ]
    options.append("+ Add new provider")

    cur_p = config.get("default_provider", "?")
    cur_m = config["providers"].get(cur_p, {}).get("default_model", "?")
    print(f"\n{YELLOW}Current: {cur_p} / {cur_m}{RESET}")
    print(f"{YELLOW}Select provider:{RESET}")
    pidx = _pick("Your choice", options)

    if pidx == len(provider_names):
        return _add_provider_interactive(config)

    provider_name = provider_names[pidx]
    models = config["providers"][provider_name]["models"]

    print(f"\n{YELLOW}Select model:{RESET}")
    midx = _pick("Your choice", models)

    config["default_provider"] = provider_name
    config["providers"][provider_name]["default_model"] = models[midx]
    save_config(config)
    print(f"{GREEN}✓ Switched to {provider_name} / {models[midx]}{RESET}")
    return config
