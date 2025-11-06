"""Tests for browser mode definitions."""

from nedok.modes import BrowserMode, ALL_MODES


def test_browser_mode_enum_values():
    """Test that BrowserMode has expected values."""
    assert BrowserMode.FILE.value == "file"
    assert BrowserMode.TREE.value == "tree"
    assert BrowserMode.GIT.value == "git"
    assert BrowserMode.OWNER.value == "owner"


def test_browser_mode_labels():
    """Test that mode labels are correct."""
    assert BrowserMode.FILE.label == "File"
    assert BrowserMode.TREE.label == "Tree"
    assert BrowserMode.GIT.label == "Git"
    assert BrowserMode.OWNER.label == "Owner"


def test_all_modes_contains_all_modes():
    """Test that ALL_MODES contains all browser modes."""
    assert len(ALL_MODES) == 4
    assert BrowserMode.FILE in ALL_MODES
    assert BrowserMode.TREE in ALL_MODES
    assert BrowserMode.GIT in ALL_MODES
    assert BrowserMode.OWNER in ALL_MODES


def test_all_modes_is_iterable():
    """Test that ALL_MODES can be iterated."""
    modes = []
    for mode in ALL_MODES:
        modes.append(mode)
    assert len(modes) == 4


def test_browser_mode_equality():
    """Test mode comparison."""
    assert BrowserMode.FILE == BrowserMode.FILE
    assert BrowserMode.FILE != BrowserMode.GIT
    assert BrowserMode.TREE != BrowserMode.OWNER
