"""Core dual pane browser logic."""

from __future__ import annotations

import curses
import os
import subprocess
from pathlib import Path
from typing import List, Tuple

from .render import render_browser
from .state import _PaneState


class DualPaneBrowserError(Exception):
    """Raised when the dual pane browser cannot start."""


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
            render_browser(self, stdscr)
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


__all__ = ["DualPaneBrowser", "DualPaneBrowserError"]
