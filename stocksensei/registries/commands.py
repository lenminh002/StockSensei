from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class CommandSpec:
    name: str
    description: str
    handler: Callable | None = None


class CommandRegistry:
    def __init__(self) -> None:
        self._commands: dict[str, CommandSpec] = {}

    def register(self, name: str, description: str, handler: Callable | None = None) -> None:
        if not name.startswith("/"):
            name = f"/{name}"
        if name in self._commands:
            raise ValueError(f"Command already registered: {name}")
        self._commands[name] = CommandSpec(name, description, handler)

    def specs(self) -> dict[str, str]:
        return {name: spec.description for name, spec in self._commands.items()}

    def entries(self) -> list[CommandSpec]:
        return list(self._commands.values())


def create_builtin_command_registry() -> CommandRegistry:
    from stocksensei.ui.terminal.command_prompt import COMMAND_SPECS

    registry = CommandRegistry()
    for name, description in COMMAND_SPECS.items():
        registry.register(name, description)
    if "/extensions" not in registry.specs():
        registry.register("/extensions", "Show extension diagnostics")
    return registry
