import json
import os
from typing import Optional

from rich.prompt import Prompt

from utils import CYAN, GREEN, RED, RESET, YELLOW, pick_option

CONFIG_PATH = os.path.expanduser("~/.stocksensei_config.json")

from providers import PROVIDER_PRESETS, get_langchain_provider


def load_config() -> Optional[dict]:
    """Load the user's StockSensei configuration from the JSON file."""
    if not os.path.exists(CONFIG_PATH):
        return None
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def save_config(config: dict) -> None:
    """Save the updated configuration to the JSON file with restricted file permissions."""
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    try:
        os.chmod(CONFIG_PATH, 0o600)
    except OSError:
        pass


def _validate_api_key(provider_name: str, base_url: str, api_key: str) -> bool:
    """Check if the provided API key is valid for the given provider."""
    is_local = provider_name == "ollama" or "localhost" in base_url or "127.0.0.1" in base_url

    if not api_key:
        return is_local

    if provider_name == "anthropic":
        import httpx
        try:
            r = httpx.get(
                "https://api.anthropic.com/v1/models",
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
                timeout=10,
            )
            if r.status_code in (401, 403):
                return False
            return r.status_code < 500
        except (httpx.NetworkError, httpx.TimeoutException, OSError):
            return True

    if provider_name == "gemini":
        import httpx
        try:
            r = httpx.get(
                f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
                timeout=10,
            )
            if r.status_code in (400, 401, 403):
                return False
            return True
        except (httpx.NetworkError, httpx.TimeoutException, OSError):
            return True

    import openai
    try:
        client = openai.OpenAI(api_key=api_key, base_url=base_url)
        client.models.list()
        return True
    except (openai.AuthenticationError, openai.PermissionDeniedError):
        return False
    except (openai.APIConnectionError, openai.APITimeoutError):
        return True
    except openai.APIStatusError as e:
        if e.status_code in (401, 403):
            return False
        return True
    except Exception:
        return False


def _add_provider_interactive(config: dict) -> dict:
    """Interactively walk the user through adding a new AI provider or a custom one."""
    preset_names = list(PROVIDER_PRESETS.keys())
    options = [f"{n}  ({PROVIDER_PRESETS[n]['base_url']})" for n in preset_names]
    options.append("Custom  (enter base URL manually)")

    print(f"\n{YELLOW}Select a provider:{RESET}")
    idx = pick_option("Your choice", options)

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
        if _validate_api_key(provider_name, base_url, api_key):
            break
        print(f"{RED}Invalid API key. Try again.{RESET}\n")

    if not models:
        raw = Prompt.ask(f"{CYAN}Comma-separated model IDs{RESET}").strip()
        models = [m.strip() for m in raw.split(",") if m.strip()]

    print(f"\n{YELLOW}Select default model for {provider_name}:{RESET}")
    midx = pick_option("Your choice", models)

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
    """Ensure a valid configuration exists, triggering the interactive setup if none is found."""
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
    """Interactively allow the user to switch the active provider and model."""
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
    pidx = pick_option("Your choice", options)

    if pidx == len(provider_names):
        return _add_provider_interactive(config)

    provider_name = provider_names[pidx]
    models = config["providers"][provider_name]["models"]

    print(f"\n{YELLOW}Select model:{RESET}")
    midx = pick_option("Your choice", models)

    config["default_provider"] = provider_name
    config["providers"][provider_name]["default_model"] = models[midx]
    save_config(config)
    print(f"{GREEN}✓ Switched to {provider_name} / {models[midx]}{RESET}")
    return config
