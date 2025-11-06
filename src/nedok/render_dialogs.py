"""Draw the small pop-up panels used throughout the interface.

These helpers keep all dialog styling in one place so changes – for example,
centering text or honouring user-defined colours – are applied consistently.
"""

from __future__ import annotations

import curses
from typing import Optional, Tuple, TYPE_CHECKING

from nedok.colors import ColorPair
from nedok.help_text import build_help_lines
from nedok.modes import ALL_MODES
from nedok.render_utils import draw_frame, draw_frame_title, truncate, truncate_end

if TYPE_CHECKING:
    from nedok.browser import DualPaneBrowser


def render_mode_prompt(
    browser: "DualPaneBrowser",
    stdscr: "curses._CursesWindow",  # type: ignore[name-defined]
    screen_height: int,
    screen_width: int,
) -> None:
    """Render mode selection overlay with the dialog color scheme."""
    color_attr = curses.color_pair(ColorPair.DIALOG)
    content_lines = [
        "",
        f"Current: {browser.mode.label} mode",
        "",
        "[f] File mode",
        "[t] Tree mode",
        "[g] Git mode",
        "[o] Owner mode",
        "",
        "Esc to cancel",
    ]

    max_content_width = max(len(line) for line in content_lines)
    box_width = min(max_content_width + 4, max(screen_width - 2, 12))
    box_height = min(len(content_lines) + 4, max(screen_height - 2, 6))

    origin_y = max((screen_height - box_height) // 2, 0)
    origin_x = max((screen_width - box_width) // 2, 0)

    draw_frame(stdscr, origin_y, origin_x, box_height, box_width, color_attr)
    draw_frame_title(
        stdscr,
        origin_y,
        origin_x,
        box_width,
        "Select Mode",
        color_attr | curses.A_BOLD,
    )

    interior_width = max(box_width - 2, 0)
    interior_height = max(box_height - 2, 0)
    start_y = origin_y + 1

    for index in range(interior_height):
        line = content_lines[index] if index < len(content_lines) else ""
        attr = color_attr | (curses.A_BOLD if index == 0 else curses.A_NORMAL)
        truncated = truncate(line, interior_width)
        centered = truncated.center(interior_width)
        stdscr.addnstr(
            start_y + index,
            origin_x + 1,
            centered,
            interior_width,
            attr,
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
    """Render comprehensive help overlay."""
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


def render_confirmation_overlay(
    browser: "DualPaneBrowser",
    stdscr: "curses._CursesWindow",  # type: ignore[name-defined]
    screen_height: int,
    screen_width: int,
) -> None:
    """Render a centered colorful confirmation popup."""
    if browser.pending_action is None:
        return

    message, _ = browser.pending_action
    color_attr = curses.color_pair(ColorPair.DIALOG)

    content_lines = [
        "",
        message,
        "",
        "[Y] confirm    [N]/Esc cancel",
    ]

    max_content_width = max(len(line) for line in content_lines)
    box_width = min(max_content_width + 4, max(screen_width - 2, 10))
    box_height = min(len(content_lines) + 4, max(screen_height - 2, 5))

    origin_y = max((screen_height - box_height) // 2, 0)
    origin_x = max((screen_width - box_width) // 2, 0)

    draw_frame(stdscr, origin_y, origin_x, box_height, box_width, color_attr)
    draw_frame_title(
        stdscr,
        origin_y,
        origin_x,
        box_width,
        "Confirm Action",
        color_attr | curses.A_BOLD,
    )

    interior_width = max(box_width - 2, 0)
    interior_height = max(box_height - 2, 0)

    for index in range(interior_height):
        line = content_lines[index] if index < len(content_lines) else ""
        attr = color_attr | (curses.A_BOLD if index == 0 else curses.A_NORMAL)
        truncated = truncate(line, interior_width)
        centered = truncated.center(interior_width)
        stdscr.addnstr(
            origin_y + 1 + index,
            origin_x + 1,
            centered,
            interior_width,
            attr,
        )


def render_rename_input(
    browser: "DualPaneBrowser",
    stdscr: "curses._CursesWindow",  # type: ignore[name-defined]
    origin_y: int,
    origin_x: int,
    height: int,
    width: int,
) -> Optional[Tuple[int, int]]:
    """Render the rename input."""
    color_attr = curses.color_pair(ColorPair.DIALOG)
    draw_frame(stdscr, origin_y, origin_x, height, width, color_attr)
    draw_frame_title(stdscr, origin_y, origin_x, width, "Rename", color_attr | curses.A_BOLD)
    interior_width = max(width - 2, 0)
    interior_height = max(height - 2, 0)
    if interior_width <= 0 or interior_height <= 0:
        return None

    prompt_x = origin_x + 1
    start_y = origin_y + 1

    prompt_prefix = "Name> "
    prompt_text = f"{prompt_prefix}{browser.rename_buffer}"
    status_text = browser.status_message or "Enter new name (Enter to confirm, Esc to cancel)"

    # Fill all interior lines with dialog color
    for index in range(interior_height):
        y = start_y + index
        if index == 0:
            # Name input line
            text = truncate_end(prompt_text, interior_width).ljust(interior_width)
        elif index == 1:
            # Status line
            text = truncate_end(status_text, interior_width).ljust(interior_width)
        else:
            # Empty line
            text = " " * interior_width
        stdscr.addnstr(y, prompt_x, text, interior_width, color_attr)

    # Position cursor
    cursor_x = prompt_x + len(prompt_prefix) + len(browser.rename_buffer)
    max_cursor_x = prompt_x + interior_width - 1
    if cursor_x > max_cursor_x:
        cursor_x = max_cursor_x
    return (start_y, cursor_x)


def render_command_input(
    browser: "DualPaneBrowser",
    stdscr: "curses._CursesWindow",  # type: ignore[name-defined]
    origin_y: int,
    origin_x: int,
    height: int,
    width: int,
) -> Optional[Tuple[int, int]]:
    """Render the command input popup."""
    color_attr = curses.color_pair(ColorPair.DIALOG)
    draw_frame(stdscr, origin_y, origin_x, height, width, color_attr)
    draw_frame_title(stdscr, origin_y, origin_x, width, "Execute Command", color_attr | curses.A_BOLD)
    interior_width = max(width - 2, 0)
    interior_height = max(height - 2, 0)
    if interior_width <= 0 or interior_height <= 0:
        return None

    prompt_x = origin_x + 1
    start_y = origin_y + 1

    prompt_prefix = "$ "
    prompt_text = f"{prompt_prefix}{browser.command_buffer}"
    status_text = browser.status_message or "Enter shell command (Enter to execute, Esc to cancel)"

    # Fill all interior lines with dialog color
    for index in range(interior_height):
        y = start_y + index
        if index == 0:
            # Command input line
            text = truncate_end(prompt_text, interior_width).ljust(interior_width)
        elif index == 1:
            # Status line
            text = truncate_end(status_text, interior_width).ljust(interior_width)
        else:
            # Empty line
            text = " " * interior_width
        stdscr.addnstr(y, prompt_x, text, interior_width, color_attr)

    # Position cursor
    cursor_x = prompt_x + len(prompt_prefix) + len(browser.command_buffer)
    max_cursor_x = prompt_x + interior_width - 1
    if cursor_x > max_cursor_x:
        cursor_x = max_cursor_x
    return (start_y, cursor_x)


def render_create_input(
    browser: "DualPaneBrowser",
    stdscr: "curses._CursesWindow",  # type: ignore[name-defined]
    origin_y: int,
    origin_x: int,
    height: int,
    width: int,
) -> Optional[Tuple[int, int]]:
    """Render the create file/directory input popup."""
    item_type = "Directory" if browser.create_is_dir else "File"
    color_attr = curses.color_pair(ColorPair.DIALOG)
    draw_frame(stdscr, origin_y, origin_x, height, width, color_attr)
    draw_frame_title(stdscr, origin_y, origin_x, width, f"Create {item_type}", color_attr | curses.A_BOLD)
    interior_width = max(width - 2, 0)
    interior_height = max(height - 2, 0)
    if interior_width <= 0 or interior_height <= 0:
        return None

    prompt_x = origin_x + 1
    start_y = origin_y + 1

    prompt_prefix = "Name> "
    prompt_text = f"{prompt_prefix}{browser.create_buffer}"
    status_text = browser.status_message or "Enter name (Enter to create, Esc to cancel)"

    # Fill all interior lines with dialog color
    for index in range(interior_height):
        y = start_y + index
        if index == 0:
            # Name input line
            text = truncate_end(prompt_text, interior_width).ljust(interior_width)
        elif index == 1:
            # Status line
            text = truncate_end(status_text, interior_width).ljust(interior_width)
        else:
            # Empty line
            text = " " * interior_width
        stdscr.addnstr(y, prompt_x, text, interior_width, color_attr)

    # Position cursor
    cursor_x = prompt_x + len(prompt_prefix) + len(browser.create_buffer)
    max_cursor_x = prompt_x + interior_width - 1
    if cursor_x > max_cursor_x:
        cursor_x = max_cursor_x
    return (start_y, cursor_x)


def render_ssh_connect_input(
    browser: "DualPaneBrowser",
    stdscr: "curses._CursesWindow",  # type: ignore[name-defined]
    origin_y: int,
    origin_x: int,
    height: int,
    width: int,
) -> Optional[Tuple[int, int]]:
    """Render the SSH connection input."""
    color_attr = curses.color_pair(ColorPair.DIALOG)
    draw_frame(stdscr, origin_y, origin_x, height, width, color_attr)
    draw_frame_title(stdscr, origin_y, origin_x, width, "SSH Connect", color_attr | curses.A_BOLD)
    interior_width = max(width - 2, 0)
    interior_height = max(height - 2, 0)
    if interior_width <= 0 or interior_height <= 0:
        return None

    prompt_x = origin_x + 1
    start_y = origin_y + 1

    # Field labels and values
    fields = [
        ("Host: ", browser.ssh_host_buffer),
        ("User: ", browser.ssh_user_buffer),
        ("Password: ", "*" * len(browser.ssh_password_buffer)),
    ]

    cursor_y = None
    cursor_x = None

    status_text = "Tab: next field | Enter: connect/next | Esc: cancel"

    # Fill all interior lines with dialog color
    for index in range(interior_height):
        y = start_y + index
        if index < len(fields):
            # Field input line
            label, value = fields[index]
            is_active = (index == browser.ssh_input_field)
            attr = color_attr | (curses.A_BOLD if is_active else curses.A_NORMAL)
            prompt_text = f"{label}{value}"
            text = truncate_end(prompt_text, interior_width).ljust(interior_width)

            # Store cursor position for active field
            if is_active:
                cursor_y = y
                cursor_x = prompt_x + len(label) + len(value)
                cursor_x = min(cursor_x, prompt_x + interior_width - 1)
        elif index == 4:
            # Status line at index 4
            attr = color_attr
            text = truncate_end(status_text, interior_width).ljust(interior_width)
        else:
            # Empty line
            attr = color_attr
            text = " " * interior_width

        stdscr.addnstr(y, prompt_x, text, interior_width, attr)

    if cursor_y is not None and cursor_x is not None:
        return (cursor_y, cursor_x)
    return None


__all__ = [
    "render_mode_prompt",
    "render_help_panel",
    "render_confirmation_overlay",
    "render_rename_input",
    "render_create_input",
    "render_ssh_connect_input",
]
