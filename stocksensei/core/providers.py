from __future__ import annotations

from config import (
    CONFIG_PATH,
    LEGACY_CONFIG_PATH,
    current_provider_info,
    ensure_config,
    load_config,
    save_config,
    switch_model_interactive,
)


class ProviderService:
    """Core owner for provider/model configuration."""

    def __init__(self, config: dict | None = None) -> None:
        self.config = config or ensure_config()

    def current_info(self) -> tuple[str, str, str, str, str]:
        return current_provider_info(self.config)

    def switch_interactive(self) -> dict:
        self.config = switch_model_interactive(self.config)
        return self.config

    def save(self) -> None:
        save_config(self.config)


__all__ = [
    "ProviderService",
    "CONFIG_PATH",
    "LEGACY_CONFIG_PATH",
    "load_config",
    "save_config",
]
