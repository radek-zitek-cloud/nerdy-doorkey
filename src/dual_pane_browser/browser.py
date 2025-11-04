"""Core dual pane browser logic."""

from __future__ import annotations

import curses
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from .modes import BrowserMode, ALL_MODES
from .render import render_browser
from .state import _PaneEntry, _PaneState


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
        self.show_help: bool = False
        self.in_mode_prompt: bool = False
        self.mode: BrowserMode = BrowserMode.FILE
        self._stdscr: Optional["curses._CursesWindow"] = None  # type: ignore[name-defined]

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

        for pane in (self.left, self.right):
            pane.refresh_entries(self.mode)

        try:
            while True:
                render_browser(self, stdscr)
                key = stdscr.getch()
                if key in (ord("q"), ord("Q")) and not self.in_command_mode:
                    break
                if self.in_mode_prompt:
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
        if key_code in (curses.KEY_RIGHT, ord("l"), ord("\t")):
            self.active_index = 1
            return True
        if key_code in (curses.KEY_LEFT, curses.KEY_BTAB):
            self.active_index = 0
            return True
        if key_code in (ord("h"), ord("H")):
            self.show_help = not self.show_help
            self.in_mode_prompt = False
            self.in_command_mode = False
            self.status_message = "Help displayed." if self.show_help else None
            return True
        if key_code in (ord("m"), ord("M")):
            self.in_mode_prompt = True
            self.show_help = False
            self.in_command_mode = False
            self.status_message = "Select a mode."
            return True
        if key_code == ord(":") and not self.show_help and not self.in_mode_prompt:
            self._start_command_mode()
            return True
        if key_code in (curses.KEY_ENTER, ord("\n"), ord("\r")):
            before_dir = pane.current_dir
            try:
                pane.enter_selected(self.mode)
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
                pane.refresh_entries(self.mode)
                self.status_message = None
            except PermissionError as err:
                self.status_message = str(err)
            return True
        if self._handle_mode_command(key_code):
            return True
        if key_code == curses.KEY_RESIZE:
            return True
        return False

    def _handle_mode_selection_key(self, key_code: int) -> bool:
        """Handle mode selection popup keys."""
        if key_code == 27:  # ESC
            self.in_mode_prompt = False
            self.status_message = "Mode selection cancelled."
            return True
        if 0 <= key_code <= 255:
            char = chr(key_code).lower()
            for candidate in ALL_MODES:
                initial = candidate.label[0].lower()
                if char == initial:
                    if candidate is not self.mode:
                        self.mode = candidate
                        for pane in (self.left, self.right):
                            pane.refresh_entries(self.mode)
                        self.status_message = f"Switched to {self.mode.label} mode."
                    else:
                        self.status_message = f"Already in {self.mode.label} mode."
                    self.in_mode_prompt = False
                    return True
        return False

    def _handle_mode_command(self, key_code: int) -> bool:
        """Execute commands tied to the active mode."""
        if key_code in (ord("d"), ord("D")):
            self._delete_entry()
            return True
        if key_code in (ord("c"), ord("C")):
            self._copy_entry()
            return True
        if key_code in (ord("t"), ord("T")):
            self._move_entry()
            return True
        if key_code in (ord("v"), ord("V")):
            self._view_file()
            return True
        if key_code in (ord("e"), ord("E")):
            self._open_in_editor()
            return True
        if key_code in (ord("a"), ord("A")):
            self._git_stage_entry()
            return True
        if key_code in (ord("u"), ord("U")):
            self._git_unstage_entry()
            return True
        if key_code in (ord("r"), ord("R")):
            self._git_restore_entry()
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

    def _delete_entry(self) -> None:
        entry = self._active_pane.selected_entry()
        if entry is None or entry.is_parent:
            self.status_message = "Nothing to delete."
            return
        try:
            if entry.is_dir:
                shutil.rmtree(entry.path)
            else:
                entry.path.unlink()
            self.status_message = f"Deleted {entry.path.name}."
        except Exception as err:  # pragma: no cover - safety fallback
            self.status_message = f"Delete failed: {err}"
        self._refresh_panes()

    def _move_entry(self) -> None:
        entry = self._active_pane.selected_entry()
        if entry is None or entry.is_parent:
            self.status_message = "Nothing to move."
            return
        target_dir = self._inactive_pane.current_dir
        destination = target_dir / entry.path.name
        if destination.exists():
            self.status_message = f"Destination exists: {destination.name}"
            return
        try:
            shutil.move(str(entry.path), str(destination))
            self.status_message = f"Moved to {destination.parent.name}/"
        except Exception as err:  # pragma: no cover
            self.status_message = f"Move failed: {err}"
        self._refresh_panes()

    def _copy_entry(self) -> None:
        entry = self._active_pane.selected_entry()
        if entry is None or entry.is_parent:
            self.status_message = "Nothing to copy."
            return
        target_dir = self._inactive_pane.current_dir
        destination = target_dir / entry.path.name
        if destination.exists():
            self.status_message = f"Destination exists: {destination.name}"
            return
        try:
            if entry.is_dir:
                shutil.copytree(entry.path, destination)
            else:
                shutil.copy2(entry.path, destination)
            self.status_message = f"Copied to {destination.parent.name}/"
        except Exception as err:  # pragma: no cover
            self.status_message = f"Copy failed: {err}"
        self._refresh_panes()

    def _open_in_editor(self) -> None:
        entry = self._active_pane.selected_entry()
        if entry is None or entry.is_dir or entry.is_parent:
            self.status_message = "Select a file to edit."
            return
        editor = os.environ.get("EDITOR", "vi")
        self._run_external([editor, str(entry.path)])

    def _view_file(self) -> None:
        entry = self._active_pane.selected_entry()
        if entry is None or entry.is_dir or entry.is_parent:
            self.status_message = "Select a file to view."
            return
        viewer = os.environ.get("PAGER", "less")
        self._run_external([viewer, str(entry.path)])

    def _git_stage_entry(self) -> None:
        entry = self._active_pane.selected_entry()
        if entry is None or entry.is_parent:
            self.status_message = "Select an item to stage."
            return
        context = self._git_context(entry)
        if context is None:
            return
        repo_root, relative_path = context
        rel_str = str(relative_path)
        if self._run_git_command(repo_root, ["add", "--", rel_str]):
            self.status_message = f"Staged {rel_str}."
            self._refresh_panes()

    def _git_unstage_entry(self) -> None:
        entry = self._active_pane.selected_entry()
        if entry is None or entry.is_parent:
            self.status_message = "Select an item to unstage."
            return
        if entry.git_status == "??":
            self.status_message = "File is untracked; nothing to unstage."
            return
        context = self._git_context(entry)
        if context is None:
            return
        repo_root, relative_path = context
        rel_str = str(relative_path)
        if self._run_git_command(repo_root, ["restore", "--staged", "--", rel_str]):
            self.status_message = f"Unstaged {rel_str}."
            self._refresh_panes()

    def _git_restore_entry(self) -> None:
        entry = self._active_pane.selected_entry()
        if entry is None or entry.is_parent:
            self.status_message = "Select an item to restore."
            return
        context = self._git_context(entry)
        if context is None:
            return
        repo_root, relative_path = context
        rel_str = str(relative_path)
        if self._run_git_command(
            repo_root,
            ["restore", "--worktree", "--source=HEAD", "--", rel_str],
        ):
            self.status_message = f"Restored {rel_str} to HEAD."
            self._refresh_panes()

    def _git_context(self, entry: _PaneEntry) -> Tuple[Path, Path] | None:
        try:
            resolved = entry.path.resolve()
        except OSError as err:
            self.status_message = f"Cannot resolve path: {err}"
            return None
        search_dir = resolved if entry.is_dir else resolved.parent
        try:
            result = subprocess.run(
                ["git", "-C", str(search_dir), "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as err:
            self.status_message = f"Git not available: {err}"
            return None
        root_text = result.stdout.strip()
        if result.returncode != 0 or not root_text:
            self.status_message = "Not inside a git repository."
            return None
        repo_root = Path(root_text)
        try:
            relative = resolved.relative_to(repo_root)
        except ValueError:
            self.status_message = "Item is outside the repository."
            return None
        return repo_root, relative

    def _run_git_command(self, repo_root: Path, arguments: List[str]) -> bool:
        try:
            result = subprocess.run(
                ["git", "-C", str(repo_root), *arguments],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as err:
            self.status_message = f"Git command failed: {err}"
            return False
        if result.returncode != 0:
            stderr = result.stderr.strip() or result.stdout.strip() or "unknown error"
            self.status_message = f"Git command failed: {stderr}"
            return False
        return True

    def _run_external(self, command: List[str]) -> None:
        """Temporarily suspend curses to run an external command."""
        if self._stdscr is None:
            self.status_message = "Cannot run external command."
            return
        curses.endwin()
        try:
            subprocess.run(command, check=False)
            self.status_message = f"Ran {' '.join(command)}"
        except Exception as err:  # pragma: no cover
            self.status_message = f"Command failed: {err}"
        finally:
            self._stdscr.refresh()
            self.show_help = False
            self.in_mode_prompt = False
            for pane in (self.left, self.right):
                pane.refresh_entries(self.mode)

    def _refresh_panes(self) -> None:
        for pane in (self.left, self.right):
            pane.refresh_entries(self.mode)

    @property
    def _active_pane(self) -> _PaneState:
        return self.left if self.active_index == 0 else self.right

    @property
    def _inactive_pane(self) -> _PaneState:
        return self.right if self.active_index == 0 else self.left


__all__ = ["DualPaneBrowser", "DualPaneBrowserError"]
