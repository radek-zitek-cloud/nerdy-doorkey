"""Rendering helpers for the curses-based dual pane browser."""

from __future__ import annotations

import curses
from typing import Optional, Tuple, TYPE_CHECKING

from nedok.colors import get_file_color, get_git_color
from nedok.help_text import build_help_lines
from nedok.modes import BrowserMode
from nedok.render_dialogs import (
    render_confirmation_dialog,
    render_create_input,
    render_help_panel,
    render_mode_prompt,
    render_rename_input,
    render_ssh_connect_input,
)
from nedok.render_utils import determine_column_widths, draw_frame, draw_frame_title, truncate, truncate_end
from nedok.state import _PaneState

if TYPE_CHECKING:
    from nedok.browser import DualPaneBrowser

# Terminal size limits
MIN_TERMINAL_HEIGHT = 9
MIN_TERMINAL_WIDTH = 40
MIN_PANE_HEIGHT = 5

# Layout ratios
BOTTOM_PANE_RATIO = 3  # Terminal height divided by this
HELP_HINTS_HEIGHT = 3  # Height for permanent help hints display


def render_browser(browser: "DualPaneBrowser", stdscr: "curses._CursesWindow") -> None:  # type: ignore[name-defined]
    """Render the full dual-pane browser layout."""
    height, width = stdscr.getmaxyx()
    stdscr.erase()

    if height < MIN_TERMINAL_HEIGHT or width < MIN_TERMINAL_WIDTH:
        stdscr.addstr(0, 0, "Terminal too small for browser.")
        stdscr.refresh()
        return

    # Allocate space for help hints at bottom, command area in middle, and browser panes at top
    help_area_height = HELP_HINTS_HEIGHT
    remaining_height = height - help_area_height
    bottom_height = max(remaining_height // BOTTOM_PANE_RATIO, 4)
    top_height = remaining_height - bottom_height
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

    # Render permanent help hints at the bottom
    help_area_y = top_height + bottom_height
    render_help_hints(
        browser,
        stdscr,
        origin_y=help_area_y,
        origin_x=0,
        height=help_area_height,
        width=width,
    )

    try:
        show_cursor = (browser.in_command_mode or browser.in_rename_mode or
                      browser.in_create_mode or browser.in_ssh_connect_mode)
        curses.curs_set(1 if show_cursor else 0)
    except curses.error:
        pass

    if command_cursor is not None and show_cursor:
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
    draw_frame_title(stdscr, origin_y, origin_x, width, pane.current_dir_display)

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

    # Mode column header
    if mode is BrowserMode.FILE or mode is BrowserMode.OWNER:
        mode_header = "Mode"
    else:  # Git mode
        mode_header = "Git"
    stdscr.addnstr(
        header_y,
        mode_x,
        truncate(mode_header, mode_width).ljust(mode_width),
        mode_width,
        header_attr,
    )

    # Third column header (Size or User)
    if mode is BrowserMode.OWNER:
        size_header = "User"
        size_align = str.ljust
    else:
        size_header = "Size"
        size_align = str.rjust
    stdscr.addnstr(
        header_y,
        size_x,
        truncate(size_header, size_width) if mode is BrowserMode.OWNER else truncate(size_header, size_width).rjust(size_width),
        size_width,
        header_attr,
    )

    # Fourth column header (Modified or Group)
    if mode is BrowserMode.OWNER:
        modified_header = "Group"
    else:
        modified_header = "Modified"
    stdscr.addnstr(
        header_y,
        modified_x,
        truncate(modified_header, modified_width).ljust(modified_width),
        modified_width,
        header_attr,
    )

    viewport_height = max(interior_height - 1, 0)
    entries = pane.entries[pane.scroll_offset : pane.scroll_offset + viewport_height]

    for index, entry in enumerate(entries):
        y = header_y + 1 + index
        absolute_index = pane.scroll_offset + index

        # Get appropriate color based on mode
        if mode is BrowserMode.GIT:
            color_attrs = get_git_color(entry)
        else:
            # FILE and OWNER modes use file colors
            color_attrs = get_file_color(entry)

        # Add reverse video for selected item
        if is_active and absolute_index == pane.cursor_index:
            name_attrs = color_attrs | curses.A_REVERSE
            base_attrs = curses.A_REVERSE
        else:
            name_attrs = color_attrs
            base_attrs = curses.A_NORMAL

        name_text = truncate(entry.display_name, name_width)

        # Mode column value
        if mode is BrowserMode.GIT:
            mode_value = entry.git_status or "-"
        else:
            # FILE and OWNER modes show file mode
            mode_value = entry.display_mode
        mode_text = truncate(mode_value, mode_width)

        # Third and fourth columns depend on mode
        if mode is BrowserMode.OWNER:
            # OWNER mode: show user and group
            owner_parts = entry.display_owner.split(":", 1)
            size_text = truncate(owner_parts[0] if len(owner_parts) > 0 else "-", size_width)
            modified_text = truncate(owner_parts[1] if len(owner_parts) > 1 else "-", modified_width)
        else:
            # FILE and GIT modes: show size and modified
            size_text = truncate(entry.display_size, size_width)
            modified_text = truncate(entry.display_modified, modified_width)

        stdscr.addnstr(y, name_x, name_text.ljust(name_width), name_width, name_attrs)
        stdscr.addnstr(y, mode_x, mode_text.ljust(mode_width), mode_width, base_attrs)
        # User column left-aligned in OWNER mode, size right-aligned in other modes
        if mode is BrowserMode.OWNER:
            stdscr.addnstr(y, size_x, size_text.ljust(size_width), size_width, base_attrs)
        else:
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
    if browser.in_ssh_connect_mode:
        return render_ssh_connect_input(browser, stdscr, origin_y, origin_x, height, width)
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


def render_help_hints(
    browser: "DualPaneBrowser",
    stdscr: "curses._CursesWindow",  # type: ignore[name-defined]
    origin_y: int,
    origin_x: int,
    height: int,
    width: int,
) -> None:
    """Render the permanent compact help hints at the bottom."""
    if height < 3 or width < 10:
        return

    help_lines = build_help_lines(browser.mode)

    for index, line in enumerate(help_lines):
        if index >= height:
            break
        y = origin_y + index
        try:
            stdscr.addnstr(
                y,
                origin_x,
                truncate_end(line, width).ljust(width),
                width,
                curses.A_DIM,
            )
        except curses.error:
            pass


__all__ = [
    "render_browser",
    "render_browser_pane",
    "render_command_area",
    "render_help_hints",
]
