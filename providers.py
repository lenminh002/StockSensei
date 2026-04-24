"""
Configuration for AI providers and their models.
"""

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

# Maps provider name → langchain model_provider string.
# Providers not listed default to "openai" (OpenAI-compat endpoint).
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
