"""Rendering helpers for the curses-based dual pane browser."""

from __future__ import annotations

import curses
from typing import Optional, Tuple, TYPE_CHECKING

from .help_text import build_help_lines
from .modes import BrowserMode
from .state import _PaneState

if TYPE_CHECKING:
    from .browser import DualPaneBrowser

# Box drawing characters
BOX_TOP_LEFT = "┌"
BOX_TOP_RIGHT = "┐"
BOX_BOTTOM_LEFT = "└"
BOX_BOTTOM_RIGHT = "┘"
BOX_HORIZONTAL = "─"
BOX_VERTICAL = "│"

# Terminal size limits
MIN_TERMINAL_HEIGHT = 9
MIN_TERMINAL_WIDTH = 40
MIN_PANE_HEIGHT = 5

# Layout ratios
BOTTOM_PANE_RATIO = 3  # Terminal height divided by this


def render_browser(browser: "DualPaneBrowser", stdscr: "curses._CursesWindow") -> None:  # type: ignore[name-defined]
    """Render the full dual-pane browser layout."""
    height, width = stdscr.getmaxyx()
    stdscr.erase()

    if height < MIN_TERMINAL_HEIGHT or width < MIN_TERMINAL_WIDTH:
        stdscr.addstr(0, 0, "Terminal too small for browser.")
        stdscr.refresh()
        return

    bottom_height = max(height // BOTTOM_PANE_RATIO, 4)
    top_height = height - bottom_height
    if top_height < MIN_PANE_HEIGHT:
        stdscr.addstr(0, 0, "Terminal height insufficient for layout.")
        stdscr.refresh()
        return

    pane_width = width // 2
    right_width = width - pane_width

    browser_entry_rows = max(top_height - 3, 0)
    browser.left.ensure_cursor_visible(browser_entry_rows)
    browser.right.ensure_cursor_visible(browser_entry_rows)

    render_browser_pane(
        stdscr,
        pane=browser.left,
        origin_y=0,
        origin_x=0,
        height=top_height,
        width=pane_width,
        is_active=(browser.active_index == 0),
        mode=browser.mode,
    )
    render_browser_pane(
        stdscr,
        pane=browser.right,
        origin_y=0,
        origin_x=pane_width,
        height=top_height,
        width=right_width,
        is_active=(browser.active_index == 1),
        mode=browser.mode,
    )

    command_cursor = render_command_area(
        browser,
        stdscr,
        origin_y=top_height,
        origin_x=0,
        height=bottom_height,
        width=width,
    )

    try:
        curses.curs_set(1 if (browser.in_command_mode or browser.in_rename_mode or browser.in_create_mode) else 0)
    except curses.error:
        pass

    if command_cursor is not None and (browser.in_command_mode or browser.in_rename_mode or browser.in_create_mode):
        try:
            stdscr.move(*command_cursor)
        except curses.error:
            pass

    stdscr.refresh()


def render_browser_pane(
    stdscr: "curses._CursesWindow",  # type: ignore[name-defined]
    *,
    pane: _PaneState,
    origin_y: int,
    origin_x: int,
    height: int,
    width: int,
    is_active: bool,
    mode: BrowserMode,
) -> None:
    """Render a single pane within the provided bounds."""
    if height < 3 or width < 6:
        return

    draw_frame(stdscr, origin_y, origin_x, height, width)
    draw_frame_title(stdscr, origin_y, origin_x, width, str(pane.current_dir))

    interior_width = max(width - 2, 0)
    interior_height = max(height - 2, 0)
    if interior_width <= 0 or interior_height <= 0:
        return

    name_width, mode_width, size_width, modified_width = determine_column_widths(
        interior_width
    )
    header_y = origin_y + 1
    name_x = origin_x + 1
    mode_x = name_x + name_width + 1
    size_x = mode_x + mode_width + 1
    modified_x = size_x + size_width + 1

    header_attr = curses.A_BOLD
    stdscr.addnstr(
        header_y,
        name_x,
        truncate("Name", name_width).ljust(name_width),
        name_width,
        header_attr,
    )
    stdscr.addnstr(
        header_y,
        mode_x,
        truncate("Mode" if mode is BrowserMode.FILE else "Git", mode_width).ljust(mode_width),
        mode_width,
        header_attr,
    )
    stdscr.addnstr(
        header_y,
        size_x,
        truncate("Size", size_width).rjust(size_width),
        size_width,
        header_attr,
    )
    stdscr.addnstr(
        header_y,
        modified_x,
        truncate("Modified", modified_width).ljust(modified_width),
        modified_width,
        header_attr,
    )

    viewport_height = max(interior_height - 1, 0)
    entries = pane.entries[pane.scroll_offset : pane.scroll_offset + viewport_height]

    for index, entry in enumerate(entries):
        y = header_y + 1 + index
        absolute_index = pane.scroll_offset + index
        base_attrs = curses.A_NORMAL
        if is_active and absolute_index == pane.cursor_index:
            base_attrs |= curses.A_REVERSE
        name_attrs = base_attrs | (curses.A_BOLD if entry.is_dir else 0)

        name_text = truncate(entry.display_name, name_width)
        if mode is BrowserMode.FILE:
            mode_value = entry.display_mode
        else:
            mode_value = entry.git_status or "-"
        mode_text = truncate(mode_value, mode_width)
        size_text = truncate(entry.display_size, size_width)
        modified_text = truncate(entry.display_modified, modified_width)

        stdscr.addnstr(y, name_x, name_text.ljust(name_width), name_width, name_attrs)
        stdscr.addnstr(y, mode_x, mode_text.ljust(mode_width), mode_width, base_attrs)
        stdscr.addnstr(y, size_x, size_text.rjust(size_width), size_width, base_attrs)
        stdscr.addnstr(
            y, modified_x, modified_text.ljust(modified_width), modified_width, base_attrs
        )


def render_command_area(
    browser: "DualPaneBrowser",
    stdscr: "curses._CursesWindow",  # type: ignore[name-defined]
    *,
    origin_y: int,
    origin_x: int,
    height: int,
    width: int,
) -> Optional[Tuple[int, int]]:
    """Render the command input and output pane."""
    if height < 3 or width < 10:
        return None

    if browser.pending_action:
        return render_confirmation_dialog(browser, stdscr, origin_y, origin_x, height, width)
    if browser.in_mode_prompt:
        return render_mode_prompt(browser, stdscr, origin_y, origin_x, height, width)
    if browser.show_help:
        return render_help_panel(browser, stdscr, origin_y, origin_x, height, width)
    if browser.in_rename_mode:
        return render_rename_input(browser, stdscr, origin_y, origin_x, height, width)
    if browser.in_create_mode:
        return render_create_input(browser, stdscr, origin_y, origin_x, height, width)

    draw_frame(stdscr, origin_y, origin_x, height, width)
    draw_frame_title(stdscr, origin_y, origin_x, width, "Command Console")

    interior_width = max(width - 2, 0)
    interior_height = max(height - 2, 0)
    if interior_width <= 0 or interior_height <= 0:
        return None

    prompt_y = origin_y + 1
    prompt_x = origin_x + 1
    prompt_prefix = "CMD> " if browser.in_command_mode else "cmd> "
    prompt_text = f"{prompt_prefix}{browser.command_buffer}"
    truncated_prompt = truncate_end(prompt_text, interior_width)
    stdscr.addnstr(prompt_y, prompt_x, truncated_prompt.ljust(interior_width), interior_width)

    status_y = prompt_y + 1
    status_text = browser.status_message or "Press : to enter command mode. q to quit."
    status_text = f"[{browser.mode.label} mode] {status_text}"
    stdscr.addnstr(
        status_y,
        prompt_x,
        truncate_end(status_text, interior_width).ljust(interior_width),
        interior_width,
    )

    output_start = status_y + 1
    available_rows = interior_height - 2
    if available_rows > 0:
        output_lines = browser.command_output[-available_rows:] if browser.command_output else []
        for offset in range(available_rows):
            y = output_start + offset
            if offset < len(output_lines):
                line = output_lines[offset]
                stdscr.addnstr(
                    y,
                    prompt_x,
                    truncate_end(line, interior_width).ljust(interior_width),
                    interior_width,
                )
            else:
                stdscr.addnstr(y, prompt_x, " " * interior_width, interior_width)

    if not browser.in_command_mode:
        return None

    cursor_x = prompt_x + len(prompt_prefix) + len(browser.command_buffer)
    max_cursor_x = prompt_x + interior_width - 1
    if cursor_x > max_cursor_x:
        cursor_x = max_cursor_x
    return (prompt_y, cursor_x)


def render_mode_prompt(
    browser: "DualPaneBrowser",
    stdscr: "curses._CursesWindow",  # type: ignore[name-defined]
    origin_y: int,
    origin_x: int,
    height: int,
    width: int,
) -> Optional[Tuple[int, int]]:
    draw_frame(stdscr, origin_y, origin_x, height, width)
    draw_frame_title(stdscr, origin_y, origin_x, width, "Select Mode")
    interior_width = max(width - 2, 0)
    interior_height = max(height - 2, 0)
    if interior_width <= 0 or interior_height <= 0:
        return None

    prompt_x = origin_x + 1
    y = origin_y + 1
    lines = [
        f"Current: {browser.mode.label} mode",
        "Choose new mode:",
        "  [F] File mode",
        "  [G] Git mode",
        "Press Esc to cancel.",
    ]

    for index, line in enumerate(lines):
        if index >= interior_height:
            break
        stdscr.addnstr(
            y + index,
            prompt_x,
            truncate_end(line, interior_width).ljust(interior_width),
            interior_width,
        )
    return None


def render_help_panel(
    browser: "DualPaneBrowser",
    stdscr: "curses._CursesWindow",  # type: ignore[name-defined]
    origin_y: int,
    origin_x: int,
    height: int,
    width: int,
) -> Optional[Tuple[int, int]]:
    draw_frame(stdscr, origin_y, origin_x, height, width)
    draw_frame_title(stdscr, origin_y, origin_x, width, "Help")
    interior_width = max(width - 2, 0)
    interior_height = max(height - 2, 0)
    if interior_width <= 0 or interior_height <= 0:
        return None

    lines = build_help_lines(browser.mode)
    prompt_x = origin_x + 1
    start_y = origin_y + 1
    for index in range(interior_height):
        y = start_y + index
        text = lines[index] if index < len(lines) else ""
        stdscr.addnstr(
            y,
            prompt_x,
            truncate_end(text, interior_width).ljust(interior_width),
            interior_width,
        )
    return None


def render_confirmation_dialog(
    browser: "DualPaneBrowser",
    stdscr: "curses._CursesWindow",  # type: ignore[name-defined]
    origin_y: int,
    origin_x: int,
    height: int,
    width: int,
) -> Optional[Tuple[int, int]]:
    """Render a confirmation dialog."""
    if browser.pending_action is None:
        return None

    draw_frame(stdscr, origin_y, origin_x, height, width)
    draw_frame_title(stdscr, origin_y, origin_x, width, "Confirm Action")
    interior_width = max(width - 2, 0)
    interior_height = max(height - 2, 0)
    if interior_width <= 0 or interior_height <= 0:
        return None

    message, _ = browser.pending_action
    prompt_x = origin_x + 1
    y = origin_y + 1

    lines = [
        message,
        "",
        "Press [Y]es to confirm or [N]o/Esc to cancel.",
    ]

    for index, line in enumerate(lines):
        if index >= interior_height:
            break
        attrs = curses.A_BOLD if index == 0 else curses.A_NORMAL
        stdscr.addnstr(
            y + index,
            prompt_x,
            truncate_end(line, interior_width).ljust(interior_width),
            interior_width,
            attrs,
        )

    return None


def render_rename_input(
    browser: "DualPaneBrowser",
    stdscr: "curses._CursesWindow",  # type: ignore[name-defined]
    origin_y: int,
    origin_x: int,
    height: int,
    width: int,
) -> Optional[Tuple[int, int]]:
    """Render the rename input."""
    draw_frame(stdscr, origin_y, origin_x, height, width)
    draw_frame_title(stdscr, origin_y, origin_x, width, "Rename")
    interior_width = max(width - 2, 0)
    interior_height = max(height - 2, 0)
    if interior_width <= 0 or interior_height <= 0:
        return None

    prompt_x = origin_x + 1
    prompt_y = origin_y + 1

    prompt_prefix = "Name> "
    prompt_text = f"{prompt_prefix}{browser.rename_buffer}"
    truncated_prompt = truncate_end(prompt_text, interior_width)
    stdscr.addnstr(prompt_y, prompt_x, truncated_prompt.ljust(interior_width), interior_width)

    status_y = prompt_y + 1
    status_text = browser.status_message or "Enter new name (Enter to confirm, Esc to cancel)"
    stdscr.addnstr(
        status_y,
        prompt_x,
        truncate_end(status_text, interior_width).ljust(interior_width),
        interior_width,
    )

    # Position cursor
    cursor_x = prompt_x + len(prompt_prefix) + len(browser.rename_buffer)
    max_cursor_x = prompt_x + interior_width - 1
    if cursor_x > max_cursor_x:
        cursor_x = max_cursor_x
    return (prompt_y, cursor_x)


def render_create_input(
    browser: "DualPaneBrowser",
    stdscr: "curses._CursesWindow",  # type: ignore[name-defined]
    origin_y: int,
    origin_x: int,
    height: int,
    width: int,
) -> Optional[Tuple[int, int]]:
    """Render the create file/directory input."""
    item_type = "Directory" if browser.create_is_dir else "File"
    draw_frame(stdscr, origin_y, origin_x, height, width)
    draw_frame_title(stdscr, origin_y, origin_x, width, f"Create {item_type}")
    interior_width = max(width - 2, 0)
    interior_height = max(height - 2, 0)
    if interior_width <= 0 or interior_height <= 0:
        return None

    prompt_x = origin_x + 1
    prompt_y = origin_y + 1

    prompt_prefix = "Name> "
    prompt_text = f"{prompt_prefix}{browser.create_buffer}"
    truncated_prompt = truncate_end(prompt_text, interior_width)
    stdscr.addnstr(prompt_y, prompt_x, truncated_prompt.ljust(interior_width), interior_width)

    status_y = prompt_y + 1
    status_text = browser.status_message or "Enter name (Enter to create, Esc to cancel)"
    stdscr.addnstr(
        status_y,
        prompt_x,
        truncate_end(status_text, interior_width).ljust(interior_width),
        interior_width,
    )

    # Position cursor
    cursor_x = prompt_x + len(prompt_prefix) + len(browser.create_buffer)
    max_cursor_x = prompt_x + interior_width - 1
    if cursor_x > max_cursor_x:
        cursor_x = max_cursor_x
    return (prompt_y, cursor_x)


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
    "render_browser",
    "render_browser_pane",
    "render_command_area",
    "determine_column_widths",
    "draw_frame",
    "draw_frame_title",
    "truncate",
    "truncate_end",
]
