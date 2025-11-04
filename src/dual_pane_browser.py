"""Dual-pane terminal directory browser built with curses."""

from __future__ import annotations

import curses
import os
import stat
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


class DualPaneBrowserError(Exception):
    """Raised when the dual pane browser cannot start."""


@dataclass
class _PaneEntry:
    path: Path
    is_dir: bool
    is_parent: bool = False
    mode: str = ""
    size: Optional[int] = None

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
        return self._format_size(self.size)

    @staticmethod
    def _format_size(size: int) -> str:
        """Return a human-readable size using binary prefixes."""
        units = ["B", "K", "M", "G", "T", "P", "E", "Z", "Y"]
        value = float(size)
        index = 0
        while value >= 1024 and index < len(units) - 1:
            value /= 1024
            index += 1
        unit = units[index]
        if unit == "B":
            return f"{int(value)}{unit}"
        formatted = f"{value:.1f}".rstrip("0").rstrip(".")
        return f"{formatted}{unit}"


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
            parent_entry = self._build_entry(self.current_dir.parent, is_parent=True)
            items.append(parent_entry)

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
        if stat_info and not stat.S_ISDIR(stat_info.st_mode):
            size = stat_info.st_size

        return _PaneEntry(
            path=path,
            is_dir=is_dir,
            is_parent=is_parent,
            mode=mode,
            size=size,
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


class DualPaneBrowser:
    """Display two directories side-by-side in a curses interface."""

    def __init__(self, left_root: Path, right_root: Path) -> None:
        self.left = _PaneState(current_dir=left_root.expanduser().resolve())
        self.right = _PaneState(current_dir=right_root.expanduser().resolve())
        self.active_index = 0
        self.status_message: str | None = None
        self.command_buffer: str = ""
        self.command_output: List[str] = []
        self.in_command_mode: bool = False

    def browse(self) -> Tuple[Path, Path]:
        """Launch the UI and return the final directories."""
        try:
            return curses.wrapper(self._loop)
        except curses.error as err:
            raise DualPaneBrowserError("Failed to initialise curses UI.") from err

    def _loop(self, stdscr: "curses._CursesWindow") -> Tuple[Path, Path]:  # type: ignore[name-defined]
        """Main curses event loop."""
        curses.curs_set(0)
        curses.use_default_colors()
        stdscr.nodelay(False)
        stdscr.keypad(True)

        for pane in (self.left, self.right):
            pane.refresh_entries()

        while True:
            self._render(stdscr)
            key = stdscr.getch()
            if self.in_command_mode:
                handled = self._handle_command_key(key)
            else:
                if key in (ord("q"), ord("Q")):
                    break
                handled = self._handle_navigation_key(key)
            if not handled:
                self.status_message = "Unhandled keypress."

        return self.left.current_dir, self.right.current_dir

    def _handle_navigation_key(self, key_code: int) -> bool:
        """Handle navigation keys while not in command mode."""
        pane = self._active_pane
        if key_code in (curses.KEY_UP, ord("k")):
            pane.move_cursor(-1)
            return True
        if key_code in (curses.KEY_DOWN, ord("j")):
            pane.move_cursor(1)
            return True
        if key_code in (curses.KEY_PPAGE,):
            pane.move_cursor(-5)
            return True
        if key_code in (curses.KEY_NPAGE,):
            pane.move_cursor(5)
            return True
        if key_code == ord(":"):
            self._start_command_mode()
            return True
        if key_code in (curses.KEY_RIGHT, ord("l"), ord("\t")):
            self.active_index = 1
            return True
        if key_code in (curses.KEY_LEFT, ord("h")):
            self.active_index = 0
            return True
        if key_code in (curses.KEY_ENTER, ord("\n"), ord("\r")):
            before_dir = pane.current_dir
            try:
                pane.enter_selected()
                self.status_message = None
            except PermissionError as err:
                self.status_message = str(err)
            except FileNotFoundError as err:
                self.status_message = str(err)
            if before_dir != pane.current_dir:
                self.status_message = None
            return True
        if key_code in (curses.KEY_BACKSPACE, 127, 8):
            pane.current_dir = pane.current_dir.parent
            pane.cursor_index = 0
            pane.scroll_offset = 0
            try:
                pane.refresh_entries()
                self.status_message = None
            except PermissionError as err:
                self.status_message = str(err)
            return True
        if key_code == curses.KEY_RESIZE:
            return True
        return False

    def _handle_command_key(self, key_code: int) -> bool:
        """Handle key presses while capturing a shell command."""
        if key_code == curses.KEY_RESIZE:
            return True
        if key_code == 27:  # ESC
            self.in_command_mode = False
            self.command_buffer = ""
            self.status_message = "Command cancelled."
            return True
        if key_code in (curses.KEY_ENTER, ord("\n"), ord("\r")):
            self._execute_command()
            return True
        if key_code in (curses.KEY_BACKSPACE, 127, 8):
            self.command_buffer = self.command_buffer[:-1]
            return True
        if 0 <= key_code <= 255 and chr(key_code).isprintable():
            self.command_buffer += chr(key_code)
            return True
        return False

    def _start_command_mode(self) -> None:
        """Switch to command entry mode."""
        self.in_command_mode = True
        self.command_buffer = ""
        self.status_message = "Enter a command and press Enter."

    def _execute_command(self) -> None:
        """Run the buffered command and capture its output."""
        command = self.command_buffer.strip()
        self.in_command_mode = False
        self.command_buffer = ""
        if not command:
            self.status_message = "No command entered."
            return
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self._active_pane.current_dir,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
            )
        except OSError as err:
            self.command_output = [f"Failed to run command: {err}"]
            self.status_message = "Command execution failed."
            return

        output_lines: List[str] = []
        if result.stdout:
            output_lines.extend(result.stdout.rstrip("\n").splitlines())
        if result.stderr:
            if output_lines:
                output_lines.append("--- stderr ---")
            output_lines.extend(result.stderr.rstrip("\n").splitlines())

        if not output_lines:
            output_lines = ["<no output>"]

        # Bound output length to avoid overflowing the UI.
        self.command_output = output_lines[-200:]
        self.status_message = f"Command exited with code {result.returncode}."

    @property
    def _active_pane(self) -> _PaneState:
        return self.left if self.active_index == 0 else self.right

    def _render(self, stdscr: "curses._CursesWindow") -> None:  # type: ignore[name-defined]
        height, width = stdscr.getmaxyx()
        stdscr.erase()

        if height < 9 or width < 40:
            stdscr.addstr(0, 0, "Terminal too small for browser.")
            stdscr.refresh()
            return

        bottom_height = max(height // 3, 4)
        top_height = height - bottom_height
        if top_height < 5:
            stdscr.addstr(0, 0, "Terminal height insufficient for layout.")
            stdscr.refresh()
            return

        pane_width = width // 2
        right_width = width - pane_width

        browser_entry_rows = max(top_height - 3, 0)
        self.left.ensure_cursor_visible(browser_entry_rows)
        self.right.ensure_cursor_visible(browser_entry_rows)

        self._render_browser_pane(
            stdscr,
            pane=self.left,
            origin_y=0,
            origin_x=0,
            height=top_height,
            width=pane_width,
            is_right=False,
        )
        self._render_browser_pane(
            stdscr,
            pane=self.right,
            origin_y=0,
            origin_x=pane_width,
            height=top_height,
            width=right_width,
            is_right=True,
        )

        command_cursor = self._render_command_area(
            stdscr,
            origin_y=top_height,
            origin_x=0,
            height=bottom_height,
            width=width,
        )

        try:
            curses.curs_set(1 if self.in_command_mode else 0)
        except curses.error:
            pass

        if self.in_command_mode and command_cursor is not None:
            try:
                stdscr.move(*command_cursor)
            except curses.error:
                pass

        stdscr.refresh()

    def _render_browser_pane(
        self,
        stdscr: "curses._CursesWindow",  # type: ignore[name-defined]
        *,
        pane: _PaneState,
        origin_y: int,
        origin_x: int,
        height: int,
        width: int,
        is_right: bool,
    ) -> None:
        """Render a single pane within the provided bounds."""
        if height < 3 or width < 6:
            return

        self._draw_frame(stdscr, origin_y, origin_x, height, width)
        self._draw_frame_title(stdscr, origin_y, origin_x, width, str(pane.current_dir))

        interior_width = max(width - 2, 0)
        interior_height = max(height - 2, 0)
        if interior_width <= 0 or interior_height <= 0:
            return

        name_width, mode_width, size_width = self._determine_column_widths(interior_width)
        header_y = origin_y + 1
        name_x = origin_x + 1
        mode_x = name_x + name_width + 1
        size_x = mode_x + mode_width + 1

        header_attr = curses.A_BOLD
        stdscr.addnstr(
            header_y,
            name_x,
            self._truncate("Name", name_width).ljust(name_width),
            name_width,
            header_attr,
        )
        stdscr.addnstr(
            header_y,
            mode_x,
            self._truncate("Mode", mode_width).ljust(mode_width),
            mode_width,
            header_attr,
        )
        stdscr.addnstr(
            header_y,
            size_x,
            self._truncate("Size", size_width).rjust(size_width),
            size_width,
            header_attr,
        )

        viewport_height = max(interior_height - 1, 0)
        entries = pane.entries[pane.scroll_offset : pane.scroll_offset + viewport_height]
        is_active_pane = (self.active_index == 0 and not is_right) or (
            self.active_index == 1 and is_right
        )

        for index, entry in enumerate(entries):
            y = header_y + 1 + index
            absolute_index = pane.scroll_offset + index
            base_attrs = curses.A_NORMAL
            if is_active_pane and absolute_index == pane.cursor_index:
                base_attrs |= curses.A_REVERSE
            name_attrs = base_attrs | (curses.A_BOLD if entry.is_dir else 0)

            name_text = self._truncate(entry.display_name, name_width)
            mode_text = self._truncate(entry.display_mode, mode_width)
            size_text = self._truncate(entry.display_size, size_width)

            stdscr.addnstr(y, name_x, name_text.ljust(name_width), name_width, name_attrs)
            stdscr.addnstr(y, mode_x, mode_text.ljust(mode_width), mode_width, base_attrs)
            stdscr.addnstr(y, size_x, size_text.rjust(size_width), size_width, base_attrs)

    def _render_command_area(
        self,
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

        self._draw_frame(stdscr, origin_y, origin_x, height, width)
        self._draw_frame_title(stdscr, origin_y, origin_x, width, "Command Console")

        interior_width = max(width - 2, 0)
        interior_height = max(height - 2, 0)
        if interior_width <= 0 or interior_height <= 0:
            return None

        prompt_y = origin_y + 1
        prompt_x = origin_x + 1
        prompt_prefix = "CMD> " if self.in_command_mode else "cmd> "
        prompt_text = f"{prompt_prefix}{self.command_buffer}"
        truncated_prompt = self._truncate_end(prompt_text, interior_width)
        stdscr.addnstr(prompt_y, prompt_x, truncated_prompt.ljust(interior_width), interior_width)

        status_y = prompt_y + 1
        status_text = self.status_message or "Press : to enter command mode. q to quit."
        stdscr.addnstr(
            status_y,
            prompt_x,
            self._truncate_end(status_text, interior_width).ljust(interior_width),
            interior_width,
        )

        output_start = status_y + 1
        available_rows = interior_height - 2
        if available_rows > 0:
            output_lines = self.command_output[-available_rows:] if self.command_output else []
            for offset in range(available_rows):
                y = output_start + offset
                if offset < len(output_lines):
                    line = output_lines[offset]
                    stdscr.addnstr(
                        y,
                        prompt_x,
                        self._truncate_end(line, interior_width).ljust(interior_width),
                        interior_width,
                    )
                else:
                    stdscr.addnstr(y, prompt_x, " " * interior_width, interior_width)

        if not self.in_command_mode:
            return None

        cursor_x = prompt_x + len(prompt_prefix) + len(self.command_buffer)
        max_cursor_x = prompt_x + interior_width - 1
        if cursor_x > max_cursor_x:
            cursor_x = max_cursor_x
        return (prompt_y, cursor_x)

    def _determine_column_widths(self, interior_width: int) -> Tuple[int, int, int]:
        """Compute dynamic column widths for the browser panes."""
        min_col_width = 4
        mode_width = min(10, max(min_col_width, interior_width // 6))
        size_width = min(12, max(min_col_width, interior_width // 6))

        remaining = interior_width - (mode_width + size_width + 2)
        if remaining < min_col_width:
            deficit = min_col_width - remaining
            reduction = min(mode_width - min_col_width, deficit)
            mode_width -= reduction
            deficit -= reduction
            reduction = min(size_width - min_col_width, deficit)
            size_width -= reduction
            remaining = interior_width - (mode_width + size_width + 2)

        name_width = max(min_col_width, remaining)
        return name_width, mode_width, size_width

    def _draw_frame(
        self,
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
            stdscr.addch(top, left, "+")
            stdscr.addch(top, right, "+")
            stdscr.addch(bottom, left, "+")
            stdscr.addch(bottom, right, "+")

            for x_axis in range(left + 1, right):
                stdscr.addch(top, x_axis, "-")
                stdscr.addch(bottom, x_axis, "-")

            for y_axis in range(top + 1, bottom):
                stdscr.addch(y_axis, left, "|")
                stdscr.addch(y_axis, right, "|")
        except curses.error:
            pass

    def _draw_frame_title(
        self,
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
        truncated = self._truncate_end(title, available)
        try:
            stdscr.addnstr(
                origin_y, origin_x + 1, truncated.ljust(available), available, curses.A_BOLD
            )
        except curses.error:
            pass

    @staticmethod
    def _truncate(text: str, max_width: int) -> str:
        """Truncate text to fit within max_width, appending ellipsis if needed."""
        if max_width <= 0:
            return ""
        if len(text) <= max_width:
            return text
        if max_width <= 3:
            return text[:max_width]
        return text[: max_width - 3] + "..."

    @staticmethod
    def _truncate_end(text: str, max_width: int) -> str:
        """Truncate text from the end to fit within max_width."""
        if max_width <= 0:
            return ""
        if len(text) <= max_width:
            return text
        return text[-max_width:]
