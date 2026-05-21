from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class StockSenseiSession:
    """Core session that owns the LangGraph thread id."""

    id: str = field(default_factory=lambda: f"stocksensei_{uuid4()}")
    thread_id: str | None = None

    def __post_init__(self) -> None:
        if self.thread_id is None:
            self.thread_id = self.id

    @property
    def run_config(self) -> dict:
        return {"configurable": {"thread_id": self.thread_id}}

    def reset(self) -> None:
        self.id = f"stocksensei_{uuid4()}"
        self.thread_id = self.id


def new_session() -> StockSenseiSession:
    return StockSenseiSession()
