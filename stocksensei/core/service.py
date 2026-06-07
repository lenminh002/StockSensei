from __future__ import annotations

import json
import random
import traceback
from collections.abc import AsyncIterator
from typing import Any

from stocksensei.core.agent import get_agent
from stocksensei.core.config import current_provider_info, ensure_config
from stocksensei.core.responses import AIResponse, make_json_fallback_response, parse_ai_response
from utils import stringify_message_content

from stocksensei.core.events import BlockEvent, ErrorEvent, FinalEvent, StatusEvent, ToolEndEvent, ToolStartEvent, StockSenseiEvent
from stocksensei.core.session import StockSenseiSession, new_session
from stocksensei.extensions.manager import ExtensionManager
from stocksensei.registries.blocks import BlockRegistry, create_builtin_block_registry
from stocksensei.registries.commands import CommandRegistry, create_builtin_command_registry
from stocksensei.registries.tools import ToolRegistry, create_builtin_tool_registry


# ---------------------------------------------------------------------------
# Status animation labels — shown while the agent is working
# ---------------------------------------------------------------------------

STATUS_LABELS = [
    "cooking",
    "drawing",
    "mewing",
    "brewing",
    "thinking",
    "plotting",
    "scheming",
    "vibing",
    "whisking",
    "forging",
    "mixing",
    "stirring",
]

# ---------------------------------------------------------------------------
# Tool-specific status messages — shown during individual tool calls
# ---------------------------------------------------------------------------

TOOL_MESSAGES = {
    "get_price": ("Fetching live price", "Fetched live price"),
    "get_stock_summary": ("Pulling stock summary", "Stock summary ready"),
    "get_company_summary": ("Reading company profile", "Company profile ready"),
    "get_historical_data": ("Loading price history", "Price history ready"),
    "get_news": ("Scanning latest headlines", "Headlines ready"),
    "compare_stocks": ("Comparing live quotes", "Quote comparison ready"),
    "compare_stocks_summary": ("Comparing valuation data", "Valuation comparison ready"),
    "build_snapshot_card_visual": ("Building snapshot card", "Snapshot card ready"),
    "build_52w_range_visual": ("Building 52-week range", "52-week range ready"),
    "build_price_comparison_visual": ("Building comparison table", "Comparison table ready"),
    "build_summary_comparison_visual": ("Building company summary table", "Company summary table ready"),
    "build_time_comparison_line_visual": ("Drawing comparison line chart", "Comparison line chart ready"),
    "build_price_chart_visual": ("Drawing price columns", "Price columns ready"),
    "build_change_chart_visual": ("Drawing daily change columns", "Daily change columns ready"),
    "build_market_cap_chart_visual": ("Drawing market-cap columns", "Market-cap columns ready"),
    "build_history_chart_visual": ("Drawing trend view", "Trend view ready"),
    "build_line_chart_visual": ("Drawing line chart", "Line chart ready"),
    "build_volume_chart_visual": ("Drawing volume columns", "Volume columns ready"),
    "build_news_visual": ("Formatting news list", "News list ready"),
}


def _tool_message(name: str, phase: str) -> str:
    """Return the appropriate status label for a tool call start or end."""
    start, end = TOOL_MESSAGES.get(name, (f"Running {name}", f"Finished {name}"))
    return start if phase == "start" else end


def _extract_response_from_state(state: dict) -> AIResponse:
    """Pull the AI response out of the agent's final state dict."""
    structured = state.get("structured_response")
    if structured:
        return parse_ai_response(structured)

    messages = state.get("messages") or []
    if messages:
        content = stringify_message_content(messages[-1].content)
        return parse_ai_response(content)

    return make_json_fallback_response("No response available from the agent.")


def _classify_api_error(exc: Exception) -> tuple[AIResponse | None, bool]:
    """Return (clean_response, log_traceback) for well-known API errors."""
    msg = str(exc)
    if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower() or "rate limit" in msg.lower():
        return AIResponse(
            message="Rate limit reached — please wait a moment and try again.",
            blocks=[],
        ), False
    if "401" in msg or "403" in msg or "API_KEY_INVALID" in msg or "UNAUTHENTICATED" in msg:
        return AIResponse(
            message="Authentication failed. Check your API key with /models.",
            blocks=[],
        ), False
    if "503" in msg or "UNAVAILABLE" in msg:
        return AIResponse(
            message="The AI provider is temporarily unavailable. Try again shortly.",
            blocks=[],
        ), False
    return None, True


def block_key(block: dict) -> str:
    return json.dumps(block, sort_keys=True)


class StockSenseiService:
    """UI-agnostic StockSensei Core service."""

    def __init__(
        self,
        *,
        config: dict | None = None,
        tool_registry: ToolRegistry | None = None,
        block_registry: BlockRegistry | None = None,
        command_registry: CommandRegistry | None = None,
    ) -> None:
        self.config = config or ensure_config()
        self.tool_registry = tool_registry or create_builtin_tool_registry()
        self.block_registry = block_registry or create_builtin_block_registry()
        self.command_registry = command_registry or create_builtin_command_registry()
        self.extensions = ExtensionManager(config=self.config, tool_registry=self.tool_registry, block_registry=self.block_registry)
        self.extensions.load_all()
        self.extensions.run_hook_sync("on_startup", service=self)
        self.agent, self.label = self._build_agent()

    def _build_agent(self):
        name, model, lc_provider, base_url, api_key = current_provider_info(self.config)
        return get_agent(model, lc_provider, api_key, base_url, tools=self.tool_registry.tools()), f"{name} / {model}"

    def new_session(self) -> StockSenseiSession:
        return new_session()

    def rebuild_agent(self, config: dict | None = None) -> str:
        if config is not None:
            self.config = config
        self.agent, self.label = self._build_agent()
        return self.label

    async def ask_events(self, user_input: str, session: StockSenseiSession) -> AsyncIterator[StockSenseiEvent]:
        for result in await self.extensions.run_hook("before_agent_run", user_input=user_input, session=session, service=self):
            if isinstance(result, dict) and result.get("block"):
                response = result.get("response") or make_json_fallback_response(result.get("reason") or "Blocked by extension.")
                yield FinalEvent(session_id=session.id, response=response)
                return
        payload = {"messages": [{"role": "user", "content": user_input}]}
        final_state: dict | None = None
        rendered_blocks: set[str] = set()
        yield StatusEvent(session_id=session.id, message=random.choice(STATUS_LABELS))
        try:
            async for event in self.agent.astream_events(payload, config=session.run_config, version="v2"):
                event_name = event.get("event")
                name = event.get("name") or "tool"
                data = event.get("data") or {}

                if event_name == "on_tool_start":
                    yield ToolStartEvent(session_id=session.id, name=name, message=_tool_message(name, "start"), input=data.get("input"))
                elif event_name == "on_tool_end":
                    output = data.get("output")
                    yield ToolEndEvent(session_id=session.id, name=name, message=_tool_message(name, "end"), output=output)
                    if isinstance(output, dict) and isinstance(output.get("block"), dict):
                        block = output["block"]
                        key = block_key(block)
                        if key not in rendered_blocks:
                            rendered_blocks.add(key)
                            yield BlockEvent(session_id=session.id, block=block)
                elif event_name == "on_chain_end":
                    output = data.get("output")
                    if isinstance(output, dict) and ("structured_response" in output or "messages" in output):
                        final_state = output

            if final_state is None:
                raise RuntimeError("Agent stream completed without final state.")
            response = _extract_response_from_state(final_state)
            response.blocks = [
                block for block in response.blocks
                if block_key(block if isinstance(block, dict) else block.model_dump()) not in rendered_blocks
            ]
            for result in await self.extensions.run_hook("after_agent_run", response=response, session=session, service=self):
                if result is not None:
                    response = result
            yield FinalEvent(session_id=session.id, response=response, rendered_block_keys=sorted(rendered_blocks))
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            clean_response, log_tb = _classify_api_error(exc)
            if log_tb:
                traceback.print_exc()
            response = clean_response or make_json_fallback_response(
                f"The agent failed while producing a structured response.\n\nError ({type(exc).__name__}): {exc}",
                error="structured-output fallback",
            )
            yield ErrorEvent(session_id=session.id, message=str(exc), error_type=type(exc).__name__, response=response)
            yield FinalEvent(session_id=session.id, response=response)

    async def shutdown(self) -> None:
        await self.extensions.run_hook("on_shutdown", service=self)

    async def ask(self, user_input: str, session: StockSenseiSession) -> AIResponse:
        final: AIResponse | None = None
        async for event in self.ask_events(user_input, session):
            if event.type == "final":
                final = event.response
        return final or make_json_fallback_response("No response available from the agent.")
