"""File operation methods for the dual pane browser."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Callable, List

if TYPE_CHECKING:
    from .state import _PaneEntry


class FileOperationsMixin:
    """Mixin providing file operations (copy, move, delete, rename, create)."""

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


__all__ = ["FileOperationsMixin"]
