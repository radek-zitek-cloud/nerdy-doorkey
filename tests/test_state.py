"""Tests for pane state and entry models."""

from datetime import datetime
from pathlib import Path

from nedok.state import _PaneEntry, _PaneState, _get_owner_name, _get_group_name
from nedok.modes import BrowserMode


def test_pane_entry_display_name_parent():
    """Test that parent entry displays as '..'."""
    entry = _PaneEntry(path=Path("/"), is_dir=True, is_parent=True)
    assert entry.display_name == ".."


def test_pane_entry_display_name_directory():
    """Test that directories have trailing slash."""
    entry = _PaneEntry(path=Path("/tmp/mydir"), is_dir=True)
    assert entry.display_name == "mydir/"


def test_pane_entry_display_name_file():
    """Test that files have no trailing slash."""
    entry = _PaneEntry(path=Path("/tmp/file.txt"), is_dir=False)
    assert entry.display_name == "file.txt"


def test_pane_entry_display_name_remote():
    """Test that remote paths are handled correctly."""
    entry = _PaneEntry(path="/home/user/file.txt", is_dir=False, is_remote=True)
    assert entry.display_name == "file.txt"

    entry = _PaneEntry(path="/home/user/dir", is_dir=True, is_remote=True)
    assert entry.display_name == "dir/"


def test_pane_entry_display_mode():
    """Test mode display."""
    entry = _PaneEntry(path=Path("/tmp/file"), is_dir=False, mode="rw-r--r--")
    assert entry.display_mode == "rw-r--r--"

    # Empty mode shows placeholder
    entry = _PaneEntry(path=Path("/tmp/file"), is_dir=False)
    assert entry.display_mode == "?????????"


def test_pane_entry_display_size():
    """Test size display formatting."""
    entry = _PaneEntry(path=Path("/tmp/file"), is_dir=False, size=1024)
    assert entry.display_size == "1K"

    entry = _PaneEntry(path=Path("/tmp/file"), is_dir=False, size=512)
    assert entry.display_size == "512B"

    # None shows dash
    entry = _PaneEntry(path=Path("/tmp/file"), is_dir=False, size=None)
    assert entry.display_size == "-"


def test_pane_entry_display_modified():
    """Test modified timestamp display."""
    timestamp = datetime(2024, 1, 15, 14, 30)
    entry = _PaneEntry(path=Path("/tmp/file"), is_dir=False, modified=timestamp)
    assert entry.display_modified == "Jan 15 14:30"

    # None shows dash
    entry = _PaneEntry(path=Path("/tmp/file"), is_dir=False, modified=None)
    assert entry.display_modified == "-"


def test_pane_entry_display_owner():
    """Test owner display."""
    entry = _PaneEntry(
        path=Path("/tmp/file"),
        is_dir=False,
        owner_user="alice",
        owner_group="users"
    )
    assert entry.display_owner == "alice:users"

    # None shows dash
    entry = _PaneEntry(path=Path("/tmp/file"), is_dir=False)
    assert entry.display_owner == "-"


def test_pane_entry_tree_properties():
    """Test tree-related properties."""
    entry = _PaneEntry(
        path=Path("/tmp/dir/subdir"),
        is_dir=True,
        tree_depth=2,
        tree_is_collapsed=True
    )
    assert entry.tree_depth == 2
    assert entry.tree_is_collapsed is True
    assert entry.tree_is_expanded is False


def test_get_owner_name_valid_uid():
    """Test getting owner name from valid UID."""
    # UID 0 should be root on most systems
    import os
    current_uid = os.getuid()
    name = _get_owner_name(current_uid)
    assert isinstance(name, str)
    assert len(name) > 0


def test_get_owner_name_invalid_uid():
    """Test getting owner name from invalid UID returns UID string."""
    # Use a very high UID that likely doesn't exist
    name = _get_owner_name(999999)
    assert name == "999999"


def test_get_group_name_valid_gid():
    """Test getting group name from valid GID."""
    import os
    current_gid = os.getgid()
    name = _get_group_name(current_gid)
    assert isinstance(name, str)
    assert len(name) > 0


def test_get_group_name_invalid_gid():
    """Test getting group name from invalid GID returns GID string."""
    # Use a very high GID that likely doesn't exist
    name = _get_group_name(999999)
    assert name == "999999"


def test_pane_state_initialization(tmp_path):
    """Test PaneState initializes with a directory."""
    state = _PaneState(current_dir=tmp_path)
    assert state.current_dir == tmp_path
    assert state.cursor_index == 0
    assert state.scroll_offset == 0
    assert state.entries == []
    assert state.ssh_connection is None


def test_pane_state_refresh_entries_sorting(tmp_path):
    """Test that refresh_entries sorts with directories first."""
    # Create test files and directories
    (tmp_path / "file1.txt").write_text("test")
    (tmp_path / "file2.txt").write_text("test")
    (tmp_path / "aaa_dir").mkdir()
    (tmp_path / "zzz_dir").mkdir()

    state = _PaneState(current_dir=tmp_path)
    state.refresh_entries(BrowserMode.FILE)

    # Should have parent (..) + 2 dirs + 2 files
    assert len(state.entries) == 5

    # First should be parent
    assert state.entries[0].is_parent

    # Next should be directories in alphabetical order
    assert state.entries[1].is_dir
    assert state.entries[1].display_name == "aaa_dir/"
    assert state.entries[2].is_dir
    assert state.entries[2].display_name == "zzz_dir/"

    # Then files in alphabetical order
    assert not state.entries[3].is_dir
    assert state.entries[3].display_name == "file1.txt"
    assert not state.entries[4].is_dir
    assert state.entries[4].display_name == "file2.txt"


def test_pane_state_selected_entry():
    """Test getting selected entry."""
    state = _PaneState(current_dir=Path("/tmp"))

    # No entries means no selection
    assert state.selected_entry() is None

    # Add entries
    entry1 = _PaneEntry(path=Path("/tmp/file1"), is_dir=False)
    entry2 = _PaneEntry(path=Path("/tmp/file2"), is_dir=False)
    state.entries = [entry1, entry2]

    # Default cursor at 0
    assert state.selected_entry() == entry1

    # Move cursor
    state.cursor_index = 1
    assert state.selected_entry() == entry2


def test_pane_state_git_status_integration(tmp_path):
    """Test that git status is collected when in git mode."""
    # This test requires a git repo
    import subprocess
    try:
        subprocess.run(
            ["git", "init"],
            cwd=tmp_path,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=tmp_path,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            check=True,
            capture_output=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Git not available, skip test
        return

    # Create an untracked file
    test_file = tmp_path / "untracked.txt"
    test_file.write_text("test")

    state = _PaneState(current_dir=tmp_path)
    state.refresh_entries(BrowserMode.GIT)

    # Find the untracked file entry
    for entry in state.entries:
        if entry.path == test_file:
            assert entry.git_status == "??"
            break
    else:
        assert False, "Untracked file not found in entries"


def test_pane_entry_readonly_detection(tmp_path):
    """Test readonly file detection."""
    readonly_file = tmp_path / "readonly.txt"
    readonly_file.write_text("test")
    readonly_file.chmod(0o444)  # Read-only

    state = _PaneState(current_dir=tmp_path)
    state.refresh_entries(BrowserMode.FILE)

    for entry in state.entries:
        if entry.path == readonly_file:
            assert entry.is_readonly is True
            break


def test_pane_entry_executable_detection(tmp_path):
    """Test executable file detection."""
    exec_file = tmp_path / "script.sh"
    exec_file.write_text("#!/bin/bash\necho test")
    exec_file.chmod(0o755)  # Executable

    state = _PaneState(current_dir=tmp_path)
    state.refresh_entries(BrowserMode.FILE)

    for entry in state.entries:
        if entry.path == exec_file:
            assert entry.is_executable is True
            break


def test_pane_entry_symlink_detection(tmp_path):
    """Test symlink detection."""
    target = tmp_path / "target.txt"
    target.write_text("test")

    link = tmp_path / "link.txt"
    link.symlink_to(target)

    state = _PaneState(current_dir=tmp_path)
    state.refresh_entries(BrowserMode.FILE)

    for entry in state.entries:
        if entry.path == link:
            assert entry.is_symlink is True
            break
