from __future__ import annotations

import atexit
import asyncio

_loop: asyncio.AbstractEventLoop | None = None


def _get_loop() -> asyncio.AbstractEventLoop:
    """Return a process-lifetime event loop so async HTTP pools stay bound to a live loop.

    Why: providers like google-genai/httpx pool connections whose transports are bound
    to whichever loop opened them. Per-prompt asyncio.run() closes that loop, and the
    next prompt explodes inside the pool's stale-connection cleanup with
    'RuntimeError: Event loop is closed'.
    """
    global _loop
    if _loop is None or _loop.is_closed():
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
    return _loop


def _close_loop() -> None:
    global _loop
    if _loop is None:
        return
    try:
        asyncio.set_event_loop(None)
        if not _loop.is_closed() and not _loop.is_running():
            _loop.close()
    except RuntimeError:
        pass
    finally:
        _loop = None


atexit.register(_close_loop)

from rich.console import Console
from rich.live import Live
from rich.text import Text

from stocksensei.core.events import BlockEvent, ErrorEvent, FinalEvent, StatusEvent, ToolEndEvent, ToolStartEvent
from stocksensei.core.responses import AIResponse, make_json_fallback_response
from stocksensei.ui.terminal.renderers import render_block as render_terminal_block


def run_service(service, user_input: str, session, console: Console) -> AIResponse:
    """Consume the core event stream and render terminal progress/blocks."""
    async def _consume(live: Live) -> AIResponse:
        response: AIResponse | None = None
        async for event in service.ask_events(user_input, session):
            if isinstance(event, StatusEvent):
                live.update(Text(f"StockSensei {event.message}...", style="dim cyan"))
            elif isinstance(event, ToolStartEvent):
                live.update(Text(f"StockSensei {event.message or event.name}...", style="dim cyan"))
            elif isinstance(event, ToolEndEvent):
                live.update(Text(f"StockSensei {event.message or event.name}...", style="dim cyan"))
            elif isinstance(event, BlockEvent):
                live.console.print()
                render_terminal_block(live.console, event.block)
                await asyncio.sleep(0.18)
            elif isinstance(event, ErrorEvent) and event.response is not None:
                response = event.response
            elif isinstance(event, FinalEvent):
                response = event.response
        return response or make_json_fallback_response("No response available from the agent.")

    with Live(Text("StockSensei thinking.", style="dim cyan"), console=console, refresh_per_second=12, transient=True) as live:
        return _get_loop().run_until_complete(_consume(live))
