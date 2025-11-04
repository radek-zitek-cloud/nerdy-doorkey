"""Directory pane state and entry models."""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from .formatting import format_size, format_timestamp


class PaneStateError(Exception):
    """Raised when pane state operations fail."""


@dataclass
class _PaneEntry:
    path: Path
    is_dir: bool
    is_parent: bool = False
    mode: str = ""
    size: Optional[int] = None
    modified: Optional[datetime] = None

    @property
    def display_name(self) -> str:
        """Return the text shown for the entry."""
        if self.is_parent:
            return ".."
        name = self.path.name or str(self.path)
        suffix = "/" if self.is_dir else ""
        return f"{name}{suffix}"

    @property
    def display_mode(self) -> str:
        """Return a printable mode string."""
        return self.mode or "?????????"

    @property
    def display_size(self) -> str:
        """Return a printable size string."""
        if self.size is None:
            return "-"
        return format_size(self.size)

    @property
    def display_modified(self) -> str:
        """Return a printable modified timestamp."""
        if self.modified is None:
            return "-"
        return format_timestamp(self.modified)


@dataclass
class _PaneState:
    current_dir: Path
    cursor_index: int = 0
    scroll_offset: int = 0
    entries: List[_PaneEntry] = field(default_factory=list)

    def refresh_entries(self) -> None:
        """Populate `entries` with directory contents."""
        items: List[_PaneEntry] = []

        if self.current_dir != self.current_dir.parent:
            items.append(self._build_entry(self.current_dir.parent, is_parent=True))

        try:
            candidates: Iterable[Path] = sorted(
                self.current_dir.iterdir(), key=self._sort_key
            )
        except PermissionError as err:
            raise PermissionError(
                f"Permission denied reading directory: {self.current_dir}"
            ) from err
        except FileNotFoundError as err:
            raise FileNotFoundError(
                f"Directory not found: {self.current_dir}"
            ) from err

        for entry in candidates:
            items.append(self._build_entry(entry))

        self.entries = items
        self.cursor_index = min(self.cursor_index, max(len(self.entries) - 1, 0))
        self.scroll_offset = min(self.scroll_offset, max(len(self.entries) - 1, 0))

    @staticmethod
    def _sort_key(path: Path) -> Tuple[int, str]:
        """Directories come first, then files alphabetically."""
        try:
            is_dir = path.is_dir()
        except OSError:
            is_dir = False
        return (0 if is_dir else 1, path.name.lower())

    def move_cursor(self, delta: int) -> None:
        """Move cursor by `delta` steps."""
        if not self.entries:
            self.cursor_index = 0
            self.scroll_offset = 0
            return
        self.cursor_index = max(0, min(self.cursor_index + delta, len(self.entries) - 1))

    def ensure_cursor_visible(self, viewport_height: int) -> None:
        """Adjust scroll offset so cursor is visible."""
        if viewport_height <= 0:
            self.scroll_offset = 0
            return
        if self.cursor_index < self.scroll_offset:
            self.scroll_offset = self.cursor_index
        elif self.cursor_index >= self.scroll_offset + viewport_height:
            self.scroll_offset = self.cursor_index - viewport_height + 1
        max_offset = max(len(self.entries) - viewport_height, 0)
        self.scroll_offset = max(0, min(self.scroll_offset, max_offset))

    def selected_entry(self) -> _PaneEntry | None:
        """Return currently highlighted entry."""
        if not self.entries:
            return None
        return self.entries[self.cursor_index]

    def enter_selected(self) -> None:
        """Enter the highlighted directory if possible."""
        entry = self.selected_entry()
        if entry is None:
            return
        if entry.is_dir:
            self.current_dir = entry.path.resolve()
            self.cursor_index = 0
            self.scroll_offset = 0
            self.refresh_entries()

    def _build_entry(self, path: Path, *, is_parent: bool = False) -> _PaneEntry:
        """Construct a pane entry for the given path."""
        stat_info = self._stat_or_none(path)
        is_dir = self._is_dir(path, stat_info)
        mode = stat.filemode(stat_info.st_mode) if stat_info else ""
        size: Optional[int] = None
        modified: Optional[datetime] = None
        if stat_info:
            modified = datetime.fromtimestamp(stat_info.st_mtime)
            if not stat.S_ISDIR(stat_info.st_mode):
                size = stat_info.st_size

        return _PaneEntry(
            path=path,
            is_dir=is_dir,
            is_parent=is_parent,
            mode=mode,
            size=size,
            modified=modified,
        )

    @staticmethod
    def _stat_or_none(path: Path) -> Optional[os.stat_result]:
        """Return stat information for `path`, or None if inaccessible."""
        try:
            return path.stat()
        except OSError:
            return None

    @staticmethod
    def _is_dir(path: Path, stat_info: Optional[os.stat_result]) -> bool:
        """Determine whether the path refers to a directory."""
        if stat_info is not None:
            return stat.S_ISDIR(stat_info.st_mode)
        try:
            return path.is_dir()
        except OSError:
            return False


__all__ = ["_PaneEntry", "_PaneState", "PaneStateError"]
