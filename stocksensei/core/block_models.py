"""Pydantic Visual Block schemas, discriminated union, type adapter, and low-level cell/sparkline helpers.

This module has NO imports from other stocksensei modules — it is the base layer.
"""
from __future__ import annotations

import math
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, TypeAdapter, field_validator


# ---------------------------------------------------------------------------
# Low-level cell / sparkline helpers (depended on by builders)
# ---------------------------------------------------------------------------

def _stringify_cell(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))
# ---------------------------------------------------------------------------
# Block models
# ---------------------------------------------------------------------------

class TextBlock(BaseModel):
    type: Literal["text"]
    title: str | None = None
    content: str


class MetricItem(BaseModel):
    label: str
    value: str
    tone: str | None = None


class MetricCardBlock(BaseModel):
    type: Literal["metric_card"]
    title: str
    subtitle: str | None = None
    items: list[MetricItem]
    footer: str | None = None


class TableBlock(BaseModel):
    type: Literal["table"]
    title: str | None = None
    columns: list[str]
    rows: list[list[str]]

    @field_validator("rows")
    @classmethod
    def _validate_rows(cls, rows: list[list[str]], info):
        columns = info.data.get("columns") or []
        width = len(columns)
        if width and any(len(row) != width for row in rows):
            raise ValueError("Each table row must match number of columns.")
        return rows


class LineChartPoint(BaseModel):
    date: str
    value: float


class LineChartSeries(BaseModel):
    label: str
    points: list[LineChartPoint]
    color: str | None = None


class LineChartBlock(BaseModel):
    type: Literal["line_chart"]
    title: str | None = None
    ticker: str | None = None
    period: str | None = None
    label: str | None = None
    points: list[LineChartPoint] = Field(default_factory=list)
    series: list[LineChartSeries] = Field(default_factory=list)
    unit: str | None = None
    summary: str | None = None


class BarChartItem(BaseModel):
    label: str
    value: float
    display_value: str
    color: str | None = None


class BarChartBlock(BaseModel):
    type: Literal["barchart"]
    title: str | None = None
    items: list[BarChartItem]
    unit: str | None = None
    summary: str | None = None


class CandlestickPoint(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float


class CandlestickChartBlock(BaseModel):
    type: Literal["candlestick_chart"]
    title: str | None = None
    ticker: str | None = None
    period: str | None = None
    points: list[CandlestickPoint]
    summary: str | None = None


class RangeBarBlock(BaseModel):
    type: Literal["range_bar"]
    title: str
    minimum_label: str
    maximum_label: str
    current_label: str
    position: float = Field(ge=0.0, le=1.0)
    summary: str | None = None


class NewsBlock(BaseModel):
    type: Literal["news"]
    title: str | None = None
    ticker: str | None = None
    headlines: list[str]


# ---------------------------------------------------------------------------
# Discriminated union and type adapter
# ---------------------------------------------------------------------------

UIBlock = Annotated[
    TextBlock
    | MetricCardBlock
    | TableBlock
    | LineChartBlock
    | BarChartBlock
    | CandlestickChartBlock
    | RangeBarBlock
    | NewsBlock,
    Field(discriminator="type"),
]
UI_BLOCK_ADAPTER = TypeAdapter(UIBlock)


class RenderToolPayload(BaseModel):
    block: UIBlock
