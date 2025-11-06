from src.nedok.help_text import build_help_lines
from src.nedok.modes import BrowserMode


def test_help_lines_cover_shortcuts():
    # Test File mode
    file_lines = build_help_lines(BrowserMode.FILE)
    file_text = "\n".join(file_lines).lower()

    # Check navigation keys are documented
    assert "enter" in file_text
    assert "bksp" in file_text or "backspace" in file_text
    assert "tab" in file_text
    assert "quit" in file_text or "q quit" in file_text

    # Check file operations are documented
    assert "rename" in file_text or " n " in file_text
    assert "del" in file_text or "delete" in file_text
    assert "copy" in file_text or " c " in file_text
    assert "move" in file_text or " t " in file_text
    assert "view" in file_text or " v " in file_text
    assert "edit" in file_text or " e " in file_text

    # Check new features are documented
    assert "newfile" in file_text or "new file" in file_text or " f " in file_text
    assert "newdir" in file_text or "new dir" in file_text or " f " in file_text

    # Check confirmation is mentioned
    assert "confirm" in file_text

    # Test Git mode
    git_lines = build_help_lines(BrowserMode.GIT)
    git_text = "\n".join(git_lines).lower()

    # Check git operations are documented
    for token in ("stage", "unstage", "restore", "diff", "commit", "log", "blame"):
        assert token in git_text

    # Check that mode switching is mentioned
    assert "mode" in git_text
