from __future__ import annotations

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
            "gemini-2.5-flash",
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

LANGCHAIN_PROVIDER_MAP: dict[str, str] = {
    "openai": "openai",
    "anthropic": "anthropic",
    "gemini": "google_genai",
    "groq": "groq",
    "ollama": "ollama",
}


def get_langchain_provider(provider_name: str) -> str:
    """Map a generic provider name to its corresponding LangChain provider identifier."""
    return LANGCHAIN_PROVIDER_MAP.get(provider_name, "openai")


class ProviderService:
    """Core owner for provider/model configuration."""

    def __init__(self, config: dict | None = None) -> None:
        from stocksensei.core.config import ensure_config
        self.config = config or ensure_config()

    def current_info(self) -> tuple[str, str, str, str, str]:
        from stocksensei.core.config import current_provider_info
        return current_provider_info(self.config)

    def switch_interactive(self) -> dict:
        from stocksensei.ui.terminal.config import switch_model_interactive
        self.config = switch_model_interactive(self.config)
        return self.config

    def save(self) -> None:
        from stocksensei.core.config import save_config
        save_config(self.config)
