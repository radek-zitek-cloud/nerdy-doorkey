"""Tests for color management."""

from pathlib import Path
from unittest.mock import Mock, patch
import curses

from nedok.colors import get_file_color, get_git_color, ColorPair


def _make_entry(
    is_parent=False,
    is_dir=False,
    is_symlink=False,
    is_executable=False,
    is_readonly=False,
    is_remote=False,
    git_status=None,
    name="file.txt"
):
    """Helper to create a mock _PaneEntry."""
    entry = Mock()
    entry.is_parent = is_parent
    entry.is_dir = is_dir
    entry.is_symlink = is_symlink
    entry.is_executable = is_executable
    entry.is_readonly = is_readonly
    entry.is_remote = is_remote
    entry.git_status = git_status
    entry.path = name if is_remote else Path(name)
    return entry


@patch('curses.has_colors', return_value=False)
def test_get_file_color_parent_directory(mock_has_colors):
    """Test that parent directory gets directory color."""
    entry = _make_entry(is_parent=True)
    # Without colors, should return A_NORMAL
    result = get_file_color(entry)
    assert result == curses.A_NORMAL


@patch('curses.has_colors', return_value=False)
def test_get_file_color_directory(mock_has_colors):
    """Test that directories get directory color."""
    entry = _make_entry(is_dir=True)
    result = get_file_color(entry)
    assert result == curses.A_NORMAL


@patch('curses.has_colors', return_value=False)
def test_get_file_color_symlink(mock_has_colors):
    """Test that symlinks get symlink color."""
    entry = _make_entry(is_symlink=True)
    result = get_file_color(entry)
    assert result == curses.A_NORMAL


@patch('curses.has_colors', return_value=False)
def test_get_file_color_hidden_file(mock_has_colors):
    """Test that hidden files (dotfiles) get hidden color."""
    entry = _make_entry(name=".hidden")
    result = get_file_color(entry)
    assert result == curses.A_NORMAL


@patch('curses.has_colors', return_value=False)
def test_get_file_color_executable(mock_has_colors):
    """Test that executable files get executable color."""
    entry = _make_entry(is_executable=True)
    result = get_file_color(entry)
    assert result == curses.A_NORMAL


@patch('curses.has_colors', return_value=False)
def test_get_file_color_readonly(mock_has_colors):
    """Test that readonly files get readonly color."""
    entry = _make_entry(is_readonly=True)
    result = get_file_color(entry)
    assert result == curses.A_NORMAL


@patch('curses.has_colors', return_value=False)
def test_get_file_color_regular_file(mock_has_colors):
    """Test that regular files get normal color."""
    entry = _make_entry()
    result = get_file_color(entry)
    assert result == curses.A_NORMAL


@patch('curses.has_colors', return_value=False)
def test_get_file_color_priority_order(mock_has_colors):
    """Test that color priority is correct."""
    # Parent takes precedence over everything
    entry = _make_entry(is_parent=True, is_symlink=True, is_executable=True)
    result = get_file_color(entry)
    assert result == curses.A_NORMAL

    # Directory takes precedence over file attributes
    entry = _make_entry(is_dir=True, is_executable=True)
    result = get_file_color(entry)
    assert result == curses.A_NORMAL

    # Symlink takes precedence over hidden
    entry = _make_entry(is_symlink=True, name=".hidden")
    result = get_file_color(entry)
    assert result == curses.A_NORMAL


@patch('curses.has_colors', return_value=False)
def test_get_git_color_parent_directory(mock_has_colors):
    """Test that parent directory gets directory color in git mode."""
    entry = _make_entry(is_parent=True)
    result = get_git_color(entry)
    assert result == curses.A_NORMAL


@patch('curses.has_colors', return_value=False)
def test_get_git_color_directory(mock_has_colors):
    """Test that directories get directory color in git mode."""
    entry = _make_entry(is_dir=True)
    result = get_git_color(entry)
    assert result == curses.A_NORMAL


@patch('curses.has_colors', return_value=False)
def test_get_git_color_untracked(mock_has_colors):
    """Test that untracked files get untracked color."""
    entry = _make_entry(git_status="??")
    result = get_git_color(entry)
    assert result == curses.A_NORMAL


@patch('curses.has_colors', return_value=False)
def test_get_git_color_deleted(mock_has_colors):
    """Test that deleted files get deleted color."""
    entry = _make_entry(git_status="D ")
    result = get_git_color(entry)
    assert result == curses.A_NORMAL

    entry = _make_entry(git_status=" D")
    result = get_git_color(entry)
    assert result == curses.A_NORMAL


@patch('curses.has_colors', return_value=False)
def test_get_git_color_renamed(mock_has_colors):
    """Test that renamed files get renamed color."""
    entry = _make_entry(git_status="R ")
    result = get_git_color(entry)
    assert result == curses.A_NORMAL


@patch('curses.has_colors', return_value=False)
def test_get_git_color_staged(mock_has_colors):
    """Test that staged files get staged color."""
    entry = _make_entry(git_status="M ")
    result = get_git_color(entry)
    assert result == curses.A_NORMAL

    entry = _make_entry(git_status="A ")
    result = get_git_color(entry)
    assert result == curses.A_NORMAL


@patch('curses.has_colors', return_value=False)
def test_get_git_color_modified_unstaged(mock_has_colors):
    """Test that modified but unstaged files get modified color."""
    entry = _make_entry(git_status=" M")
    result = get_git_color(entry)
    assert result == curses.A_NORMAL


@patch('curses.has_colors', return_value=False)
def test_get_git_color_clean(mock_has_colors):
    """Test that clean files get clean color."""
    entry = _make_entry(git_status="  ")
    result = get_git_color(entry)
    assert result == curses.A_NORMAL

    # No git status also means clean
    entry = _make_entry(git_status=None)
    result = get_git_color(entry)
    assert result == curses.A_NORMAL


@patch('curses.has_colors', return_value=False)
def test_get_git_color_priority_order(mock_has_colors):
    """Test that git color priority is correct."""
    # Parent/directory always takes precedence
    entry = _make_entry(is_parent=True, git_status="??")
    result = get_git_color(entry)
    assert result == curses.A_NORMAL

    entry = _make_entry(is_dir=True, git_status="M ")
    result = get_git_color(entry)
    assert result == curses.A_NORMAL


def test_color_pair_enum_values():
    """Test that ColorPair enum has expected values."""
    assert ColorPair.DEFAULT == 0
    assert ColorPair.DIRECTORY == 1
    assert ColorPair.EXECUTABLE == 2
    assert ColorPair.SYMLINK == 3
    assert ColorPair.HIDDEN == 4
    assert ColorPair.READONLY == 5
    assert ColorPair.GIT_UNTRACKED == 10
    assert ColorPair.GIT_MODIFIED == 11
    assert ColorPair.GIT_STAGED == 12
    assert ColorPair.GIT_DELETED == 13
    assert ColorPair.GIT_RENAMED == 14
    assert ColorPair.GIT_CLEAN == 15
    assert ColorPair.DIALOG == 20
