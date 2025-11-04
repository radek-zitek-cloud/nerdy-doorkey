"""Core dual pane browser logic."""

from __future__ import annotations

import curses
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from .modes import BrowserMode, ALL_MODES
from .render import render_browser
from .state import _PaneEntry, _PaneState

# Constants
OUTPUT_BUFFER_MAX_LINES = 200
PAGE_SCROLL_LINES = 5


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
            pane.move_cursor(-PAGE_SCROLL_LINES)
            return True
        if key_code in (curses.KEY_NPAGE,):
            pane.move_cursor(PAGE_SCROLL_LINES)
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
            self.in_rename_mode = False
            self.in_create_mode = False
            self.status_message = "Help displayed." if self.show_help else None
            return True
        if key_code in (ord("n"),) and not self.show_help:
            self._dismiss_overlays()
            self._start_rename()
            return True
        if key_code in (ord("f"),) and not self.show_help:
            self._dismiss_overlays()
            self._create_file()
            return True
        if key_code in (ord("F"),) and not self.show_help:
            self._dismiss_overlays()
            self._create_directory()
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
            self._dismiss_overlays()
            self._delete_entry()
            return True
        if key_code in (ord("c"), ord("C")):
            self._dismiss_overlays()
            self._copy_entry()
            return True
        if key_code in (ord("t"), ord("T")):
            self._dismiss_overlays()
            self._move_entry()
            return True
        if key_code in (ord("v"), ord("V")):
            self._dismiss_overlays()
            self._view_file()
            return True
        if key_code in (ord("e"), ord("E")):
            self._dismiss_overlays()
            self._open_in_editor()
            return True
        if key_code in (ord("a"), ord("A")):
            self._dismiss_overlays()
            self._git_stage_entry()
            return True
        if key_code in (ord("u"), ord("U")):
            self._dismiss_overlays()
            self._git_unstage_entry()
            return True
        if key_code in (ord("r"), ord("R")):
            self._dismiss_overlays()
            self._git_restore_entry()
            return True
        if key_code in (ord("g"), ord("G")):
            self._dismiss_overlays()
            self._git_diff_entry()
            return True
        if key_code in (ord("o"), ord("O")):
            self._dismiss_overlays()
            self._git_commit()
            return True
        if key_code in (ord("l"), ord("L")):
            self._dismiss_overlays()
            self._git_log_entry()
            return True
        if key_code in (ord("b"), ord("B")):
            self._dismiss_overlays()
            self._git_blame_entry()
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

    def _handle_confirmation_key(self, key_code: int) -> bool:
        """Handle y/n confirmation."""
        if self.pending_action is None:
            return False

        if key_code in (ord('y'), ord('Y')):
            message, action = self.pending_action
            self.pending_action = None
            action()
            return True
        elif key_code in (ord('n'), ord('N'), 27):  # n, N, or ESC
            self.pending_action = None
            self.status_message = "Cancelled."
            return True
        return False

    def _handle_rename_key(self, key_code: int) -> bool:
        """Handle key presses during rename."""
        if key_code == curses.KEY_RESIZE:
            return True
        if key_code == 27:  # ESC
            self.in_rename_mode = False
            self.rename_buffer = ""
            self.status_message = "Rename cancelled."
            return True
        if key_code in (curses.KEY_ENTER, ord("\n"), ord("\r")):
            self._execute_rename()
            return True
        if key_code in (curses.KEY_BACKSPACE, 127, 8):
            self.rename_buffer = self.rename_buffer[:-1]
            return True
        if 0 <= key_code <= 255 and chr(key_code).isprintable():
            self.rename_buffer += chr(key_code)
            return True
        return False

    def _handle_create_key(self, key_code: int) -> bool:
        """Handle key presses during file/dir creation."""
        if key_code == curses.KEY_RESIZE:
            return True
        if key_code == 27:  # ESC
            self.in_create_mode = False
            self.create_buffer = ""
            self.status_message = "Create cancelled."
            return True
        if key_code in (curses.KEY_ENTER, ord("\n"), ord("\r")):
            self._execute_create()
            return True
        if key_code in (curses.KEY_BACKSPACE, 127, 8):
            self.create_buffer = self.create_buffer[:-1]
            return True
        if 0 <= key_code <= 255 and chr(key_code).isprintable():
            self.create_buffer += chr(key_code)
            return True
        return False

    def _request_confirmation(self, message: str, action: Callable[[], None]) -> None:
        """Show confirmation prompt for destructive action."""
        self.pending_action = (message, action)
        self.status_message = f"{message} (y/n)"

    def _start_rename(self) -> None:
        """Start rename mode for the selected entry."""
        entry = self._active_pane.selected_entry()
        if entry is None or entry.is_parent:
            self.status_message = "Select an item to rename."
            return
        self.in_rename_mode = True
        self.rename_buffer = entry.path.name
        self.status_message = "Enter new name (Enter to confirm, Esc to cancel):"

    def _execute_rename(self) -> None:
        """Perform the rename operation."""
        new_name = self.rename_buffer.strip()
        self.in_rename_mode = False
        self.rename_buffer = ""

        if not new_name:
            self.status_message = "Rename cancelled (empty name)."
            return

        entry = self._active_pane.selected_entry()
        if entry is None:
            return

        new_path = entry.path.parent / new_name

        if new_path.exists():
            self.status_message = f"'{new_name}' already exists."
            return

        try:
            entry.path.rename(new_path)
            self.status_message = f"Renamed to '{new_name}'."
            self._refresh_panes()
        except (OSError, PermissionError) as err:
            self.status_message = f"Rename failed: {err}"

    def _create_file(self) -> None:
        """Start create file mode."""
        self.in_create_mode = True
        self.create_buffer = ""
        self.create_is_dir = False
        self.status_message = "New file name (Enter to create, Esc to cancel):"

    def _create_directory(self) -> None:
        """Start create directory mode."""
        self.in_create_mode = True
        self.create_buffer = ""
        self.create_is_dir = True
        self.status_message = "New directory name (Enter to create, Esc to cancel):"

    def _execute_create(self) -> None:
        """Create file or directory."""
        name = self.create_buffer.strip()
        self.in_create_mode = False
        self.create_buffer = ""

        if not name:
            self.status_message = "Cancelled (empty name)."
            return

        target = self._active_pane.current_dir / name

        if target.exists():
            self.status_message = f"'{name}' already exists."
            return

        try:
            if self.create_is_dir:
                target.mkdir(parents=True)
                self.status_message = f"Created directory '{name}'."
            else:
                target.touch()
                self.status_message = f"Created file '{name}'."
            self._refresh_panes()
        except (OSError, PermissionError) as err:
            self.status_message = f"Create failed: {err}"

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
        self.command_output = output_lines[-OUTPUT_BUFFER_MAX_LINES:]
        self.status_message = f"Command exited with code {result.returncode}."

    def _delete_entry(self) -> None:
        entry = self._active_pane.selected_entry()
        if entry is None or entry.is_parent:
            self.status_message = "Nothing to delete."
            return

        def do_delete() -> None:
            try:
                if entry.is_dir:
                    shutil.rmtree(entry.path)
                else:
                    entry.path.unlink()
                self.status_message = f"Deleted {entry.path.name}."
            except (OSError, PermissionError, shutil.Error) as err:
                self.status_message = f"Delete failed: {err}"
            self._refresh_panes()

        self._request_confirmation(f"Delete {entry.path.name}?", do_delete)

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
        except (OSError, PermissionError, shutil.Error) as err:
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
        except (OSError, PermissionError, shutil.Error) as err:
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

        def do_restore() -> None:
            if self._run_git_command(
                repo_root,
                ["restore", "--worktree", "--source=HEAD", "--", rel_str],
            ):
                self.status_message = f"Restored {rel_str} to HEAD."
                self._refresh_panes()

        self._request_confirmation(f"Restore {entry.path.name} to HEAD?", do_restore)

    def _git_diff_entry(self) -> None:
        """Show git diff in pager for better viewing."""
        entry = self._active_pane.selected_entry()
        if entry is None or entry.is_parent:
            self.status_message = "Select a file to diff."
            return
        if entry.is_dir:
            self.status_message = "Diff is only available for files."
            return
        context = self._git_context(entry)
        if context is None:
            return
        repo_root, relative_path = context
        rel_str = str(relative_path)

        # Build diff command
        if entry.git_status == "??":
            command = [
                "git",
                "-C",
                str(repo_root),
                "diff",
                "--no-index",
                "--color=always",
                "--",
                "/dev/null",
                rel_str,
            ]
        else:
            command = [
                "git",
                "-C",
                str(repo_root),
                "diff",
                "HEAD",
                "--color=always",
                "--",
                rel_str,
            ]

        try:
            # Create the diff
            diff_result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )

            if diff_result.returncode not in (0, 1):
                err_text = diff_result.stderr.strip() or "unknown error"
                self.status_message = f"Git diff failed: {err_text}"
                return

            if not diff_result.stdout.strip():
                self.status_message = f"No differences for {rel_str}."
                return

            # Write to temp file and open in pager
            with tempfile.NamedTemporaryFile(mode='w', suffix='.diff', delete=False) as f:
                f.write(diff_result.stdout)
                temp_path = f.name

            try:
                pager = os.environ.get("PAGER", "less")
                # Add -R flag for less to handle ANSI color codes
                if "less" in pager.lower():
                    pager_command = [pager, "-R", temp_path]
                else:
                    pager_command = [pager, temp_path]
                self._run_external(pager_command)
            finally:
                Path(temp_path).unlink(missing_ok=True)

        except OSError as err:
            self.status_message = f"Git diff failed: {err}"

    def _git_commit(self) -> None:
        """Create a git commit."""
        # Get repo root
        try:
            result = subprocess.run(
                ["git", "-C", str(self._active_pane.current_dir), "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as err:
            self.status_message = f"Git not available: {err}"
            return

        if result.returncode != 0:
            self.status_message = "Not in a git repository."
            return

        repo_root = Path(result.stdout.strip())

        # Check if there are staged changes
        try:
            status_result = subprocess.run(
                ["git", "-C", str(repo_root), "diff", "--cached", "--quiet"],
                check=False,
            )
            if status_result.returncode == 0:
                self.status_message = "No staged changes to commit."
                return
        except OSError:
            pass

        # Open editor for commit message
        editor = os.environ.get("EDITOR", "vi")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("\n# Enter commit message above this line\n")
            f.write("# Changes to be committed:\n")
            temp_path = f.name

        try:
            # Suspend curses and open editor
            self._run_external([editor, temp_path])

            # Read commit message
            commit_msg = Path(temp_path).read_text()
            # Remove comment lines
            lines = [l for l in commit_msg.splitlines() if not l.startswith('#')]
            commit_msg = '\n'.join(lines).strip()

            if not commit_msg:
                self.status_message = "Commit cancelled (empty message)."
                return

            # Execute commit
            result = subprocess.run(
                ["git", "-C", str(repo_root), "commit", "-m", commit_msg],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                self.status_message = "Commit created successfully."
                self._refresh_panes()
            else:
                self.status_message = f"Commit failed: {result.stderr.strip()}"

        except OSError as err:
            self.status_message = f"Commit failed: {err}"
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def _git_log_entry(self) -> None:
        """Show git log for selected file or directory."""
        entry = self._active_pane.selected_entry()
        if entry is None or entry.is_parent:
            self.status_message = "Select an item to view log."
            return

        context = self._git_context(entry)
        if context is None:
            return

        repo_root, relative_path = context
        rel_str = str(relative_path)

        pager = os.environ.get("PAGER", "less")
        command = [
            "git", "-C", str(repo_root),
            "log", "--oneline", "--decorate", "--color=always",
            "-n", "100",  # Last 100 commits
            "--", rel_str
        ]

        try:
            # Run git log and capture output
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                self.status_message = f"Git log failed: {result.stderr.strip()}"
                return

            if not result.stdout.strip():
                self.status_message = f"No commits found for {rel_str}."
                return

            # Write to temp file and open in pager
            with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
                f.write(result.stdout)
                temp_path = f.name

            try:
                # Add -R flag for less to handle ANSI color codes
                if "less" in pager.lower():
                    pager_command = [pager, "-R", temp_path]
                else:
                    pager_command = [pager, temp_path]
                self._run_external(pager_command)
            finally:
                Path(temp_path).unlink(missing_ok=True)

        except OSError as err:
            self.status_message = f"Git log failed: {err}"

    def _git_blame_entry(self) -> None:
        """Show git blame for selected file."""
        entry = self._active_pane.selected_entry()
        if entry is None or entry.is_parent or entry.is_dir:
            self.status_message = "Select a file to blame."
            return

        context = self._git_context(entry)
        if context is None:
            return

        repo_root, relative_path = context
        rel_str = str(relative_path)

        pager = os.environ.get("PAGER", "less")
        command = [
            "git", "-C", str(repo_root),
            "blame", "--color-by-age", rel_str
        ]

        try:
            # Run git blame and capture output
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                self.status_message = f"Git blame failed: {result.stderr.strip()}"
                return

            if not result.stdout.strip():
                self.status_message = f"No blame info for {rel_str}."
                return

            # Write to temp file and open in pager
            with tempfile.NamedTemporaryFile(mode='w', suffix='.blame', delete=False) as f:
                f.write(result.stdout)
                temp_path = f.name

            try:
                # Add -R flag for less to handle ANSI color codes
                if "less" in pager.lower():
                    pager_command = [pager, "-R", temp_path]
                else:
                    pager_command = [pager, temp_path]
                self._run_external(pager_command)
            finally:
                Path(temp_path).unlink(missing_ok=True)

        except OSError as err:
            self.status_message = f"Git blame failed: {err}"

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

    def _dismiss_overlays(self) -> None:
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
        for pane in (self.left, self.right):
            pane.refresh_entries(self.mode)

    @property
    def _active_pane(self) -> _PaneState:
        return self.left if self.active_index == 0 else self.right

    @property
    def _inactive_pane(self) -> _PaneState:
        return self.right if self.active_index == 0 else self.left


__all__ = ["DualPaneBrowser", "DualPaneBrowserError"]
