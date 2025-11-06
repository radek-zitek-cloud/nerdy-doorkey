"""Enumerations that describe alternate column layouts for the UI."""

from __future__ import annotations

from enum import Enum


class BrowserMode(Enum):
    FILE = "file"
    TREE = "tree"
    GIT = "git"
    OWNER = "owner"

    @property
    def label(self) -> str:
        if self is BrowserMode.FILE:
            return "File"
        elif self is BrowserMode.TREE:
            return "Tree"
        elif self is BrowserMode.GIT:
            return "Git"
        else:
            return "Owner"


ALL_MODES = [BrowserMode.FILE, BrowserMode.TREE, BrowserMode.GIT, BrowserMode.OWNER]


__all__ = ["BrowserMode", "ALL_MODES"]
