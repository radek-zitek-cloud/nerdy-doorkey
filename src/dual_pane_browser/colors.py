"""Color management for the dual pane browser."""

from __future__ import annotations

import curses
from enum import IntEnum


class ColorPair(IntEnum):
    """Color pair constants for curses."""
    DEFAULT = 0
    DIRECTORY = 1
    EXECUTABLE = 2
    SYMLINK = 3
    HIDDEN = 4
    READONLY = 5

    # Git status colors
    GIT_UNTRACKED = 10
    GIT_MODIFIED = 11
    GIT_STAGED = 12
    GIT_DELETED = 13
    GIT_RENAMED = 14
    GIT_CLEAN = 15


def init_colors() -> None:
    """Initialize curses color pairs.

    Call this after curses initialization and before rendering.
    """
    if not curses.has_colors():
        return

    curses.start_color()
    curses.use_default_colors()

    # File mode colors
    curses.init_pair(ColorPair.DIRECTORY, curses.COLOR_BLUE, -1)
    curses.init_pair(ColorPair.EXECUTABLE, curses.COLOR_GREEN, -1)
    curses.init_pair(ColorPair.SYMLINK, curses.COLOR_CYAN, -1)
    curses.init_pair(ColorPair.HIDDEN, 8, -1)  # Bright black (gray) if available
    curses.init_pair(ColorPair.READONLY, curses.COLOR_YELLOW, -1)

    # Git mode colors
    curses.init_pair(ColorPair.GIT_UNTRACKED, curses.COLOR_RED, -1)
    curses.init_pair(ColorPair.GIT_MODIFIED, curses.COLOR_YELLOW, -1)
    curses.init_pair(ColorPair.GIT_STAGED, curses.COLOR_GREEN, -1)
    curses.init_pair(ColorPair.GIT_DELETED, curses.COLOR_RED, -1)
    curses.init_pair(ColorPair.GIT_RENAMED, curses.COLOR_CYAN, -1)
    curses.init_pair(ColorPair.GIT_CLEAN, 8, -1)  # Dim


def get_file_color(entry: "PaneEntry") -> int:  # type: ignore[name-defined]
    """Get the appropriate color for a file entry in File mode.

    Args:
        entry: The pane entry to colorize

    Returns:
        curses color pair number and attributes
    """
    if not curses.has_colors():
        return curses.A_NORMAL

    # Parent directory
    if entry.is_parent:
        return curses.color_pair(ColorPair.DIRECTORY) | curses.A_BOLD

    # Directories
    if entry.is_dir:
        return curses.color_pair(ColorPair.DIRECTORY) | curses.A_BOLD

    # Symlinks
    if entry.is_symlink:
        return curses.color_pair(ColorPair.SYMLINK)

    # Hidden files (dotfiles)
    if entry.path.name.startswith('.'):
        return curses.color_pair(ColorPair.HIDDEN)

    # Executables
    if entry.is_executable:
        return curses.color_pair(ColorPair.EXECUTABLE) | curses.A_BOLD

    # Read-only files
    if entry.is_readonly:
        return curses.color_pair(ColorPair.READONLY)

    # Regular files
    return curses.A_NORMAL


def get_git_color(entry: "PaneEntry") -> int:  # type: ignore[name-defined]
    """Get the appropriate color for a file entry in Git mode.

    Args:
        entry: The pane entry to colorize

    Returns:
        curses color pair number and attributes
    """
    if not curses.has_colors():
        return curses.A_NORMAL

    # Parent directory - always show as directory
    if entry.is_parent:
        return curses.color_pair(ColorPair.DIRECTORY) | curses.A_BOLD

    # Directories - show as directory color
    if entry.is_dir:
        return curses.color_pair(ColorPair.DIRECTORY) | curses.A_BOLD

    # Check git status
    status = entry.git_status or ""

    # Untracked files
    if status == "??":
        return curses.color_pair(ColorPair.GIT_UNTRACKED) | curses.A_BOLD

    # Deleted files
    if "D" in status:
        return curses.color_pair(ColorPair.GIT_DELETED)

    # Renamed files
    if "R" in status:
        return curses.color_pair(ColorPair.GIT_RENAMED)

    # Staged changes (left column has change)
    if status and status[0] != " " and status[0] != "?":
        return curses.color_pair(ColorPair.GIT_STAGED) | curses.A_BOLD

    # Modified but not staged (right column has change)
    if status and len(status) > 1 and status[1] != " ":
        return curses.color_pair(ColorPair.GIT_MODIFIED)

    # Clean/unmodified files - dim them
    return curses.color_pair(ColorPair.GIT_CLEAN)


__all__ = ["ColorPair", "init_colors", "get_file_color", "get_git_color"]
