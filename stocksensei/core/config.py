import json
import os
from typing import Optional

from stocksensei.core.providers import PROVIDER_PRESETS, get_langchain_provider

CONFIG_DIR = os.path.expanduser("~/.config/stocksensei")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
LEGACY_CONFIG_PATH = os.path.expanduser("~/.stocksensei_config.json")


def load_config() -> Optional[dict]:
    """Load the user's StockSensei configuration from the JSON file."""
    path = CONFIG_PATH if os.path.exists(CONFIG_PATH) else LEGACY_CONFIG_PATH
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def save_config(config: dict) -> None:
    """Save the updated configuration to the JSON file with restricted file permissions."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
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
        except (httpx.RequestError, httpx.TimeoutException, OSError):
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
        except (httpx.RequestError, httpx.TimeoutException, OSError):
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


def ensure_config() -> dict:
    """Ensure a valid configuration exists, triggering the interactive setup if none is found."""
    config = load_config()
    if config:
        return config
    try:
        from stocksensei.ui.terminal.config import ensure_config_interactive
        return ensure_config_interactive()
    except ImportError:
        raise RuntimeError("StockSensei configuration file not found, and interactive setup is unavailable.")


def current_provider_info(config: dict) -> tuple[str, str, str, str, str]:
    """Returns (display_name, model, langchain_provider, base_url, api_key)."""
    name = config["default_provider"]
    provider = config["providers"][name]
    model = provider["default_model"]
    lc_provider = get_langchain_provider(name)
    return name, model, lc_provider, provider["base_url"], provider["api_key"]
