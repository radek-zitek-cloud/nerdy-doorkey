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
]

MODE_COMMANDS = {
    BrowserMode.FILE: [
        ("d", "Delete highlighted item"),
        ("v", "Move item to the other pane"),
        ("c", "Copy item to the other pane"),
    ],
    BrowserMode.GIT: [
        ("e", "Open file with $EDITOR"),
        ("v", "View file contents read-only"),
        ("a", "Stage item with git add"),
        ("u", "Unstage item from index"),
        ("r", "Restore item from HEAD"),
    ],
}


def build_help_lines(mode: BrowserMode) -> List[str]:
    """Return formatted help lines for the current mode."""
    lines: List[str] = ["Available Commands:"]
    for key, message in GENERAL_COMMANDS:
        lines.append(f"  {key:<18} {message}")
    lines.append("")
    lines.append(f"{mode.label} Mode:")
    for key, message in MODE_COMMANDS.get(mode, []):
        lines.append(f"  {key:<18} {message}")
    return lines


__all__ = ["build_help_lines"]
