"""Minimal wrappers around the ``git`` command line client."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict, Tuple


def collect_git_status(directory: Path) -> Tuple[Path | None, Dict[Path, str]]:
    """Return ``(repository_root, status_map)`` for the given directory.

    ``status_map`` is a dictionary where each key is an absolute path inside the
    repository and each value is the two-character porcelain status code (e.g.
    ``"??"`` for untracked files).  When ``directory`` is not part of a Git
    repository we return ``(None, {})``.
    """
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
            ["git", "-C", str(repo_root), "status", "--porcelain=1", "-z"],
            capture_output=True,
            text=False,
            check=False,
        )
    except OSError:
        return repo_root, {}
    if status_result.returncode != 0:
        return repo_root, {}

    status_map: Dict[Path, str] = {}
    entries = status_result.stdout.split(b"\0")
    index = 0
    total = len(entries)

    while index < total:
        raw_entry = entries[index]
        index += 1
        if not raw_entry:
            continue
        if len(raw_entry) < 4:
            continue

        status_bytes = raw_entry[:2]
        status_code = status_bytes.decode("ascii", errors="replace")

        path_bytes = raw_entry[3:]
        path_text = path_bytes.decode("utf-8", errors="surrogateescape")

        # Renames/copies include an additional path entry; prefer the new name
        if status_code and status_code[0] in ("R", "C") and index < total:
            new_path_bytes = entries[index]
            index += 1
            if new_path_bytes:
                path_text = new_path_bytes.decode("utf-8", errors="surrogateescape")

        absolute = (repo_root / Path(path_text)).resolve(strict=False)
        status_map[absolute] = status_code

    return repo_root, status_map


__all__ = ["collect_git_status"]
