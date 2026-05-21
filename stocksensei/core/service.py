from __future__ import annotations

import asyncio
import json
import random
import traceback
from collections.abc import AsyncIterator
from typing import Any

from agent import get_agent
from config import current_provider_info, ensure_config
from runner import STATUS_LABELS, _classify_api_error, _extract_response_from_state, _tool_message
from ui_blocks import AIResponse, make_json_fallback_response
from utils import stringify_message_content

from stocksensei.core.events import BlockEvent, ErrorEvent, FinalEvent, StatusEvent, ToolEndEvent, ToolStartEvent, StockSenseiEvent
from stocksensei.core.session import StockSenseiSession, new_session
from stocksensei.extensions.manager import ExtensionManager
from stocksensei.registries.blocks import BlockRegistry, create_builtin_block_registry
from stocksensei.registries.commands import CommandRegistry, create_builtin_command_registry
from stocksensei.registries.tools import ToolRegistry, create_builtin_tool_registry


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
