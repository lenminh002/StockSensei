"""Shared formatting and chart-drawing helpers for block builders and renderers.

All functions are pure (no side-effects, no Rich/console imports) so they can be
imported safely from any layer (core builders, terminal renderers, future web UI).
"""
from __future__ import annotations

import math
from typing import Any


# ---------------------------------------------------------------------------
# Numeric display formatting
# ---------------------------------------------------------------------------

def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def _fmt_price(value: Any) -> str:
    return f"${value:,.2f}" if _is_finite_number(value) else "N/A"


def _fmt_change(value: Any) -> str:
    return f"{value:+.2f}%" if _is_finite_number(value) else "N/A"


def _fmt_pe(value: Any) -> str:
    return f"{value:.2f}" if _is_finite_number(value) else "N/A"


def _fmt_market_cap(value: Any) -> str:
    if not _is_finite_number(value):
        return "N/A"
    return f"${value / 1_000_000_000_000:.2f}T" if value >= 1_000_000_000_000 else f"${value / 1_000_000_000:.2f}B"


def _fmt_compact_number(value: Any) -> str:
    if not _is_finite_number(value):
        return "N/A"
    value = float(value)
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.2f}K"
    return f"{value:,.0f}"


def _fmt_axis_value(value: float, unit: str | None = None) -> str:
    if unit == "price":
        return _fmt_price(value)
    if unit == "market cap":
        return _fmt_market_cap(value)
    if unit == "%":
        return _fmt_change(value)
    return f"{value:,.2f}"


# ---------------------------------------------------------------------------
# ASCII chart drawing primitives
# ---------------------------------------------------------------------------

def _grid_positions(width: int, segments: int = 4) -> list[int]:
    if width <= 1:
        return [0]
    return sorted({round(index * (width - 1) / segments) for index in range(segments + 1)})
