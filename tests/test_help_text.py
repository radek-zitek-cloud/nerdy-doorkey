from src.dual_pane_browser.help_text import build_help_lines
from src.dual_pane_browser.modes import BrowserMode


def test_help_lines_include_mode_header():
    lines = build_help_lines(BrowserMode.FILE)
    assert lines[0].lower().startswith("display mode:")
    assert any("navigation & layout" in line.lower() for line in lines)


def test_help_lines_list_all_commands_for_every_mode():
    for mode in (BrowserMode.FILE, BrowserMode.GIT):
        lines = build_help_lines(mode)
        joined = "\n".join(lines).lower()
        for snippet in (
            "delete highlighted item",
            "copy item to the other pane",
            "move item to the other pane",
            "view file contents read-only",
            "open file with $editor",
            "stage item with git add",
            "unstage item from index",
            "restore item from head",
        ):
            assert snippet in joined
