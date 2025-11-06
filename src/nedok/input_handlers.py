"""Input handling methods for the dual pane browser."""

from __future__ import annotations

import curses
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable, List, Optional

from nedok.modes import ALL_MODES, BrowserMode

if TYPE_CHECKING:
    pass

# Constants
PAGE_SCROLL_LINES = 5


@dataclass(frozen=True)
class _TextInputModeConfig:
    """Configuration describing how to handle buffered text input modes."""

    active_flag: str
    buffer_attr: str
    cancel_message: str
    submit_action: Callable[[], None]


@dataclass
class _PendingAction:
    """Track confirmation prompts with optional decline behavior."""

    message: str
    confirm_action: Callable[[], None]
    cancel_action: Optional[Callable[[], None]] = None
    cancel_message: str = "Cancelled."

    def __iter__(self):
        """Allow legacy tuple-style unpacking in tests."""
        yield self.message
        yield self.confirm_action

    def __getitem__(self, index: int):
        """Support tuple-style indexing for compatibility."""
        return (self.message, self.confirm_action)[index]


@dataclass
class _AvailableSSHCredentials:
    """Describe credentials discovered for a host."""

    host: str
    username: str
    password: str
    sources: List[str]
    saved_credentials: Optional[dict[str, str]]


class InputHandlersMixin:
    """Mixin providing all keyboard input handlers."""

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
        if key_code in (ord("\t"),):
            # Tab toggles between panes
            self.active_index = 1 - self.active_index
            return True
        if key_code in (curses.KEY_RIGHT,):
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
        if key_code == ord("+") and self._expand_tree_cursor():
            return True
        if key_code == ord("-") and self._collapse_tree_cursor():
            return True
        if key_code in (curses.KEY_BACKSPACE, 127, 8):
            try:
                pane.go_to_parent()
                self._refresh_pane(pane)
                self.status_message = None
            except PermissionError as err:
                self.status_message = str(err)
            return True
        if key_code == ord("s"):
            self._dismiss_overlays()
            self._refresh_active_pane()
            return True
        if key_code == ord("S"):
            self._dismiss_overlays()
            self._start_ssh_connect()
            return True
        if key_code in (ord("x"), ord("X")):
            self._dismiss_overlays()
            self._disconnect_ssh()
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
                            self._refresh_pane(pane)
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
        mode = _TextInputModeConfig(
            active_flag="in_command_mode",
            buffer_attr="command_buffer",
            cancel_message="Command cancelled.",
            submit_action=self._execute_command,
        )
        return self._handle_text_input_mode(key_code, mode)

    def _handle_confirmation_key(self, key_code: int) -> bool:
        """Handle y/n confirmation."""
        if self.pending_action is None:
            return False

        pending = self.pending_action
        if key_code in (ord('y'), ord('Y')):
            self.pending_action = None
            pending.confirm_action()
            return True
        if key_code in (ord('n'), ord('N'), 27):  # n, N, or ESC
            self.pending_action = None
            if pending.cancel_action:
                pending.cancel_action()
            else:
                self.status_message = pending.cancel_message
            return True
        return False

    def _handle_rename_key(self, key_code: int) -> bool:
        """Handle key presses during rename."""
        mode = _TextInputModeConfig(
            active_flag="in_rename_mode",
            buffer_attr="rename_buffer",
            cancel_message="Rename cancelled.",
            submit_action=self._execute_rename,
        )
        return self._handle_text_input_mode(key_code, mode)

    def _handle_create_key(self, key_code: int) -> bool:
        """Handle key presses during file/dir creation."""
        mode = _TextInputModeConfig(
            active_flag="in_create_mode",
            buffer_attr="create_buffer",
            cancel_message="Create cancelled.",
            submit_action=self._execute_create,
        )
        return self._handle_text_input_mode(key_code, mode)

    def _request_confirmation(
        self,
        message: str,
        action: Callable[[], None],
        *,
        on_decline: Optional[Callable[[], None]] = None,
        cancel_message: str = "Cancelled.",
    ) -> None:
        """Show confirmation prompt with optional decline handling."""
        self.pending_action = _PendingAction(
            message=message,
            confirm_action=action,
            cancel_action=on_decline,
            cancel_message=cancel_message,
        )
        self.status_message = f"{message} (y/n)"

    def _refresh_active_pane(self) -> None:
        """Refresh the active pane to reload directory contents."""
        pane = self._active_pane
        try:
            self._refresh_pane(pane)
            self.status_message = f"Refreshed {pane.current_dir}"
        except PermissionError as err:
            self.status_message = str(err)
        except FileNotFoundError as err:
            self.status_message = str(err)

    def _expand_tree_cursor(self) -> bool:
        """Expand the selected directory when tree mode is active."""
        pane = self._active_pane
        if self.mode is not BrowserMode.TREE or not getattr(pane, "tree_mode_enabled", False):
            return False
        if pane.expand_tree_at_cursor():
            self._refresh_pane(pane)
            return True
        return False

    def _collapse_tree_cursor(self) -> bool:
        """Collapse the selected directory or its parent when in tree mode."""
        pane = self._active_pane
        if self.mode is not BrowserMode.TREE or not getattr(pane, "tree_mode_enabled", False):
            return False
        if pane.collapse_tree_at_cursor():
            self._refresh_pane(pane)
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

        # Handle local or remote command execution
        pane = self._active_pane
        if pane.is_remote and pane.ssh_connection:
            # Execute command on remote host
            try:
                stdin, stdout, stderr = pane.ssh_connection.client.exec_command(
                    f"cd {pane.current_dir} && {command}"
                )
                stdout_text = stdout.read().decode('utf-8', errors='replace')
                stderr_text = stderr.read().decode('utf-8', errors='replace')
                exit_code = stdout.channel.recv_exit_status()

                self.command_output = self._format_command_output(stdout_text, stderr_text)
                self.status_message = f"Remote command exited with code {exit_code}."
            except Exception as err:
                self.command_output = [f"Failed to run remote command: {err}"]
                self.status_message = "Remote command execution failed."
        else:
            # Execute command locally
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=pane.current_dir,
                    capture_output=True,
                    text=True,
                    env=os.environ.copy(),
                )
            except OSError as err:
                self.command_output = [f"Failed to run command: {err}"]
                self.status_message = "Command execution failed."
                return

            self.command_output = self._format_command_output(result.stdout, result.stderr)
            self.status_message = f"Command exited with code {result.returncode}."

    def _start_ssh_connect(self) -> None:
        """Start SSH connection input mode."""
        self.in_ssh_connect_mode = True
        self.ssh_host_buffer = ""
        self.ssh_user_buffer = os.getenv("USER", "user")
        self.ssh_password_buffer = ""
        self.ssh_input_field = 0
        self.ssh_available_credentials = None
        self.status_message = "SSH: Will try agent keys first, then password. 🔐 Use SSH agent for security!"

    def _handle_ssh_connect_key(self, key_code: int) -> bool:
        """Handle key presses during SSH connection setup."""
        if key_code == curses.KEY_RESIZE:
            return True
        if key_code == 27:  # ESC
            self.in_ssh_connect_mode = False
            self.ssh_host_buffer = ""
            self.ssh_user_buffer = ""
            self.ssh_password_buffer = ""
            self.ssh_input_field = 0
            self.status_message = "SSH connection cancelled."
            return True
        if key_code in (curses.KEY_ENTER, ord("\n"), ord("\r")):
            if self.ssh_input_field == 0 and self._handle_host_field_exit():
                return True
            if self.ssh_input_field < 2:
                self.ssh_input_field += 1
                return True
            # Final field - execute connection
            self._execute_ssh_connect()
            return True
        if key_code == ord("\t"):
            # Tab to next field
            if self.ssh_input_field == 0 and self._handle_host_field_exit():
                return True
            self.ssh_input_field = (self.ssh_input_field + 1) % 3
            return True
        if key_code in (curses.KEY_BACKSPACE, 127, 8):
            if self.ssh_input_field == 0:
                self.ssh_host_buffer = self.ssh_host_buffer[:-1]
            elif self.ssh_input_field == 1:
                self.ssh_user_buffer = self.ssh_user_buffer[:-1]
            elif self.ssh_input_field == 2:
                self.ssh_password_buffer = self.ssh_password_buffer[:-1]
            return True
        if 0 <= key_code <= 255 and chr(key_code).isprintable():
            if self.ssh_input_field == 0:
                self.ssh_host_buffer += chr(key_code)
            elif self.ssh_input_field == 1:
                self.ssh_user_buffer += chr(key_code)
            elif self.ssh_input_field == 2:
                self.ssh_password_buffer += chr(key_code)
            return True
        return False

    def _execute_ssh_connect(self, auto_add_host_key: bool = False) -> None:
        """Execute SSH connection.

        Args:
            auto_add_host_key: If True, automatically accept unknown host keys (after user confirmation)
        """
        from .ssh_connection import SSHConnection
        from .config import get_ssh_credentials
        import paramiko

        host = self.ssh_host_buffer.strip()
        user = self.ssh_user_buffer.strip()
        password = self.ssh_password_buffer if self.ssh_password_buffer else None

        if not host:
            self.status_message = "Host cannot be empty."
            self.in_ssh_connect_mode = False
            return

        if not user:
            user = os.getenv("USER", "user")

        try:
            # Create SSH connection
            ssh_conn = SSHConnection(hostname=host, username=user)

            # Try to connect (with or without host key auto-accept)
            ssh_conn.connect(password=password, auto_add_host_key=auto_add_host_key)

            # Set the connection on active pane
            pane = self._active_pane
            pane.ssh_connection = ssh_conn
            pane.current_dir = "/"
            pane.cursor_index = 0
            pane.scroll_offset = 0
            self._refresh_pane(pane)

            self.status_message = f"Connected to {user}@{host}"

            # Check if credentials should be saved
            saved_creds = get_ssh_credentials(host)
            if not saved_creds or saved_creds.get("username") != user or saved_creds.get("password") != password:
                # Offer to save credentials with security warning
                self.ssh_last_connection = (host, user, password or "")
                warning_msg = f"Save SSH credentials for {host}?"
                if password:
                    warning_msg += " ⚠️  WARNING: Password will be stored in PLAINTEXT!"
                else:
                    warning_msg += " (username only, use SSH agent for keys)"
                self._request_confirmation(
                    warning_msg,
                    self._save_ssh_credentials_confirmed
                )
        except paramiko.SSHException as err:
            # Check if this is an unknown host key error
            if "Unknown host key" in str(err):
                # Store connection details and prompt for host key approval
                self.ssh_pending_connection = (host, user, password)
                self._request_confirmation(
                    f"⚠️  Unknown host key for {host}! Accept and connect? (Check fingerprint first!)",
                    self._approve_host_key_and_connect
                )
            else:
                self.status_message = f"SSH connection failed: {err}"
                self.ssh_last_connection = None
        except Exception as err:
            self.status_message = f"SSH connection failed: {err}"
            self.ssh_last_connection = None
        finally:
            if not hasattr(self, 'ssh_pending_connection') or self.ssh_pending_connection is None:
                self.in_ssh_connect_mode = False
                self.ssh_host_buffer = ""
                self.ssh_user_buffer = ""
                self.ssh_password_buffer = ""
                self.ssh_input_field = 0

    def _disconnect_ssh(self) -> None:
        """Disconnect SSH connection from active pane."""
        pane = self._active_pane
        if not pane.is_remote or not pane.ssh_connection:
            self.status_message = "No SSH connection to disconnect."
            return

        try:
            pane.ssh_connection.disconnect()
            pane.ssh_connection = None
            # Return to home directory
            pane.current_dir = Path.home()
            pane.cursor_index = 0
            pane.scroll_offset = 0
            self._refresh_pane(pane)
            self.status_message = "Disconnected from SSH."
        except Exception as err:
            self.status_message = f"Error disconnecting: {err}"

    def _handle_host_field_exit(self) -> bool:
        """Check for available credentials when leaving the host field."""
        host = self.ssh_host_buffer.strip()
        if not host:
            return False

        available = self._detect_available_credentials(host)
        if not available:
            return False

        self.ssh_available_credentials = available
        source_text = self._format_credential_sources(available.sources)
        self._request_confirmation(
            f"Credentials available for {host} via {source_text}. Override them?",
            self._begin_manual_credentials_override,
            on_decline=self._connect_with_available_credentials,
            cancel_message="Connecting with existing credentials...",
        )
        return True

    def _detect_available_credentials(self, host: str) -> Optional["_AvailableSSHCredentials"]:
        """Look for saved credentials or SSH agent support."""
        from .config import get_ssh_credentials

        saved_creds = get_ssh_credentials(host)
        agent_available = bool(os.environ.get("SSH_AUTH_SOCK"))

        if not saved_creds and not agent_available:
            return None

        username = (
            (saved_creds.get("username") if saved_creds else None)
            or self.ssh_user_buffer
            or os.getenv("USER", "user")
        )
        password = saved_creds.get("password") if saved_creds else ""

        sources: List[str] = []
        if saved_creds:
            sources.append("saved config")
        if agent_available:
            sources.append("SSH agent")

        return _AvailableSSHCredentials(
            host=host,
            username=username,
            password=password or "",
            sources=sources,
            saved_credentials=saved_creds,
        )

    @staticmethod
    def _format_credential_sources(sources: List[str]) -> str:
        """Return a readable description of credential sources."""
        if not sources:
            return "unknown source"
        if len(sources) == 1:
            return sources[0]
        if len(sources) == 2:
            return f"{sources[0]} and {sources[1]}"
        return ", ".join(sources[:-1]) + f", and {sources[-1]}"

    def _begin_manual_credentials_override(self) -> None:
        """Allow the user to enter new credentials instead of saved ones."""
        if self.ssh_available_credentials and self.ssh_available_credentials.saved_credentials:
            saved_username = self.ssh_available_credentials.saved_credentials.get("username")
            if saved_username:
                self.ssh_user_buffer = saved_username
        self.ssh_password_buffer = ""
        self.ssh_input_field = 1
        self.ssh_available_credentials = None
        self.status_message = "Override selected. Enter SSH username."

    def _connect_with_available_credentials(self) -> None:
        """Connect immediately using discovered credentials."""
        available = self.ssh_available_credentials
        if not available:
            self.status_message = "No credentials available; enter them manually."
            return

        self.ssh_user_buffer = available.username or (self.ssh_user_buffer or os.getenv("USER", "user"))
        self.ssh_password_buffer = available.password or ""
        self.ssh_available_credentials = None
        self.status_message = "Connecting with available credentials..."
        self._execute_ssh_connect()

    def _approve_host_key_and_connect(self) -> None:
        """Retry SSH connection after user approves unknown host key."""
        if not hasattr(self, 'ssh_pending_connection') or not self.ssh_pending_connection:
            return

        host, user, password = self.ssh_pending_connection
        self.ssh_pending_connection = None

        # Restore connection buffers and retry with auto_add_host_key=True
        self.ssh_host_buffer = host
        self.ssh_user_buffer = user
        self.ssh_password_buffer = password or ""
        self._execute_ssh_connect(auto_add_host_key=True)

    def _save_ssh_credentials_confirmed(self) -> None:
        """Save SSH credentials after user confirms."""
        from .config import save_ssh_credentials

        if not self.ssh_last_connection:
            return

        host, user, password = self.ssh_last_connection
        save_ssh_credentials(host, user, password if password else None)
        self.ssh_last_connection = None
        if password:
            self.status_message = f"⚠️  Saved credentials for {host} (password in plaintext!)"
        else:
            self.status_message = f"Saved username for {host}"

    def _handle_text_input_mode(self, key_code: int, mode: _TextInputModeConfig) -> bool:
        """Shared handler for simple buffered text input modes."""
        if key_code == curses.KEY_RESIZE:
            return True
        if key_code == 27:  # ESC
            setattr(self, mode.active_flag, False)
            setattr(self, mode.buffer_attr, "")
            self.status_message = mode.cancel_message
            return True
        if key_code in (curses.KEY_ENTER, ord("\n"), ord("\r")):
            mode.submit_action()
            return True
        if key_code in (curses.KEY_BACKSPACE, 127, 8):
            current_value = getattr(self, mode.buffer_attr)
            setattr(self, mode.buffer_attr, current_value[:-1])
            return True
        if 0 <= key_code <= 255 and chr(key_code).isprintable():
            current_value = getattr(self, mode.buffer_attr)
            setattr(self, mode.buffer_attr, current_value + chr(key_code))
            return True
        return False

    def _format_command_output(self, stdout_text: str, stderr_text: str) -> List[str]:
        """Combine stdout/stderr text and truncate to fit the UI buffer."""
        output_lines: List[str] = []
        if stdout_text:
            output_lines.extend(stdout_text.rstrip("\n").splitlines())
        if stderr_text:
            if output_lines:
                output_lines.append("--- stderr ---")
            output_lines.extend(stderr_text.rstrip("\n").splitlines())

        if not output_lines:
            output_lines = ["<no output>"]
        return self._trim_output_for_display(output_lines)

    def _trim_output_for_display(self, output_lines: List[str]) -> List[str]:
        """Ensure command output stays within the UI buffer size."""
        from .browser import OUTPUT_BUFFER_MAX_LINES

        if len(output_lines) <= OUTPUT_BUFFER_MAX_LINES:
            return output_lines

        truncated_count = len(output_lines) - OUTPUT_BUFFER_MAX_LINES
        return [
            f"... [truncated {truncated_count} lines] ...",
            "",
            *output_lines[-OUTPUT_BUFFER_MAX_LINES:],
        ]


__all__ = ["InputHandlersMixin"]
