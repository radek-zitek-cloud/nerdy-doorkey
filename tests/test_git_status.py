import subprocess
from pathlib import Path

from nedok.git_status import collect_git_status


def test_collect_git_status_outside_repo(tmp_path: Path):
    root, status_map = collect_git_status(tmp_path)
    assert root is None
    assert status_map == {}


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    )


def _setup_repo(path: Path) -> None:
    _run(["git", "init"], cwd=path)
    _run(["git", "config", "user.email", "test@example.com"], cwd=path)
    _run(["git", "config", "user.name", "Tester"], cwd=path)


def test_collect_git_status_preserves_columns(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _setup_repo(repo)

    tracked = repo / "tracked.txt"
    tracked.write_text("initial\n", encoding="utf-8")

    _run(["git", "add", "tracked.txt"], cwd=repo)
    _run(["git", "commit", "-m", "init"], cwd=repo)

    # Modify without staging: should appear as ' M'
    tracked.write_text("modified\n", encoding="utf-8")
    root, status_map = collect_git_status(repo)
    assert root == repo.resolve()
    key = (repo / "tracked.txt").resolve()
    assert status_map[key] == " M"

    # Stage the change: should appear as 'M '
    _run(["git", "add", "tracked.txt"], cwd=repo)
    root, status_map = collect_git_status(repo)
    assert status_map[key] == "M "


def test_collect_git_status_handles_quoted_paths(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _setup_repo(repo)

    # Create initial commit so repository has HEAD
    _run(["git", "commit", "--allow-empty", "-m", "init"], cwd=repo)

    spaced = repo / "spaced name.txt"
    spaced.write_text("data\n", encoding="utf-8")

    root, status_map = collect_git_status(repo)
    assert root == repo.resolve()
    key = spaced.resolve()
    assert status_map[key] == "??"
