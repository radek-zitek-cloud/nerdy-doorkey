"""Tests for new features: confirmation, rename, and file creation."""

from __future__ import annotations

from pathlib import Path

from src.nedok.browser import DualPaneBrowser
from src.nedok.modes import BrowserMode


def test_delete_requires_confirmation(tmp_path: Path) -> None:
    """Test that delete shows confirmation dialog."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content", encoding="utf-8")

    browser = DualPaneBrowser(tmp_path, tmp_path)
    browser.left.refresh_entries(BrowserMode.FILE)

    # Find and select the test file
    for idx, entry in enumerate(browser.left.entries):
        if entry.path == test_file:
            browser.left.cursor_index = idx
            break

    # Try to delete - should show confirmation
    browser._delete_entry()

    assert browser.pending_action is not None
    assert "Delete" in browser.pending_action[0]
    assert test_file.exists()  # Not deleted yet

    # Cancel the deletion
    browser.pending_action = None
    assert test_file.exists()


def test_delete_with_confirmation(tmp_path: Path) -> None:
    """Test that delete works when confirmed."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content", encoding="utf-8")

    browser = DualPaneBrowser(tmp_path, tmp_path)
    browser.left.refresh_entries(BrowserMode.FILE)

    # Find and select the test file
    for idx, entry in enumerate(browser.left.entries):
        if entry.path == test_file:
            browser.left.cursor_index = idx
            break

    # Delete and confirm
    browser._delete_entry()
    assert browser.pending_action is not None

    # Execute the action
    _, action = browser.pending_action
    browser.pending_action = None
    action()

    assert not test_file.exists()


def test_rename_file(tmp_path: Path) -> None:
    """Test renaming a file."""
    old_file = tmp_path / "old.txt"
    old_file.write_text("content", encoding="utf-8")

    browser = DualPaneBrowser(tmp_path, tmp_path)
    browser.left.refresh_entries(BrowserMode.FILE)

    # Select the file
    for idx, entry in enumerate(browser.left.entries):
        if entry.path == old_file:
            browser.left.cursor_index = idx
            break

    # Start rename
    browser._start_rename()
    assert browser.in_rename_mode
    assert browser.rename_buffer == "old.txt"

    # Change the name
    browser.rename_buffer = "new.txt"
    browser._execute_rename()

    # Verify rename worked
    assert not old_file.exists()
    assert (tmp_path / "new.txt").exists()
    assert not browser.in_rename_mode


def test_rename_to_existing_file_fails(tmp_path: Path) -> None:
    """Test that renaming to an existing file name fails."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("content1", encoding="utf-8")
    file2.write_text("content2", encoding="utf-8")

    browser = DualPaneBrowser(tmp_path, tmp_path)
    browser.left.refresh_entries(BrowserMode.FILE)

    # Select file1
    for idx, entry in enumerate(browser.left.entries):
        if entry.path == file1:
            browser.left.cursor_index = idx
            break

    # Try to rename to file2
    browser._start_rename()
    browser.rename_buffer = "file2.txt"
    browser._execute_rename()

    # Verify rename failed
    assert file1.exists()
    assert file2.exists()
    assert "already exists" in browser.status_message.lower()


def test_create_new_file(tmp_path: Path) -> None:
    """Test creating a new file."""
    browser = DualPaneBrowser(tmp_path, tmp_path)

    # Create a new file
    browser._create_file()
    assert browser.in_create_mode
    assert not browser.create_is_dir

    browser.create_buffer = "newfile.txt"
    browser._execute_create()

    # Verify file was created
    assert (tmp_path / "newfile.txt").exists()
    assert not browser.in_create_mode


def test_create_new_directory(tmp_path: Path) -> None:
    """Test creating a new directory."""
    browser = DualPaneBrowser(tmp_path, tmp_path)

    # Create a new directory
    browser._create_directory()
    assert browser.in_create_mode
    assert browser.create_is_dir

    browser.create_buffer = "newdir"
    browser._execute_create()

    # Verify directory was created
    assert (tmp_path / "newdir").exists()
    assert (tmp_path / "newdir").is_dir()
    assert not browser.in_create_mode


def test_create_with_empty_name_cancels(tmp_path: Path) -> None:
    """Test that creating with an empty name cancels the operation."""
    browser = DualPaneBrowser(tmp_path, tmp_path)

    browser._create_file()
    browser.create_buffer = "   "  # Whitespace only
    browser._execute_create()

    assert "empty name" in browser.status_message.lower()


def test_create_existing_file_fails(tmp_path: Path) -> None:
    """Test that creating a file that already exists fails."""
    existing = tmp_path / "existing.txt"
    existing.write_text("content", encoding="utf-8")

    browser = DualPaneBrowser(tmp_path, tmp_path)

    browser._create_file()
    browser.create_buffer = "existing.txt"
    browser._execute_create()

    assert "already exists" in browser.status_message.lower()


def test_confirmation_key_handler(tmp_path: Path) -> None:
    """Test the confirmation key handler."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content", encoding="utf-8")

    browser = DualPaneBrowser(tmp_path, tmp_path)
    browser.left.refresh_entries(BrowserMode.FILE)

    # Select file
    for idx, entry in enumerate(browser.left.entries):
        if entry.path == test_file:
            browser.left.cursor_index = idx
            break

    # Request delete (creates pending action)
    browser._delete_entry()
    assert browser.pending_action is not None

    # Test 'n' cancels
    handled = browser._handle_confirmation_key(ord('n'))
    assert handled
    assert browser.pending_action is None
    assert test_file.exists()

    # Request delete again
    browser._delete_entry()
    assert browser.pending_action is not None

    # Test 'y' confirms
    handled = browser._handle_confirmation_key(ord('y'))
    assert handled
    assert browser.pending_action is None
    assert not test_file.exists()


def test_refresh_active_pane(tmp_path: Path) -> None:
    """Test that refresh reloads directory contents."""
    browser = DualPaneBrowser(tmp_path, tmp_path)
    browser.left.refresh_entries(BrowserMode.FILE)

    # Record initial entry count
    initial_count = len(browser.left.entries)

    # Create a new file externally
    new_file = tmp_path / "new_file.txt"
    new_file.write_text("content", encoding="utf-8")

    # Without refresh, entry count should be the same
    assert len(browser.left.entries) == initial_count

    # Refresh the active pane
    browser._refresh_active_pane()

    # After refresh, should see the new file
    assert len(browser.left.entries) == initial_count + 1
    assert any(entry.path == new_file for entry in browser.left.entries)
    assert "Refreshed" in browser.status_message
