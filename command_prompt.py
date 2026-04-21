from __future__ import annotations

import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import FuzzyCompleter, WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts.prompt import CompleteStyle
from prompt_toolkit.styles import Style

COMMAND_SPECS = {
    "/help": "Show command help",
    "/models": "Switch AI provider or model",
    "/quit": "Exit StockSensei",
}

PROMPT_STYLE = Style.from_dict(
    {
        "completion-menu": "bg:#1f2335 #e6e6e6",
        "completion-menu.completion": "bg:#1f2335 #e6e6e6",
        "completion-menu.completion.current": "bg:#7aa2f7 #111111",
        "completion-menu.meta.completion": "bg:#1f2335 #9aa5ce",
        "completion-menu.meta.completion.current": "bg:#7aa2f7 #111111",
        "scrollbar.background": "bg:#2a2f45",
        "scrollbar.button": "bg:#7aa2f7",
    }
)


class CommandPrompt:
    """Interactive prompt wrapper with cleaner slash-command completion for TTY sessions."""

    def __init__(self) -> None:
        self._interactive = sys.stdin.isatty() and sys.stdout.isatty()
        if self._interactive:
            completer = WordCompleter(
                list(COMMAND_SPECS.keys()),
                ignore_case=True,
                sentence=True,
                meta_dict=COMMAND_SPECS,
            )
            self._session = PromptSession(history=InMemoryHistory(), style=PROMPT_STYLE)
            self._completer = FuzzyCompleter(completer)
        else:
            self._session = None
            self._completer = None

    def prompt(self, prompt_text: str = "You: ") -> str:
        if not self._interactive:
            return input(prompt_text)
        return self._session.prompt(
            prompt_text,
            completer=self._completer,
            complete_while_typing=True,
            complete_in_thread=True,
            complete_style=CompleteStyle.COLUMN,
            reserve_space_for_menu=10,
            bottom_toolbar=HTML("<b>/</b> commands available · <b>Tab</b> autocomplete · <b>/quit</b> exit"),
        )
