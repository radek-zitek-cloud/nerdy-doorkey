from src.dual_pane_browser.help_text import build_help_lines
from src.dual_pane_browser.modes import BrowserMode


def test_help_lines_include_general_commands():
    lines = build_help_lines(BrowserMode.FILE)
    assert any("Available Commands" in line for line in lines)
    assert any("Arrow keys" in line for line in lines)
    assert all(" q" not in line.lower() for line in lines)


def test_help_lines_include_mode_specific_entries():
    file_lines = build_help_lines(BrowserMode.FILE)
    git_lines = build_help_lines(BrowserMode.GIT)

    assert any("File Mode" in line for line in file_lines)
    assert any("Git Mode" in line for line in git_lines)
    assert any("delete" in line.lower() for line in file_lines)
    assert any("editor" in line.lower() for line in git_lines)
    assert any("stage item" in line.lower() for line in git_lines)
    assert any("unstage item" in line.lower() for line in git_lines)
    assert any("restore item" in line.lower() for line in git_lines)
