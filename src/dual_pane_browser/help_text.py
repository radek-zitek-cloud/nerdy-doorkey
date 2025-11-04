"""Build help content for the command pane."""

from __future__ import annotations

from typing import List

from .modes import BrowserMode

GENERAL_COMMANDS = [
    ("Arrow keys", "Navigate entries"),
    ("Enter", "Open highlighted directory"),
    ("Backspace", "Go to parent directory"),
    (":", "Run shell command in active directory"),
    ("Tab / Left / Right", "Switch panes"),
    ("h", "Toggle help panel"),
    ("m", "Choose display mode"),
]

ACTION_COMMANDS = [
    ("d", "Delete highlighted item"),
    ("c", "Copy item to the other pane"),
    ("t", "Move item to the other pane"),
    ("v", "View file contents read-only"),
    ("e", "Open file with $EDITOR"),
    ("a", "Stage item with git add"),
    ("u", "Unstage item from index"),
    ("r", "Restore item from HEAD"),
]


def build_help_lines(mode: BrowserMode) -> List[str]:
    """Return formatted help lines for the current mode."""
    lines: List[str] = [f"Display mode: {mode.label}"]
    lines.append("")
    lines.append("Navigation & layout:")
    for key, message in GENERAL_COMMANDS:
        lines.append(f"  {key:<18} {message}")
    lines.append("")
    lines.append("File & git actions:")
    for key, message in ACTION_COMMANDS:
        lines.append(f"  {key:<18} {message}")
    return lines


__all__ = ["build_help_lines"]
