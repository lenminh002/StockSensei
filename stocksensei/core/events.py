from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class CoreEvent(BaseModel):
    """Base event emitted by StockSensei Core."""

    type: str
    session_id: str


class StatusEvent(CoreEvent):
    type: Literal["status"] = "status"
    message: str


class ToolStartEvent(CoreEvent):
    type: Literal["tool_start"] = "tool_start"
    name: str
    message: str | None = None
    input: Any = None


class ToolEndEvent(CoreEvent):
    type: Literal["tool_end"] = "tool_end"
    name: str
    message: str | None = None
    output: Any = None


class BlockEvent(CoreEvent):
    type: Literal["block"] = "block"
    block: dict[str, Any]


class FinalEvent(CoreEvent):
    type: Literal["final"] = "final"
    response: Any
    rendered_block_keys: list[str] = Field(default_factory=list)


class ErrorEvent(CoreEvent):
    type: Literal["error"] = "error"
    message: str
    error_type: str | None = None
    response: Any = None


StockSenseiEvent = StatusEvent | ToolStartEvent | ToolEndEvent | BlockEvent | FinalEvent | ErrorEvent
