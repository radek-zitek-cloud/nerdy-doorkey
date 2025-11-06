"""Browser mode definitions."""

from __future__ import annotations

from enum import Enum


class BrowserMode(Enum):
    FILE = "file"
    GIT = "git"
    OWNER = "owner"

    @property
    def label(self) -> str:
        if self is BrowserMode.FILE:
            return "File"
        elif self is BrowserMode.GIT:
            return "Git"
        else:
            return "Owner"


ALL_MODES = [BrowserMode.FILE, BrowserMode.GIT, BrowserMode.OWNER]


__all__ = ["BrowserMode", "ALL_MODES"]
