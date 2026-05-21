from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel


@dataclass(frozen=True)
class RegisteredBlock:
    type: str
    model: type[BaseModel]
    fallback_field: str | None = None
    extension_id: str | None = None


class BlockRegistry:
    """Registry of Visual Block schemas and fallback metadata."""

    def __init__(self) -> None:
        self._blocks: dict[str, RegisteredBlock] = {}

    def register(
        self,
        block_type: str,
        model: type[BaseModel],
        *,
        fallback_field: str | None = None,
        extension_id: str | None = None,
    ) -> str:
        final_type = block_type
        if extension_id and "/" not in final_type:
            final_type = f"{extension_id}/{block_type}"
        if final_type in self._blocks:
            raise ValueError(f"Visual Block already registered: {final_type}")
        self._blocks[final_type] = RegisteredBlock(final_type, model, fallback_field, extension_id)
        return final_type

    def validate(self, block: dict[str, Any]) -> BaseModel | dict[str, Any]:
        block_type = block.get("type")
        entry = self._blocks.get(block_type)
        if not entry:
            return block
        return entry.model.model_validate(block)

    def entries(self) -> list[RegisteredBlock]:
        return list(self._blocks.values())


def create_builtin_block_registry() -> BlockRegistry:
    from ui_blocks import BarChartBlock, MetricCardBlock, NewsBlock, RangeBarBlock, SparklineBlock, TableBlock, TextBlock

    registry = BlockRegistry()
    for block_type, model in [
        ("text", TextBlock),
        ("metric_card", MetricCardBlock),
        ("table", TableBlock),
        ("sparkline", SparklineBlock),
        ("barchart", BarChartBlock),
        ("range_bar", RangeBarBlock),
        ("news", NewsBlock),
    ]:
        registry.register(block_type, model)
    return registry
