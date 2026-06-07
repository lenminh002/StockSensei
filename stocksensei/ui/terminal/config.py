from utils import CYAN, GREEN, RED, RESET, YELLOW, ask_text, pick_option
from stocksensei.core.providers import PROVIDER_PRESETS
from stocksensei.core.config import save_config, CONFIG_PATH, _validate_api_key


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
        provider_name = ask_text(f"{CYAN}Provider name{RESET}").strip() or "custom"
        while True:
            base_url = ask_text(f"{CYAN}Base URL (OpenAI-compatible){RESET}").strip()
            if base_url.startswith("http://") or base_url.startswith("https://"):
                break
            print(f"{RED}Base URL must start with http:// or https://{RESET}")
        raw = ask_text(f"{CYAN}Comma-separated model IDs{RESET}").strip()
        models = [m.strip() for m in raw.split(",") if m.strip()]

    while True:
        api_key = ask_text(
            f"{CYAN}API key for {provider_name} (blank if not required){RESET}",
            default="",
        ).strip()
        print(f"{YELLOW}Validating...{RESET}")
        if _validate_api_key(provider_name, base_url, api_key):
            break
        print(f"{RED}Invalid API key. Try again.{RESET}\n")

    if not models:
        raw = ask_text(f"{CYAN}Comma-separated model IDs{RESET}").strip()
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


def ensure_config_interactive() -> dict:
    """Trigger the interactive setup for a terminal environment."""
    print(f"\n{YELLOW}Welcome to StockSensei!{RESET}")
    print("Let's set up your AI provider.\n")
    return _add_provider_interactive({"providers": {}})


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
