"""Build help content for the command pane."""

from __future__ import annotations

from typing import List

from nedok.modes import BrowserMode

def build_help_lines(mode: BrowserMode) -> List[str]:
    """Return formatted help lines for all modes (all commands available)."""
    lines = [
        f"{mode.label}: ↑↓/jk move | Tab pane | Enter open | Bksp up | s refresh | S ssh | x disconnect | m mode | h help | q quit",
        "File: n rename | d del* | c copy | t move | v view | e edit | f file | F dir | : cmd",
        "Git: a stage | u unstage | r restore* | g diff | l log | b blame | o commit | *confirm needed",
    ]
    if mode is BrowserMode.TREE:
        lines.append("Tree: + expand | - collapse parent | shows recursive left pane tree")
    return lines


__all__ = ["build_help_lines"]
