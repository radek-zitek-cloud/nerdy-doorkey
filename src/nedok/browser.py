"""Core dual pane browser logic."""

from __future__ import annotations

import curses
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Callable, List, Optional, Tuple

from .colors import init_colors
from .file_operations import FileOperationsMixin
from .git_operations import GitOperationsMixin
from .input_handlers import InputHandlersMixin
from .modes import BrowserMode
from .render import render_browser
from .state import _PaneState

# Constants
OUTPUT_BUFFER_MAX_LINES = 200

if TYPE_CHECKING:
    from .input_handlers import _PendingAction, _AvailableSSHCredentials


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
        self.pending_action: Optional["_PendingAction"] = None

        # Rename mode state
        self.in_rename_mode: bool = False
        self.rename_buffer: str = ""

        # Create mode state
        self.in_create_mode: bool = False
        self.create_buffer: str = ""
        self.create_is_dir: bool = False

        # SSH connection mode state
        self.in_ssh_connect_mode: bool = False
        self.ssh_host_buffer: str = ""
        self.ssh_user_buffer: str = ""
        self.ssh_password_buffer: str = ""
        self.ssh_input_field: int = 0  # 0=host, 1=user, 2=password
        self.ssh_last_connection: Optional[Tuple[str, str, str]] = None  # (host, user, pass) for save prompt
        self.ssh_pending_connection: Optional[Tuple[str, str, Optional[str]]] = None  # (host, user, pass) for host key approval
        self.ssh_available_credentials: Optional["_AvailableSSHCredentials"] = None

    def auto_reconnect_ssh(self, left_ssh: Optional[dict] = None, right_ssh: Optional[dict] = None) -> tuple[bool, bool]:
        """Attempt to auto-reconnect SSH sessions from saved state.

        Args:
            left_ssh: Left pane SSH info dict (hostname, username, remote_directory)
            right_ssh: Right pane SSH info dict (hostname, username, remote_directory)

        Returns:
            Tuple of (left_connected, right_connected) booleans
        """
        from .ssh_connection import SSHConnection
        from .config import get_ssh_credentials

        left_connected = False
        right_connected = False

        # Try left pane reconnection
        if left_ssh:
            try:
                hostname = left_ssh["hostname"]
                username = left_ssh["username"]
                remote_dir = left_ssh["remote_directory"]

                # Try to get credentials (for password auth)
                creds = get_ssh_credentials(hostname)
                password = creds.get("password") if creds else None

                # Attempt connection (SSH agent will be tried first automatically)
                ssh_conn = SSHConnection(hostname=hostname, username=username)
                ssh_conn.connect(password=password, auto_add_host_key=True)  # Auto-add for saved sessions

                # Set up pane
                self.left.ssh_connection = ssh_conn
                self.left.current_dir = remote_dir
                self.left.cursor_index = 0
                self.left.scroll_offset = 0
                left_connected = True

            except Exception:
                # Silently fail - will use local directory as fallback
                pass

        # Try right pane reconnection
        if right_ssh:
            try:
                hostname = right_ssh["hostname"]
                username = right_ssh["username"]
                remote_dir = right_ssh["remote_directory"]

                # Try to get credentials
                creds = get_ssh_credentials(hostname)
                password = creds.get("password") if creds else None

                # Attempt connection
                ssh_conn = SSHConnection(hostname=hostname, username=username)
                ssh_conn.connect(password=password, auto_add_host_key=True)

                # Set up pane
                self.right.ssh_connection = ssh_conn
                self.right.current_dir = remote_dir
                self.right.cursor_index = 0
                self.right.scroll_offset = 0
                right_connected = True

            except Exception:
                # Silently fail - will use local directory as fallback
                pass

        return left_connected, right_connected

    def browse(self) -> Tuple[Path, Path, Optional[dict], Optional[dict]]:
        """Launch the UI and return the final directories and SSH connection info.

        Returns:
            Tuple of (left_dir, right_dir, left_ssh_info, right_ssh_info)
            where ssh_info is dict with {hostname, username, remote_directory} or None
        """
        try:
            return curses.wrapper(self._loop)
        except curses.error as err:
            raise DualPaneBrowserError("Failed to initialise curses UI.") from err

    def _loop(self, stdscr: "curses._CursesWindow") -> Tuple[Path, Path, Optional[dict], Optional[dict]]:  # type: ignore[name-defined]
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

                # Check if we're in any modal input mode where 'q' should be treated as regular input
                in_modal_input = (
                    self.in_command_mode or
                    self.pending_action or
                    self.in_ssh_connect_mode or
                    self.in_rename_mode or
                    self.in_create_mode or
                    self.in_mode_prompt
                )

                # Only quit if 'q' is pressed and we're not in any modal input mode
                if key in (ord("q"), ord("Q")) and not in_modal_input:
                    break

                if self.pending_action:
                    handled = self._handle_confirmation_key(key)
                elif self.in_ssh_connect_mode:
                    handled = self._handle_ssh_connect_key(key)
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

        # Collect SSH connection info if present
        left_ssh = None
        if self.left.is_remote and self.left.ssh_connection:
            left_ssh = {
                "hostname": self.left.ssh_connection.hostname,
                "username": self.left.ssh_connection.username,
                "remote_directory": str(self.left.current_dir),
            }

        right_ssh = None
        if self.right.is_remote and self.right.ssh_connection:
            right_ssh = {
                "hostname": self.right.ssh_connection.hostname,
                "username": self.right.ssh_connection.username,
                "remote_directory": str(self.right.current_dir),
            }

        # Convert to Path for return (remote connections return their local starting point)
        left_dir = Path(self.left.current_dir) if not self.left.is_remote else Path.cwd()
        right_dir = Path(self.right.current_dir) if not self.right.is_remote else Path.cwd()
        return left_dir, right_dir, left_ssh, right_ssh

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
            # Wait for user to press a key before returning to browser
            print("\nPress any key to continue...", end='', flush=True)
            import sys
            import tty
            import termios
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
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
