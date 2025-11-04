"""Core dual pane browser logic."""

from __future__ import annotations

import curses
import subprocess
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from .colors import init_colors
from .file_operations import FileOperationsMixin
from .git_operations import GitOperationsMixin
from .input_handlers import InputHandlersMixin
from .modes import BrowserMode
from .render import render_browser
from .state import _PaneState

# Constants
OUTPUT_BUFFER_MAX_LINES = 200


class DualPaneBrowserError(Exception):
    """Raised when the dual pane browser cannot start."""


class DualPaneBrowser(InputHandlersMixin, FileOperationsMixin, GitOperationsMixin):
    """Display two directories side-by-side in a curses interface.

    This class orchestrates the main event loop and delegates responsibilities to mixins:
    - InputHandlersMixin: All keyboard input handling
    - FileOperationsMixin: File operations (copy, move, delete, rename, create)
    - GitOperationsMixin: Git operations (stage, commit, diff, log, blame)
    """

    def __init__(self, left_root: Path, right_root: Path) -> None:
        self.left = _PaneState(current_dir=left_root.expanduser().resolve())
        self.right = _PaneState(current_dir=right_root.expanduser().resolve())
        self.active_index = 0
        self.status_message: str | None = None
        self.command_buffer: str = ""
        self.command_output: List[str] = []
        self.in_command_mode: bool = False
        self.show_help: bool = False
        self.in_mode_prompt: bool = False
        self.mode: BrowserMode = BrowserMode.FILE
        self._stdscr: Optional["curses._CursesWindow"] = None  # type: ignore[name-defined]

        # Confirmation dialog state
        self.pending_action: Optional[Tuple[str, Callable[[], None]]] = None

        # Rename mode state
        self.in_rename_mode: bool = False
        self.rename_buffer: str = ""

        # Create mode state
        self.in_create_mode: bool = False
        self.create_buffer: str = ""
        self.create_is_dir: bool = False

    def browse(self) -> Tuple[Path, Path]:
        """Launch the UI and return the final directories."""
        try:
            return curses.wrapper(self._loop)
        except curses.error as err:
            raise DualPaneBrowserError("Failed to initialise curses UI.") from err

    def _loop(self, stdscr: "curses._CursesWindow") -> Tuple[Path, Path]:  # type: ignore[name-defined]
        """Main curses event loop."""
        self._stdscr = stdscr
        curses.curs_set(0)
        curses.use_default_colors()
        stdscr.nodelay(False)
        stdscr.keypad(True)

        # Initialize colors
        init_colors()

        for pane in (self.left, self.right):
            pane.refresh_entries(self.mode)

        try:
            while True:
                render_browser(self, stdscr)
                key = stdscr.getch()
                if key in (ord("q"), ord("Q")) and not self.in_command_mode and not self.pending_action:
                    break
                if self.pending_action:
                    handled = self._handle_confirmation_key(key)
                elif self.in_rename_mode:
                    handled = self._handle_rename_key(key)
                elif self.in_create_mode:
                    handled = self._handle_create_key(key)
                elif self.in_mode_prompt:
                    handled = self._handle_mode_selection_key(key)
                elif self.in_command_mode:
                    handled = self._handle_command_key(key)
                else:
                    handled = self._handle_navigation_key(key)
                if not handled and key not in (ord("q"), ord("Q")):
                    self.status_message = "Unhandled keypress."
        finally:
            self._stdscr = None

        return self.left.current_dir, self.right.current_dir

    def _dismiss_overlays(self) -> None:
        """Dismiss help and mode selection overlays."""
        self.show_help = False
        self.in_mode_prompt = False

    def _run_external(self, command: List[str]) -> None:
        """Temporarily suspend curses to run an external command."""
        if self._stdscr is None:
            self.status_message = "Cannot run external command."
            return
        curses.endwin()
        try:
            subprocess.run(command, check=False)
            self.status_message = f"Ran {' '.join(command)}"
        except (OSError, subprocess.SubprocessError) as err:
            self.status_message = f"Command failed: {err}"
        finally:
            self._stdscr.refresh()
            self.show_help = False
            self.in_mode_prompt = False
            for pane in (self.left, self.right):
                pane.refresh_entries(self.mode)

    def _refresh_panes(self) -> None:
        """Refresh both panes to reflect filesystem changes."""
        for pane in (self.left, self.right):
            pane.refresh_entries(self.mode)

    @property
    def _active_pane(self) -> _PaneState:
        """Get the currently active pane."""
        return self.left if self.active_index == 0 else self.right

    @property
    def _inactive_pane(self) -> _PaneState:
        """Get the currently inactive pane."""
        return self.right if self.active_index == 0 else self.left


__all__ = ["DualPaneBrowser", "DualPaneBrowserError"]
