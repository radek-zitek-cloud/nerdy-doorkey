"""Build help content for the command pane."""

from __future__ import annotations

from typing import List

from .modes import BrowserMode

def build_help_lines(mode: BrowserMode) -> List[str]:
    """Return formatted help lines for the current mode."""
    if mode == BrowserMode.FILE:
        return [
            "File Mode: ↑↓/jk move | Enter open | Bksp up | Tab pane | : cmd | h help | m mode | q quit",
            "n rename | d del* | c copy | t move | v view | e edit | f newfile | F newdir",
            "*Destructive ops need confirm (y/n)",
        ]
    else:
        return [
            "Git Mode: ↑↓/jk move | Enter open | Bksp up | Tab pane | : cmd | h help | m mode | q quit",
            "a stage | u unstage | r restore* | g diff | l log | b blame | o commit",
            "*Destructive ops need confirm (y/n)",
        ]


__all__ = ["build_help_lines"]
