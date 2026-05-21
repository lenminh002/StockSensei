from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

SUPPORTED_API_MAJOR = "0"


@dataclass
class HookResult:
    block: bool = False
    response: Any = None


Hook = Callable[..., Any | Awaitable[Any]]


@dataclass
class ExtensionAPI:
    id: str
    api_version: str
    tool_registry: Any
    block_registry: Any
    hooks: dict[str, list[Hook]] = field(default_factory=lambda: {
        "on_startup": [],
        "before_agent_run": [],
        "after_agent_run": [],
        "on_shutdown": [],
    })

    def register_tool(self, tool: Any, *, name: str | None = None) -> str:
        return self.tool_registry.register(tool, name=name, extension_id=self.id)

    def register_block(
        self,
        block_type: str,
        model: type[BaseModel],
        *,
        fallback_field: str | None = None,
    ) -> str:
        return self.block_registry.register(block_type, model, fallback_field=fallback_field, extension_id=self.id)

    def on(self, hook_name: str, handler: Hook) -> None:
        if hook_name not in self.hooks:
            raise ValueError(f"Unsupported hook: {hook_name}")
        self.hooks[hook_name].append(handler)


def assert_api_compatible(api_version: str) -> None:
    major = api_version.split(".", 1)[0]
    if major != SUPPORTED_API_MAJOR:
        raise ValueError(f"Unsupported extension API version: {api_version}")
