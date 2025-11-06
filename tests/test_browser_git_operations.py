from __future__ import annotations

import subprocess
from pathlib import Path

from nedok.browser import DualPaneBrowser
from nedok.modes import BrowserMode


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    )


def _select_entry(browser: DualPaneBrowser, path: Path) -> None:
    browser.left.refresh_entries(BrowserMode.GIT)
    for idx, entry in enumerate(browser.left.entries):
        if entry.path == path:
            browser.left.cursor_index = idx
            return
    raise AssertionError(f"Path not listed in pane: {path}")


def test_git_mode_stage_unstage_restore(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    _run(["git", "init"], cwd=repo)
    _run(["git", "config", "user.email", "test@example.com"], cwd=repo)
    _run(["git", "config", "user.name", "Tester"], cwd=repo)

    tracked = repo / "tracked.txt"
    tracked.write_text("initial\n", encoding="utf-8")

    _run(["git", "add", "tracked.txt"], cwd=repo)
    _run(["git", "commit", "-m", "init"], cwd=repo)

    tracked.write_text("changed\n", encoding="utf-8")

    browser = DualPaneBrowser(repo, repo)
    browser.mode = BrowserMode.GIT

    # Note: _git_diff_entry now opens in pager, so we can't easily test output here
    # We just verify it doesn't crash
    browser.show_help = True
    assert browser._handle_mode_command(ord("g")) is True
    assert browser.show_help is False

    _select_entry(browser, tracked)
    browser._git_stage_entry()

    status_after_stage = _run(["git", "status", "--porcelain"], cwd=repo).stdout.splitlines()
    assert "M  tracked.txt" in status_after_stage

    _select_entry(browser, tracked)
    browser._git_unstage_entry()

    status_after_unstage = _run(["git", "status", "--porcelain"], cwd=repo).stdout.splitlines()
    assert " M tracked.txt" in status_after_unstage

    _select_entry(browser, tracked)
    # Need to confirm the restore since it now requires confirmation
    browser._git_restore_entry()
    assert browser.pending_action is not None
    # Simulate pressing 'y' to confirm
    _, action = browser.pending_action
    browser.pending_action = None
    action()

    status_after_restore = _run(["git", "status", "--porcelain"], cwd=repo).stdout.splitlines()
    assert status_after_restore == []
    assert tracked.read_text(encoding="utf-8") == "initial\n"
