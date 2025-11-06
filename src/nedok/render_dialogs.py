"""Modal dialog rendering for the dual pane browser."""

from __future__ import annotations

import curses
from typing import Optional, Tuple, TYPE_CHECKING

from nedok.help_text import build_help_lines
from nedok.modes import ALL_MODES
from nedok.render_utils import draw_frame, draw_frame_title, truncate_end

if TYPE_CHECKING:
    from nedok.browser import DualPaneBrowser


def render_mode_prompt(
    browser: "DualPaneBrowser",
    stdscr: "curses._CursesWindow",  # type: ignore[name-defined]
    origin_y: int,
    origin_x: int,
    height: int,
    width: int,
) -> Optional[Tuple[int, int]]:
    """Render mode selection overlay."""
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
        "  [O] Owner mode",
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


def render_ssh_connect_input(
    browser: "DualPaneBrowser",
    stdscr: "curses._CursesWindow",  # type: ignore[name-defined]
    origin_y: int,
    origin_x: int,
    height: int,
    width: int,
) -> Optional[Tuple[int, int]]:
    """Render the SSH connection input."""
    draw_frame(stdscr, origin_y, origin_x, height, width)
    draw_frame_title(stdscr, origin_y, origin_x, width, "SSH Connect")
    interior_width = max(width - 2, 0)
    interior_height = max(height - 2, 0)
    if interior_width <= 0 or interior_height <= 0:
        return None

    prompt_x = origin_x + 1
    y = origin_y + 1

    # Field labels and values
    fields = [
        ("Host: ", browser.ssh_host_buffer),
        ("User: ", browser.ssh_user_buffer),
        ("Password: ", "*" * len(browser.ssh_password_buffer)),
    ]

    cursor_y = None
    cursor_x = None

    for index, (label, value) in enumerate(fields):
        if y + index >= origin_y + interior_height:
            break

        # Determine if this field is active
        is_active = (index == browser.ssh_input_field)
        attr = curses.A_BOLD if is_active else curses.A_NORMAL

        prompt_text = f"{label}{value}"
        truncated_prompt = truncate_end(prompt_text, interior_width)
        stdscr.addnstr(y + index, prompt_x, truncated_prompt.ljust(interior_width), interior_width, attr)

        # Store cursor position for active field
        if is_active:
            cursor_y = y + index
            cursor_x = prompt_x + len(label) + len(value)
            cursor_x = min(cursor_x, prompt_x + interior_width - 1)

    # Status line
    status_y = y + 4
    if status_y < origin_y + interior_height:
        status_text = "Tab: next field | Enter: connect/next | Esc: cancel"
        stdscr.addnstr(
            status_y,
            prompt_x,
            truncate_end(status_text, interior_width).ljust(interior_width),
            interior_width,
        )

    if cursor_y is not None and cursor_x is not None:
        return (cursor_y, cursor_x)
    return None


__all__ = [
    "render_mode_prompt",
    "render_help_panel",
    "render_confirmation_dialog",
    "render_rename_input",
    "render_create_input",
    "render_ssh_connect_input",
]
