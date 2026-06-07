from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class RegisteredTool:
    name: str
    tool: Any
    extension_id: str | None = None


class ToolRegistry:
    """Registry for built-in and extension-provided LangChain tools."""

    def __init__(self) -> None:
        self._tools: dict[str, RegisteredTool] = {}

    def register(self, tool: Any, *, name: str | None = None, extension_id: str | None = None) -> str:
        raw_name = name or getattr(tool, "name", None) or getattr(tool, "__name__", None)
        if not raw_name:
            raise ValueError("Tool must have a name.")
        final_name = raw_name
        if final_name in self._tools:
            if extension_id:
                final_name = f"{extension_id}.{raw_name}"
            if final_name in self._tools:
                raise ValueError(f"Tool already registered: {final_name}")
        if final_name != raw_name and hasattr(tool, "name"):
            try:
                tool.name = final_name
            except Exception:
                pass
        self._tools[final_name] = RegisteredTool(name=final_name, tool=tool, extension_id=extension_id)
        return final_name

    def register_many(self, tools: Iterable[Any], *, extension_id: str | None = None) -> list[str]:
        return [self.register(tool, extension_id=extension_id) for tool in tools]

    def tools(self) -> list[Any]:
        return [item.tool for item in self._tools.values()]

    def entries(self) -> list[RegisteredTool]:
        return list(self._tools.values())


def create_builtin_tool_registry() -> ToolRegistry:
    from stocksensei.core.agent import TOOLS

    registry = ToolRegistry()
    registry.register_many(TOOLS)
    return registry
