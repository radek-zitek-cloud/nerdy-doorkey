"""Helpers for integrating git status information."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict, Tuple


def collect_git_status(directory: Path) -> Tuple[Path | None, Dict[Path, str]]:
    """Return (repo_root, status_map) for files under `directory`."""
    try:
        root_result = subprocess.run(
            ["git", "-C", str(directory), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None, {}
    if root_result.returncode != 0:
        return None, {}
    repo_root = Path(root_result.stdout.strip())
    try:
        status_result = subprocess.run(
            ["git", "-C", str(repo_root), "status", "--porcelain=1"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return repo_root, {}
    if status_result.returncode != 0:
        return repo_root, {}

    status_map: Dict[Path, str] = {}
    for raw_line in status_result.stdout.splitlines():
        if not raw_line:
            continue
        if len(raw_line) < 3:
            continue
        status_code = raw_line[:2].strip()
        path_part = raw_line[3:]
        if " -> " in path_part:
            path_part = path_part.split(" -> ", 1)[-1]
        abs_path = (repo_root / path_part).resolve()
        status_map[abs_path] = status_code or "-"
    return repo_root, status_map


__all__ = ["collect_git_status"]
