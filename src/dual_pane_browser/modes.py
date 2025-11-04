"""Browser mode definitions."""

from __future__ import annotations

from enum import Enum


class BrowserMode(Enum):
    FILE = "file"
    GIT = "git"

    @property
    def label(self) -> str:
        return "File" if self is BrowserMode.FILE else "Git"


ALL_MODES = [BrowserMode.FILE, BrowserMode.GIT]


__all__ = ["BrowserMode", "ALL_MODES"]
