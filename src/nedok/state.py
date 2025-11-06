"""Directory pane state and entry models."""

from __future__ import annotations

import grp
import os
import pwd
import stat
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Dict, Iterable, List, Optional, Set, Tuple, Union

from nedok.formatting import format_size, format_timestamp
from nedok.git_status import collect_git_status
from nedok.modes import BrowserMode
from nedok.ssh_connection import SSHConnection


class PaneStateError(Exception):
    """Raised when pane state operations fail."""


def _get_owner_name(uid: int) -> str:
    """Convert UID to username, fallback to UID string."""
    try:
        return pwd.getpwuid(uid).pw_name
    except (KeyError, AttributeError):
        return str(uid)


def _get_group_name(gid: int) -> str:
    """Convert GID to group name, fallback to GID string."""
    try:
        return grp.getgrgid(gid).gr_name
    except (KeyError, AttributeError):
        return str(gid)


@dataclass
class _PaneEntry:
    path: Union[Path, str]  # Path for local, str for remote
    is_dir: bool
    is_parent: bool = False
    mode: str = ""
    size: Optional[int] = None
    modified: Optional[datetime] = None
    git_status: Optional[str] = None
    is_executable: bool = False
    is_symlink: bool = False
    is_readonly: bool = False
    is_remote: bool = False
    owner_user: Optional[str] = None
    owner_group: Optional[str] = None
    tree_depth: int = 0
    tree_parent_path: Optional[Path] = None
    tree_is_collapsed: bool = False
    tree_is_expanded: bool = False

    @property
    def display_name(self) -> str:
        """Return the text shown for the entry."""
        if self.is_parent:
            return ".."
        if self.is_remote:
            name = PurePosixPath(str(self.path)).name
        else:
            name = Path(self.path).name or str(self.path)
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
        return format_size(self.size)

    @property
    def display_modified(self) -> str:
        """Return a printable modified timestamp."""
        if self.modified is None:
            return "-"
        return format_timestamp(self.modified)

    @property
    def display_owner(self) -> str:
        """Return a printable owner string (user:group)."""
        if self.owner_user is None or self.owner_group is None:
            return "-"
        return f"{self.owner_user}:{self.owner_group}"


@dataclass
class _PaneState:
    current_dir: Union[Path, str]  # Path for local, str for remote
    cursor_index: int = 0
    scroll_offset: int = 0
    entries: List[_PaneEntry] = field(default_factory=list)
    ssh_connection: Optional[SSHConnection] = None
    tree_mode_enabled: bool = False
    tree_collapsed_paths: Set[Path] = field(default_factory=set)

    @property
    def is_remote(self) -> bool:
        """Check if this pane is connected to a remote host."""
        return self.ssh_connection is not None and self.ssh_connection.is_connected

    @property
    def current_dir_display(self) -> str:
        """Get display string for current directory."""
        if self.is_remote:
            return f"{self.ssh_connection}:{self.current_dir}"
        return str(self.current_dir)

    def refresh_entries(self, mode: BrowserMode) -> None:
        """Populate `entries` with directory contents."""
        if self.tree_mode_enabled and not self.is_remote and mode is BrowserMode.TREE:
            self._refresh_tree_entries()
            return
        if self.is_remote:
            self._refresh_remote_entries(mode)
        else:
            self._refresh_local_entries(mode)

    def _refresh_local_entries(self, mode: BrowserMode) -> None:
        """Populate entries from local directory."""
        items: List[_PaneEntry] = []
        current = Path(self.current_dir)

        if current != current.parent:
            items.append(self._build_entry(current.parent, is_parent=True))

        try:
            candidates: Iterable[Path] = sorted(
                current.iterdir(), key=self._sort_key
            )
        except PermissionError as err:
            raise PermissionError(
                f"Permission denied reading directory: {current}"
            ) from err
        except FileNotFoundError as err:
            raise FileNotFoundError(
                f"Directory not found: {current}"
            ) from err

        for entry in candidates:
            items.append(self._build_entry(entry))

        if mode is BrowserMode.GIT:
            self._attach_git_status(items)

        self.entries = items
        self.cursor_index = min(self.cursor_index, max(len(self.entries) - 1, 0))
        self.scroll_offset = min(self.scroll_offset, max(len(self.entries) - 1, 0))

    def _refresh_remote_entries(self, mode: BrowserMode) -> None:
        """Populate entries from remote directory via SSH."""
        if not self.is_remote or not self.ssh_connection:
            return

        items: List[_PaneEntry] = []
        current = PurePosixPath(str(self.current_dir))

        # Add parent directory entry if not at root
        if current != current.parent:
            items.append(self._build_remote_entry(str(current.parent), is_parent=True))

        try:
            entries = self.ssh_connection.list_directory(str(current))
            # Sort: directories first, then alphabetically
            entries.sort(key=lambda x: (0 if stat.S_ISDIR(x[1].st_mode or 0) else 1, x[0].lower()))

            for name, attrs in entries:
                if name in ('.', '..'):
                    continue
                full_path = str(current / name)
                items.append(self._build_remote_entry(full_path, attrs=attrs))

        except IOError as err:
            raise PermissionError(
                f"Error reading remote directory: {current}"
            ) from err

        # Git operations not supported for remote
        self.entries = items
        self.cursor_index = min(self.cursor_index, max(len(self.entries) - 1, 0))
        self.scroll_offset = min(self.scroll_offset, max(len(self.entries) - 1, 0))

    def _refresh_tree_entries(self) -> None:
        """Populate entries with a recursive tree of the current directory."""
        current = Path(self.current_dir)
        try:
            root = current.resolve()
        except OSError:
            root = current

        self._prune_tree_state(root)

        items: List[_PaneEntry] = []

        visited_dirs: Set[Path] = set()

        def add_children(directory: Path, depth: int) -> None:
            normalized_dir = self._normalize_tree_path(directory)
            if normalized_dir is not None:
                if normalized_dir in visited_dirs:
                    return
                visited_dirs.add(normalized_dir)

            try:
                children = sorted(directory.iterdir(), key=self._sort_key)
            except (PermissionError, FileNotFoundError, NotADirectoryError, OSError):
                return

            for child in children:
                entry = self._build_entry(child)
                entry.tree_depth = depth
                entry.tree_parent_path = directory
                normalized_child = self._normalize_tree_path(child)
                is_collapsed = (
                    normalized_child in self.tree_collapsed_paths
                    if normalized_child is not None
                    else False
                )
                can_expand = entry.is_dir and not entry.is_symlink
                entry.tree_is_collapsed = can_expand and is_collapsed
                entry.tree_is_expanded = can_expand and not is_collapsed
                items.append(entry)
                if can_expand and not is_collapsed:
                    add_children(child, depth + 1)

        add_children(root, 0)

        self.entries = items
        self.cursor_index = min(self.cursor_index, max(len(self.entries) - 1, 0))
        self.scroll_offset = min(self.scroll_offset, max(len(self.entries) - 1, 0))

    def _normalize_tree_path(self, path: Path) -> Optional[Path]:
        """Return a resolved version of `path` when possible."""
        try:
            return path.resolve()
        except (OSError, RuntimeError):
            # RuntimeError can occur for deeply nested or cyclic symlinks
            return path

    def _prune_tree_state(self, root: Path) -> None:
        """Drop cached collapsed paths that are no longer under `root`."""
        normalized_root = self._normalize_tree_path(root) or root
        filtered: Set[Path] = set()
        for candidate in self.tree_collapsed_paths:
            normalized = self._normalize_tree_path(candidate) or candidate
            try:
                parents = normalized.parents
            except AttributeError:
                continue
            if normalized == normalized_root:
                continue
            if normalized_root in parents:
                filtered.add(normalized)
        self.tree_collapsed_paths = filtered

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

    def expand_tree_at_cursor(self) -> bool:
        """Expand the currently selected directory in tree mode."""
        if not self.tree_mode_enabled:
            return False
        entry = self.selected_entry()
        if entry is None or not entry.is_dir or not isinstance(entry.path, Path):
            return False
        normalized = self._normalize_tree_path(entry.path)
        if normalized is None:
            return False
        if normalized in self.tree_collapsed_paths:
            self.tree_collapsed_paths.remove(normalized)
            return True
        return False

    def collapse_tree_at_cursor(self) -> bool:
        """Collapse the selected directory or its parent in tree mode."""
        if not self.tree_mode_enabled:
            return False

        entry = self.selected_entry()
        if entry is None:
            return False

        target_path: Optional[Path] = None
        if entry.is_dir and isinstance(entry.path, Path):
            target_path = entry.path
        elif entry.tree_parent_path is not None:
            target_path = entry.tree_parent_path

        if target_path is None:
            return False

        normalized_target = self._normalize_tree_path(target_path)
        normalized_root = self._normalize_tree_path(Path(self.current_dir)) or Path(self.current_dir)
        if normalized_target is None or normalized_target == normalized_root:
            return False
        if normalized_target not in self.tree_collapsed_paths:
            self.tree_collapsed_paths.add(normalized_target)
            return True
        return False

    def selected_entry(self) -> _PaneEntry | None:
        """Return currently highlighted entry."""
        if not self.entries:
            return None
        return self.entries[self.cursor_index]

    def enter_selected(self, mode: BrowserMode) -> None:
        """Enter the highlighted directory if possible."""
        entry = self.selected_entry()
        if entry is None:
            return
        if entry.is_dir:
            if self.is_remote:
                self.current_dir = str(entry.path)
            else:
                self.current_dir = Path(entry.path).resolve()
            self.cursor_index = 0
            self.scroll_offset = 0
            if self.tree_mode_enabled:
                self.tree_collapsed_paths.clear()
            self.refresh_entries(mode)

    def go_to_parent(self) -> None:
        """Navigate to parent directory (handles both local and remote)."""
        if self.is_remote:
            # For remote paths (strings), use PurePosixPath to get parent
            current = PurePosixPath(str(self.current_dir))
            parent = current.parent
            self.current_dir = str(parent)
        else:
            # For local paths, use Path.parent
            self.current_dir = Path(self.current_dir).parent
        self.cursor_index = 0
        self.scroll_offset = 0
        if self.tree_mode_enabled:
            self.tree_collapsed_paths.clear()

    def _build_entry(self, path: Path, *, is_parent: bool = False) -> _PaneEntry:
        """Construct a pane entry for the given path."""
        stat_info = self._stat_or_none(path)
        is_dir = self._is_dir(path, stat_info)
        mode = stat.filemode(stat_info.st_mode) if stat_info else ""
        size: Optional[int] = None
        modified: Optional[datetime] = None
        is_executable = False
        is_symlink = False
        is_readonly = False
        owner_user: Optional[str] = None
        owner_group: Optional[str] = None

        if stat_info:
            modified = datetime.fromtimestamp(stat_info.st_mtime)
            if not stat.S_ISDIR(stat_info.st_mode):
                size = stat_info.st_size

            # Check if file is a symlink
            try:
                is_symlink = path.is_symlink()
            except OSError:
                pass

            # Check if file is executable (for non-directories)
            if not is_dir:
                is_executable = bool(stat_info.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))

            # Check if file is readonly (not writable by user)
            is_readonly = not bool(stat_info.st_mode & stat.S_IWUSR)

            # Get ownership info
            owner_user = _get_owner_name(stat_info.st_uid)
            owner_group = _get_group_name(stat_info.st_gid)

        return _PaneEntry(
            path=path,
            is_dir=is_dir,
            is_parent=is_parent,
            mode=mode,
            size=size,
            modified=modified,
            is_executable=is_executable,
            is_symlink=is_symlink,
            is_readonly=is_readonly,
            is_remote=False,
            owner_user=owner_user,
            owner_group=owner_group,
        )

    def _build_remote_entry(self, path: str, *, is_parent: bool = False, attrs=None) -> _PaneEntry:
        """Construct a pane entry for a remote path."""
        if attrs is None and not is_parent and self.ssh_connection:
            try:
                attrs = self.ssh_connection.stat(path)
            except:
                attrs = None

        is_dir = False
        mode = ""
        size: Optional[int] = None
        modified: Optional[datetime] = None
        is_executable = False
        is_symlink = False
        is_readonly = False
        owner_user: Optional[str] = None
        owner_group: Optional[str] = None

        if attrs:
            is_dir = stat.S_ISDIR(attrs.st_mode or 0)
            mode = stat.filemode(attrs.st_mode) if attrs.st_mode else ""
            if not is_dir and attrs.st_size is not None:
                size = attrs.st_size
            if attrs.st_mtime is not None:
                modified = datetime.fromtimestamp(attrs.st_mtime)

            # Check if executable
            if not is_dir and attrs.st_mode:
                is_executable = bool(attrs.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))

            # Check if readonly (not writable by user)
            if attrs.st_mode:
                is_readonly = not bool(attrs.st_mode & stat.S_IWUSR)

            # Symlinks detection is limited in SFTP
            is_symlink = stat.S_ISLNK(attrs.st_mode or 0)

            # Get ownership info (remote uses numeric IDs as SFTP doesn't resolve names)
            if hasattr(attrs, 'st_uid') and attrs.st_uid is not None:
                owner_user = str(attrs.st_uid)
            if hasattr(attrs, 'st_gid') and attrs.st_gid is not None:
                owner_group = str(attrs.st_gid)
        else:
            # If we don't have attrs, assume it's a directory if is_parent
            is_dir = is_parent

        return _PaneEntry(
            path=path,
            is_dir=is_dir,
            is_parent=is_parent,
            mode=mode,
            size=size,
            modified=modified,
            is_executable=is_executable,
            is_symlink=is_symlink,
            is_readonly=is_readonly,
            is_remote=True,
            owner_user=owner_user,
            owner_group=owner_group,
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

    def _attach_git_status(self, entries: List[_PaneEntry]) -> None:
        """Populate git status for entries when in git mode."""
        if not entries:
            return
        repo_root, status_map = collect_git_status(self.current_dir)
        if not status_map or repo_root is None:
            return
        repo_root = repo_root.resolve()
        normalized_map: Dict[Path, str] = {}
        for abs_path, status in status_map.items():
            try:
                normalized = abs_path.resolve()
            except OSError:
                continue
            normalized_map[normalized] = status

        for entry in entries:
            try:
                resolved_path = entry.path.resolve()
            except OSError:
                continue
            status = normalized_map.get(resolved_path)
            if status is None and entry.is_dir:
                status = normalized_map.get(resolved_path / "")
            entry.git_status = status


__all__ = ["_PaneEntry", "_PaneState", "PaneStateError"]
