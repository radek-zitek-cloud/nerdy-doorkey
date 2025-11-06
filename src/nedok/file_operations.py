"""File operation methods for the dual pane browser."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Callable, List

if TYPE_CHECKING:
    from .state import _PaneEntry


class FileOperationsMixin:
    """Mixin providing file operations (copy, move, delete, rename, create)."""

    def _get_entry_name(self, entry: "_PaneEntry") -> str:
        """Get the name of an entry, handling both local and remote paths."""
        if entry.is_remote:
            return PurePosixPath(str(entry.path)).name
        else:
            return Path(entry.path).name

    def _delete_entry(self) -> None:
        entry = self._active_pane.selected_entry()
        if entry is None or entry.is_parent:
            self.status_message = "Nothing to delete."
            return

        entry_name = self._get_entry_name(entry)

        def do_delete() -> None:
            try:
                if entry.is_remote:
                    # Remote delete
                    pane = self._active_pane
                    if not pane.ssh_connection:
                        self.status_message = "No SSH connection."
                        return

                    if entry.is_dir:
                        # Delete directory recursively on remote
                        self._delete_remote_dir_recursive(pane.ssh_connection, str(entry.path))
                    else:
                        pane.ssh_connection.remove(str(entry.path))
                    self.status_message = f"Deleted {entry_name}."
                else:
                    # Local delete
                    if entry.is_dir:
                        shutil.rmtree(str(entry.path))
                    else:
                        Path(entry.path).unlink()
                    self.status_message = f"Deleted {entry_name}."
            except (OSError, PermissionError, shutil.Error, IOError) as err:
                self.status_message = f"Delete failed: {err}"
            self._refresh_panes()

        self._request_confirmation(f"Delete {entry_name}?", do_delete)

    def _delete_remote_dir_recursive(self, ssh_conn, remote_path: str) -> None:
        """Recursively delete a remote directory.

        Raises:
            IOError: If network operation fails
        """
        try:
            # List directory contents
            entries = ssh_conn.list_directory(remote_path)
        except IOError as err:
            raise IOError(f"Failed to list remote directory {remote_path}: {err}") from err

        for name, attrs in entries:
            if name in ('.', '..'):
                continue

            full_path = str(PurePosixPath(remote_path) / name)

            # Check if directory
            import stat as stat_module
            if stat_module.S_ISDIR(attrs.st_mode or 0):
                # Recursively delete subdirectory
                try:
                    self._delete_remote_dir_recursive(ssh_conn, full_path)
                except IOError as err:
                    raise IOError(f"Failed to delete remote subdirectory {full_path}: {err}") from err
            else:
                # Delete file
                try:
                    ssh_conn.remove(full_path)
                except IOError as err:
                    raise IOError(f"Failed to delete remote file {full_path}: {err}") from err

        # Finally, remove the empty directory
        try:
            ssh_conn.rmdir(remote_path)
        except IOError as err:
            raise IOError(f"Failed to remove remote directory {remote_path}: {err}") from err

    def _copy_entry(self) -> None:
        """Copy entry from active pane to inactive pane."""
        entry = self._active_pane.selected_entry()
        if entry is None or entry.is_parent:
            self.status_message = "Nothing to copy."
            return

        entry_name = self._get_entry_name(entry)

        # Check destination existence
        if self._inactive_pane.is_remote:
            dest_path = str(PurePosixPath(str(self._inactive_pane.current_dir)) / entry_name)
            if self._inactive_pane.ssh_connection and self._inactive_pane.ssh_connection.exists(dest_path):
                self.status_message = f"Destination exists: {entry_name}"
                return
        else:
            dest_path = Path(self._inactive_pane.current_dir) / entry_name
            if dest_path.exists():
                self.status_message = f"Destination exists: {entry_name}"
                return

        try:
            # Determine copy operation based on source/dest types
            src_remote = entry.is_remote
            dst_remote = self._inactive_pane.is_remote

            if not src_remote and not dst_remote:
                # Local to local
                self._copy_local_to_local(entry, dest_path)
            elif src_remote and not dst_remote:
                # Remote to local
                self._copy_remote_to_local(entry, dest_path)
            elif not src_remote and dst_remote:
                # Local to remote
                self._copy_local_to_remote(entry, dest_path)
            else:
                # Remote to remote
                self._copy_remote_to_remote(entry, dest_path)

            self.status_message = f"Copied {entry_name}."
            self._refresh_panes()
        except (OSError, PermissionError, shutil.Error, IOError) as err:
            self.status_message = f"Copy failed: {err}"

    def _move_entry(self) -> None:
        """Move entry from active pane to inactive pane (copy + delete)."""
        entry = self._active_pane.selected_entry()
        if entry is None or entry.is_parent:
            self.status_message = "Nothing to move."
            return

        entry_name = self._get_entry_name(entry)

        # First copy, then delete on success
        try:
            # Save original status message handler
            original_msg = self.status_message

            # Perform copy
            self._copy_entry()

            # Check if copy succeeded (status won't have "failed" in it)
            if self.status_message and "failed" in self.status_message.lower():
                return

            # Copy succeeded, now delete source
            if entry.is_remote:
                pane = self._active_pane
                if not pane.ssh_connection:
                    self.status_message = "Move failed: No SSH connection."
                    return

                if entry.is_dir:
                    self._delete_remote_dir_recursive(pane.ssh_connection, str(entry.path))
                else:
                    pane.ssh_connection.remove(str(entry.path))
            else:
                # Local delete
                if entry.is_dir:
                    shutil.rmtree(str(entry.path))
                else:
                    Path(entry.path).unlink()

            self.status_message = f"Moved {entry_name}."
            self._refresh_panes()
        except (OSError, PermissionError, shutil.Error, IOError) as err:
            self.status_message = f"Move failed: {err}"

    def _copy_local_to_local(self, entry: "_PaneEntry", dest_path: Path) -> None:
        """Copy from local to local."""
        if entry.is_dir:
            shutil.copytree(str(entry.path), str(dest_path))
        else:
            shutil.copy2(str(entry.path), str(dest_path))

    def _copy_remote_to_local(self, entry: "_PaneEntry", dest_path: Path) -> None:
        """Copy from remote to local via SFTP."""
        src_ssh = self._active_pane.ssh_connection
        if not src_ssh:
            raise IOError("No SSH connection for source")

        if entry.is_dir:
            # Create local directory and copy recursively
            dest_path.mkdir(parents=True, exist_ok=True)
            self._copy_remote_dir_to_local(src_ssh, str(entry.path), dest_path)
        else:
            src_ssh.get_file(str(entry.path), str(dest_path))

    def _copy_local_to_remote(self, entry: "_PaneEntry", dest_path: str) -> None:
        """Copy from local to remote via SFTP."""
        dst_ssh = self._inactive_pane.ssh_connection
        if not dst_ssh:
            raise IOError("No SSH connection for destination")

        if entry.is_dir:
            # Create remote directory and copy recursively
            dst_ssh.mkdir(dest_path)
            self._copy_local_dir_to_remote(Path(entry.path), dest_path, dst_ssh)
        else:
            dst_ssh.put_file(str(entry.path), dest_path)

    def _copy_remote_to_remote(self, entry: "_PaneEntry", dest_path: str) -> None:
        """Copy from remote to remote via local temp."""
        # Use temp directory as intermediary
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir) / self._get_entry_name(entry)

            # Download from source
            self._copy_remote_to_local(entry, tmp_path)

            # Upload to destination
            dst_ssh = self._inactive_pane.ssh_connection
            if not dst_ssh:
                raise IOError("No SSH connection for destination")

            if entry.is_dir:
                dst_ssh.mkdir(dest_path)
                self._copy_local_dir_to_remote(tmp_path, dest_path, dst_ssh)
            else:
                dst_ssh.put_file(str(tmp_path), dest_path)

    def _copy_remote_dir_to_local(self, ssh_conn, remote_path: str, local_path: Path) -> None:
        """Recursively copy remote directory to local.

        Raises:
            IOError: If network operation fails
            OSError: If local file operation fails
        """
        try:
            entries = ssh_conn.list_directory(remote_path)
        except IOError as err:
            raise IOError(f"Failed to list remote directory {remote_path}: {err}") from err

        for name, attrs in entries:
            if name in ('.', '..'):
                continue

            remote_item = str(PurePosixPath(remote_path) / name)
            local_item = local_path / name

            import stat as stat_module
            if stat_module.S_ISDIR(attrs.st_mode or 0):
                try:
                    local_item.mkdir(exist_ok=True)
                except OSError as err:
                    raise OSError(f"Failed to create local directory {local_item}: {err}") from err
                try:
                    self._copy_remote_dir_to_local(ssh_conn, remote_item, local_item)
                except (IOError, OSError) as err:
                    raise IOError(f"Failed to copy remote directory {remote_item}: {err}") from err
            else:
                try:
                    ssh_conn.get_file(remote_item, str(local_item))
                except IOError as err:
                    raise IOError(f"Failed to copy remote file {remote_item}: {err}") from err

    def _copy_local_dir_to_remote(self, local_path: Path, remote_path: str, ssh_conn) -> None:
        """Recursively copy local directory to remote.

        Raises:
            IOError: If network operation fails
            OSError: If local file operation fails
        """
        try:
            items = list(local_path.iterdir())
        except OSError as err:
            raise OSError(f"Failed to list local directory {local_path}: {err}") from err

        for item in items:
            remote_item = str(PurePosixPath(remote_path) / item.name)

            if item.is_dir():
                try:
                    ssh_conn.mkdir(remote_item)
                except IOError as err:
                    raise IOError(f"Failed to create remote directory {remote_item}: {err}") from err
                try:
                    self._copy_local_dir_to_remote(item, remote_item, ssh_conn)
                except (IOError, OSError) as err:
                    raise IOError(f"Failed to copy local directory {item}: {err}") from err
            else:
                try:
                    ssh_conn.put_file(str(item), remote_item)
                except IOError as err:
                    raise IOError(f"Failed to copy local file {item}: {err}") from err

    def _view_file(self) -> None:
        """View file (download to temp if remote)."""
        entry = self._active_pane.selected_entry()
        if entry is None or entry.is_dir or entry.is_parent:
            self.status_message = "Select a file to view."
            return

        viewer = os.environ.get("PAGER", "less")

        if entry.is_remote:
            # Download to temp file and view
            pane = self._active_pane
            if not pane.ssh_connection:
                self.status_message = "No SSH connection."
                return

            try:
                # Create temp file with same extension
                entry_name = self._get_entry_name(entry)
                suffix = Path(entry_name).suffix
                with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as tmp:
                    tmp_path = tmp.name

                # Download file
                pane.ssh_connection.get_file(str(entry.path), tmp_path)

                # View temp file
                self._run_external([viewer, tmp_path])

                # Clean up
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            except (IOError, OSError) as err:
                self.status_message = f"View failed: {err}"
        else:
            # Local file
            self._run_external([viewer, str(entry.path)])

    def _open_in_editor(self) -> None:
        """Edit file (download to temp if remote, upload after editing)."""
        entry = self._active_pane.selected_entry()
        if entry is None or entry.is_dir or entry.is_parent:
            self.status_message = "Select a file to edit."
            return

        editor = os.environ.get("EDITOR", "vi")

        if entry.is_remote:
            # Download to temp file, edit, upload back
            pane = self._active_pane
            if not pane.ssh_connection:
                self.status_message = "No SSH connection."
                return

            try:
                # Create temp file with same extension
                entry_name = self._get_entry_name(entry)
                suffix = Path(entry_name).suffix
                with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as tmp:
                    tmp_path = tmp.name

                # Download file
                pane.ssh_connection.get_file(str(entry.path), tmp_path)

                # Get original modification time
                orig_stat = os.stat(tmp_path)
                orig_mtime = orig_stat.st_mtime

                # Edit temp file
                self._run_external([editor, tmp_path])

                # Check if file was modified
                new_stat = os.stat(tmp_path)
                if new_stat.st_mtime > orig_mtime:
                    # Upload modified file back
                    pane.ssh_connection.put_file(tmp_path, str(entry.path))
                    self.status_message = f"Uploaded changes to {entry_name}."
                    self._refresh_panes()
                else:
                    self.status_message = "No changes made."

                # Clean up
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            except (IOError, OSError) as err:
                self.status_message = f"Edit failed: {err}"
        else:
            # Local file
            self._run_external([editor, str(entry.path)])

    def _start_rename(self) -> None:
        """Start rename mode for the selected entry."""
        entry = self._active_pane.selected_entry()
        if entry is None or entry.is_parent:
            self.status_message = "Select an item to rename."
            return

        self.in_rename_mode = True
        self.rename_buffer = self._get_entry_name(entry)
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

        try:
            if entry.is_remote:
                # Remote rename
                pane = self._active_pane
                if not pane.ssh_connection:
                    self.status_message = "No SSH connection."
                    return

                old_path = PurePosixPath(str(entry.path))
                new_path = old_path.parent / new_name

                # Check if destination exists
                if pane.ssh_connection.exists(str(new_path)):
                    self.status_message = f"'{new_name}' already exists."
                    return

                pane.ssh_connection.rename(str(old_path), str(new_path))
                self.status_message = f"Renamed to '{new_name}'."
            else:
                # Local rename
                old_path = Path(entry.path)
                new_path = old_path.parent / new_name

                if new_path.exists():
                    self.status_message = f"'{new_name}' already exists."
                    return

                old_path.rename(new_path)
                self.status_message = f"Renamed to '{new_name}'."

            self._refresh_panes()
        except (OSError, PermissionError, IOError) as err:
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

        pane = self._active_pane

        try:
            if pane.is_remote:
                # Remote create
                if not pane.ssh_connection:
                    self.status_message = "No SSH connection."
                    return

                target = str(PurePosixPath(str(pane.current_dir)) / name)

                # Check if exists
                if pane.ssh_connection.exists(target):
                    self.status_message = f"'{name}' already exists."
                    return

                if self.create_is_dir:
                    pane.ssh_connection.mkdir(target)
                    self.status_message = f"Created directory '{name}'."
                else:
                    # Create empty file by opening and closing
                    with pane.ssh_connection.open(target, 'w') as f:
                        pass
                    self.status_message = f"Created file '{name}'."
            else:
                # Local create
                target = Path(pane.current_dir) / name

                if target.exists():
                    self.status_message = f"'{name}' already exists."
                    return

                if self.create_is_dir:
                    target.mkdir(parents=True)
                    self.status_message = f"Created directory '{name}'."
                else:
                    target.touch()
                    self.status_message = f"Created file '{name}'."

            self._refresh_panes()
        except (OSError, PermissionError, IOError) as err:
            self.status_message = f"Create failed: {err}"


__all__ = ["FileOperationsMixin"]
