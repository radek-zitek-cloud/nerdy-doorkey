from pathlib import Path

from src.dual_pane_browser.git_status import collect_git_status


def test_collect_git_status_outside_repo(tmp_path: Path):
    root, status_map = collect_git_status(tmp_path)
    assert root is None
    assert status_map == {}
