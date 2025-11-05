"""Input handling methods for the dual pane browser."""

from __future__ import annotations

import curses
import os
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Callable, List

from .modes import ALL_MODES

if TYPE_CHECKING:
    pass

# Constants
PAGE_SCROLL_LINES = 5


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
        if key_code in (curses.KEY_RIGHT, ord("\t")):
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

    def _refresh_active_pane(self) -> None:
        """Refresh the active pane to reload directory contents."""
        pane = self._active_pane
        try:
            pane.refresh_entries(self.mode)
            self.status_message = f"Refreshed {pane.current_dir}"
        except PermissionError as err:
            self.status_message = str(err)
        except FileNotFoundError as err:
            self.status_message = str(err)

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

                output_lines: List[str] = []
                if stdout_text:
                    output_lines.extend(stdout_text.rstrip("\n").splitlines())
                if stderr_text:
                    if output_lines:
                        output_lines.append("--- stderr ---")
                    output_lines.extend(stderr_text.rstrip("\n").splitlines())

                if not output_lines:
                    output_lines = ["<no output>"]

                from .browser import OUTPUT_BUFFER_MAX_LINES
                self.command_output = output_lines[-OUTPUT_BUFFER_MAX_LINES:]
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
            from .browser import OUTPUT_BUFFER_MAX_LINES
            self.command_output = output_lines[-OUTPUT_BUFFER_MAX_LINES:]
            self.status_message = f"Command exited with code {result.returncode}."

    def _start_ssh_connect(self) -> None:
        """Start SSH connection input mode."""
        self.in_ssh_connect_mode = True
        self.ssh_host_buffer = ""
        self.ssh_user_buffer = os.getenv("USER", "user")
        self.ssh_password_buffer = ""
        self.ssh_input_field = 0
        self.status_message = "Enter SSH connection details"

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
            if self.ssh_input_field < 2:
                # Move to next field
                self.ssh_input_field += 1
                return True
            else:
                # Final field - execute connection
                self._execute_ssh_connect()
                return True
        if key_code == ord("\t"):
            # Tab to next field
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

    def _execute_ssh_connect(self) -> None:
        """Execute SSH connection."""
        from .ssh_connection import SSHConnection

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

            # Try to connect
            ssh_conn.connect(password=password)

            # Set the connection on active pane
            pane = self._active_pane
            pane.ssh_connection = ssh_conn
            pane.current_dir = "/"
            pane.cursor_index = 0
            pane.scroll_offset = 0
            pane.refresh_entries(self.mode)

            self.status_message = f"Connected to {user}@{host}"
        except Exception as err:
            self.status_message = f"SSH connection failed: {err}"
        finally:
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
            pane.refresh_entries(self.mode)
            self.status_message = "Disconnected from SSH."
        except Exception as err:
            self.status_message = f"Error disconnecting: {err}"


__all__ = ["InputHandlersMixin"]
