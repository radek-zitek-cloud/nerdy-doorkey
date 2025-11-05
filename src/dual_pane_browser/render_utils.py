"""Utility functions for rendering."""

from __future__ import annotations

import curses
from typing import Tuple

# Box drawing characters
BOX_TOP_LEFT = "┌"
BOX_TOP_RIGHT = "┐"
BOX_BOTTOM_LEFT = "└"
BOX_BOTTOM_RIGHT = "┘"
BOX_HORIZONTAL = "─"
BOX_VERTICAL = "│"


def determine_column_widths(interior_width: int) -> Tuple[int, int, int, int]:
    """Compute dynamic column widths for the browser panes."""
    min_col_width = 4
    mode_width = min(10, max(min_col_width, interior_width // 8))
    size_width = min(12, max(min_col_width, interior_width // 8))
    modified_width = min(len("Sep 30 23:59"), max(min_col_width, interior_width // 5))

    reserved = mode_width + size_width + modified_width + 3
    remaining = interior_width - reserved

    if remaining < min_col_width:
        deficit = min_col_width - remaining
        adjustable = [
            ("modified", modified_width),
            ("size", size_width),
            ("mode", mode_width),
        ]
        for name, width in adjustable:
            if deficit <= 0:
                break
            reduction = min(width - min_col_width, deficit)
            if reduction <= 0:
                continue
            if name == "modified":
                modified_width -= reduction
            elif name == "size":
                size_width -= reduction
            else:
                mode_width -= reduction
            deficit -= reduction
        remaining = interior_width - (mode_width + size_width + modified_width + 3)

    name_width = max(min_col_width, remaining)
    return name_width, mode_width, size_width, modified_width


def draw_frame(
    stdscr: "curses._CursesWindow",  # type: ignore[name-defined]
    origin_y: int,
    origin_x: int,
    height: int,
    width: int,
) -> None:
    """Draw a rectangular ASCII frame."""
    if height < 2 or width < 2:
        return

    top = origin_y
    bottom = origin_y + height - 1
    left = origin_x
    right = origin_x + width - 1

    try:
        stdscr.addch(top, left, BOX_TOP_LEFT)
        stdscr.addch(top, right, BOX_TOP_RIGHT)
        stdscr.addch(bottom, left, BOX_BOTTOM_LEFT)
        stdscr.addch(bottom, right, BOX_BOTTOM_RIGHT)

        for x_axis in range(left + 1, right):
            stdscr.addch(top, x_axis, BOX_HORIZONTAL)
            stdscr.addch(bottom, x_axis, BOX_HORIZONTAL)

        for y_axis in range(top + 1, bottom):
            stdscr.addch(y_axis, left, BOX_VERTICAL)
            stdscr.addch(y_axis, right, BOX_VERTICAL)
    except curses.error:
        pass


def draw_frame_title(
    stdscr: "curses._CursesWindow",  # type: ignore[name-defined]
    origin_y: int,
    origin_x: int,
    width: int,
    title: str,
) -> None:
    """Overlay a title along the top border of a frame."""
    available = max(width - 2, 0)
    if available <= 0:
        return
    truncated = truncate_end(title, available)
    try:
        stdscr.addnstr(
            origin_y, origin_x + 1, truncated.ljust(available), available, curses.A_BOLD
        )
    except curses.error:
        pass


def truncate(text: str, max_width: int) -> str:
    """Truncate text to fit within max_width, appending ellipsis if needed."""
    if max_width <= 0:
        return ""
    if len(text) <= max_width:
        return text
    if max_width <= 3:
        return text[:max_width]
    return text[: max_width - 3] + "..."


def truncate_end(text: str, max_width: int) -> str:
    """Truncate text from the end to fit within max_width."""
    if max_width <= 0:
        return ""
    if len(text) <= max_width:
        return text
    return text[-max_width:]


__all__ = [
    "BOX_TOP_LEFT",
    "BOX_TOP_RIGHT",
    "BOX_BOTTOM_LEFT",
    "BOX_BOTTOM_RIGHT",
    "BOX_HORIZONTAL",
    "BOX_VERTICAL",
    "determine_column_widths",
    "draw_frame",
    "draw_frame_title",
    "truncate",
    "truncate_end",
]
