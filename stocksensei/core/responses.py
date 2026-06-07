"""AIResponse schema, JSON schema dict, response parsing, and fallback construction.

Depends on: stocksensei.core.block_models
"""
from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from stocksensei.core.block_models import TextBlock, UIBlock, UI_BLOCK_ADAPTER


# ---------------------------------------------------------------------------
# Structured response model
# ---------------------------------------------------------------------------

class AIResponse(BaseModel):
    message: str = ""
    blocks: list[Any] = Field(default_factory=list)


AI_RESPONSE_SCHEMA = {
    "name": "AIResponse",
    "schema": AIResponse.model_json_schema(),
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_JSON_BLOCK_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def _validate_block(block: Any) -> UIBlock | Any:
    if isinstance(block, BaseModel):
        return block
    if isinstance(block, dict):
        try:
            return UI_BLOCK_ADAPTER.validate_python(block)
        except ValidationError:
            return block
    return block


def _normalize_response_dict(data: Any) -> Any:
    if not isinstance(data, dict):
        return data
    blocks = data.get("blocks")
    if isinstance(blocks, list):
        normalized = []
        for block in blocks:
            if isinstance(block, str):
                try:
                    block = json.loads(block)
                except json.JSONDecodeError:
                    pass
            normalized.append(_validate_block(block))
        data = {**data, "blocks": normalized}
    return data


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def make_json_fallback_response(raw_text: str, error: str | None = None) -> AIResponse:
    """Build a safe AIResponse from unstructured text (used when parsing fails)."""
    message = "I could not produce a fully structured response, so here is a safe fallback."
    if error:
        message += f" ({error})"
    text = raw_text.strip() or "No response available."
    return AIResponse(message=message, blocks=[TextBlock(type="text", title="Fallback", content=text)])


def parse_ai_response(raw: Any) -> AIResponse:
    """Parse model output into a validated AIResponse.

    Accepts: AIResponse, BaseModel, dict, JSON string, or markdown-fenced JSON.
    Falls back to a text block containing the raw content on failure.
    """
    if isinstance(raw, AIResponse):
        return raw
    if isinstance(raw, BaseModel):
        return AIResponse.model_validate(_normalize_response_dict(raw.model_dump()))
    if isinstance(raw, dict):
        return AIResponse.model_validate(_normalize_response_dict(raw))
    if isinstance(raw, str):
        stripped = raw.strip()
        candidates = [stripped]
        match = _JSON_BLOCK_RE.search(stripped)
        if match:
            candidates.insert(0, match.group(1))
        for candidate in candidates:
            try:
                return AIResponse.model_validate(_normalize_response_dict(json.loads(candidate)))
            except (json.JSONDecodeError, ValidationError):
                continue
        return make_json_fallback_response(stripped)
    return make_json_fallback_response(str(raw))
