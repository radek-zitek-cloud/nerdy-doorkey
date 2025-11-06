"""Tests for tree mode behavior."""

from __future__ import annotations

from pathlib import Path

from nedok.browser import DualPaneBrowser
from nedok.modes import BrowserMode


def test_tree_mode_lists_recursive_entries(tmp_path: Path) -> None:
    """Tree mode should show nested files beneath directories."""
    nested = tmp_path / "dir1" / "child.txt"
    nested.parent.mkdir(parents=True)
    nested.write_text("nested", encoding="utf-8")
    (tmp_path / "root.txt").write_text("root", encoding="utf-8")

    browser = DualPaneBrowser(tmp_path, tmp_path)
    browser.mode = BrowserMode.TREE
    browser._refresh_pane(browser.left)

    paths = [entry.path for entry in browser.left.entries]
    assert tmp_path / "dir1" in paths
    assert nested in paths
    assert tmp_path / "root.txt" in paths


def test_tree_mode_collapse_and_expand_from_file(tmp_path: Path) -> None:
    """Collapsing on a file should collapse its parent directory."""
    target_dir = tmp_path / "parent" / "child"
    target_dir.mkdir(parents=True)
    target_file = target_dir / "example.txt"
    target_file.write_text("data", encoding="utf-8")

    browser = DualPaneBrowser(tmp_path, tmp_path)
    browser.mode = BrowserMode.TREE
    browser._refresh_pane(browser.left)

    # Collapse while a file inside the directory is selected
    for index, entry in enumerate(browser.left.entries):
        if entry.path == target_file:
            browser.left.cursor_index = index
            break
    assert browser.left.collapse_tree_at_cursor()
    browser._refresh_pane(browser.left)

    # File is hidden while directory entry remains collapsed
    assert target_file not in [entry.path for entry in browser.left.entries]
    collapsed_dir = next(entry for entry in browser.left.entries if entry.path == target_dir)
    assert collapsed_dir.tree_is_collapsed

    # Expand the directory and verify the file reappears
    for index, entry in enumerate(browser.left.entries):
        if entry.path == target_dir:
            browser.left.cursor_index = index
            break
    assert browser.left.expand_tree_at_cursor()
    browser._refresh_pane(browser.left)
    assert target_file in [entry.path for entry in browser.left.entries]


def test_tree_mode_handles_symlink_cycles(tmp_path: Path) -> None:
    """Tree mode should not recurse endlessly when encountering symlink loops."""
    base = tmp_path / "base"
    child = base / "child"
    child.mkdir(parents=True)
    (child / "file.txt").write_text("payload", encoding="utf-8")
    loop = child / "loop"
    loop.symlink_to(base)

    browser = DualPaneBrowser(tmp_path, tmp_path)
    browser.mode = BrowserMode.TREE
    browser._refresh_pane(browser.left)

    entries = browser.left.entries
    assert sum(1 for entry in entries if entry.path == base) == 1
    assert sum(1 for entry in entries if entry.path == child) == 1
    assert sum(1 for entry in entries if entry.path == loop) == 1
    loop_entry = next(entry for entry in entries if entry.path == loop)
    assert not loop_entry.tree_is_expanded
