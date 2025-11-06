"""Actions that shell out to Git when the user requests a VCS feature."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from .state import _PaneEntry


class GitOperationsMixin:
    """Mixin providing git operations (stage, commit, diff, log, blame, restore)."""

    def _git_stage_entry(self) -> None:
        """Stage the selected file or directory for the next commit."""
        entry = self._active_pane.selected_entry()
        if entry is None or entry.is_parent:
            self.status_message = "Select an item to stage."
            return
        context = self._git_context(entry)
        if context is None:
            return
        repo_root, relative_path = context
        rel_str = str(relative_path)
        if self._run_git_command(repo_root, ["add", "--", rel_str]):
            self.status_message = f"Staged {rel_str}."
            self._refresh_panes()

    def _git_unstage_entry(self) -> None:
        """Remove the selected item from the staging area."""
        entry = self._active_pane.selected_entry()
        if entry is None or entry.is_parent:
            self.status_message = "Select an item to unstage."
            return
        if entry.git_status == "??":
            self.status_message = "File is untracked; nothing to unstage."
            return
        context = self._git_context(entry)
        if context is None:
            return
        repo_root, relative_path = context
        rel_str = str(relative_path)
        if self._run_git_command(repo_root, ["restore", "--staged", "--", rel_str]):
            self.status_message = f"Unstaged {rel_str}."
            self._refresh_panes()

    def _git_restore_entry(self) -> None:
        """Prompt the user before resetting a file back to ``HEAD``."""
        entry = self._active_pane.selected_entry()
        if entry is None or entry.is_parent:
            self.status_message = "Select an item to restore."
            return
        context = self._git_context(entry)
        if context is None:
            return
        repo_root, relative_path = context
        rel_str = str(relative_path)

        def do_restore() -> None:
            if self._run_git_command(
                repo_root,
                ["restore", "--worktree", "--source=HEAD", "--", rel_str],
            ):
                self.status_message = f"Restored {rel_str} to HEAD."
                self._refresh_panes()

        self._request_confirmation(f"Restore {entry.path.name} to HEAD?", do_restore)

    def _git_diff_entry(self) -> None:
        """Show git diff in pager for better viewing."""
        entry = self._active_pane.selected_entry()
        if entry is None or entry.is_parent:
            self.status_message = "Select a file to diff."
            return
        if entry.is_dir:
            self.status_message = "Diff is only available for files."
            return
        context = self._git_context(entry)
        if context is None:
            return
        repo_root, relative_path = context
        rel_str = str(relative_path)

        # Build diff command
        if entry.git_status == "??":
            command = [
                "git",
                "-C",
                str(repo_root),
                "diff",
                "--no-index",
                "--color=always",
                "--",
                "/dev/null",
                rel_str,
            ]
        else:
            command = [
                "git",
                "-C",
                str(repo_root),
                "diff",
                "HEAD",
                "--color=always",
                "--",
                rel_str,
            ]

        try:
            # Create the diff
            diff_result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )

            if diff_result.returncode not in (0, 1):
                err_text = diff_result.stderr.strip() or "unknown error"
                self.status_message = f"Git diff failed: {err_text}"
                return

            if not diff_result.stdout.strip():
                self.status_message = f"No differences for {rel_str}."
                return

            # Write to temp file and open in pager
            with tempfile.NamedTemporaryFile(mode='w', suffix='.diff', delete=False) as f:
                f.write(diff_result.stdout)
                temp_path = f.name

            try:
                pager = os.environ.get("PAGER", "less")
                # Add -R flag for less to handle ANSI color codes
                if "less" in pager.lower():
                    pager_command = [pager, "-R", temp_path]
                else:
                    pager_command = [pager, temp_path]
                self._run_external(pager_command)
            finally:
                Path(temp_path).unlink(missing_ok=True)

        except OSError as err:
            self.status_message = f"Git diff failed: {err}"

    def _git_commit(self) -> None:
        """Create a git commit."""
        # Get repo root
        try:
            result = subprocess.run(
                ["git", "-C", str(self._active_pane.current_dir), "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as err:
            self.status_message = f"Git not available: {err}"
            return

        if result.returncode != 0:
            self.status_message = "Not in a git repository."
            return

        repo_root = Path(result.stdout.strip())

        # Check if there are staged changes
        try:
            status_result = subprocess.run(
                ["git", "-C", str(repo_root), "diff", "--cached", "--quiet"],
                check=False,
            )
            if status_result.returncode == 0:
                self.status_message = "No staged changes to commit."
                return
        except OSError:
            pass

        # Open editor for commit message
        editor = os.environ.get("EDITOR", "vi")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("\n# Enter commit message above this line\n")
            f.write("# Changes to be committed:\n")
            temp_path = f.name

        try:
            # Suspend curses and open editor
            self._run_external([editor, temp_path])

            # Read commit message
            commit_msg = Path(temp_path).read_text()
            # Remove comment lines
            lines = [l for l in commit_msg.splitlines() if not l.startswith('#')]
            commit_msg = '\n'.join(lines).strip()

            if not commit_msg:
                self.status_message = "Commit cancelled (empty message)."
                return

            # Execute commit
            result = subprocess.run(
                ["git", "-C", str(repo_root), "commit", "-m", commit_msg],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                self.status_message = "Commit created successfully."
                self._refresh_panes()
            else:
                self.status_message = f"Commit failed: {result.stderr.strip()}"

        except OSError as err:
            self.status_message = f"Commit failed: {err}"
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def _git_log_entry(self) -> None:
        """Show git log for selected file or directory."""
        entry = self._active_pane.selected_entry()
        if entry is None or entry.is_parent:
            self.status_message = "Select an item to view log."
            return

        context = self._git_context(entry)
        if context is None:
            return

        repo_root, relative_path = context
        rel_str = str(relative_path)

        pager = os.environ.get("PAGER", "less")
        command = [
            "git", "-C", str(repo_root),
            "log", "--oneline", "--decorate", "--color=always",
            "-n", "100",  # Last 100 commits
            "--", rel_str
        ]

        try:
            # Run git log and capture output
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                self.status_message = f"Git log failed: {result.stderr.strip()}"
                return

            if not result.stdout.strip():
                self.status_message = f"No commits found for {rel_str}."
                return

            # Write to temp file and open in pager
            with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
                f.write(result.stdout)
                temp_path = f.name

            try:
                # Add -R flag for less to handle ANSI color codes
                if "less" in pager.lower():
                    pager_command = [pager, "-R", temp_path]
                else:
                    pager_command = [pager, temp_path]
                self._run_external(pager_command)
            finally:
                Path(temp_path).unlink(missing_ok=True)

        except OSError as err:
            self.status_message = f"Git log failed: {err}"

    def _git_blame_entry(self) -> None:
        """Show git blame for selected file."""
        entry = self._active_pane.selected_entry()
        if entry is None or entry.is_parent or entry.is_dir:
            self.status_message = "Select a file to blame."
            return

        context = self._git_context(entry)
        if context is None:
            return

        repo_root, relative_path = context
        rel_str = str(relative_path)

        pager = os.environ.get("PAGER", "less")
        command = [
            "git", "-C", str(repo_root),
            "blame", "--color-by-age", rel_str
        ]

        try:
            # Run git blame and capture output
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                self.status_message = f"Git blame failed: {result.stderr.strip()}"
                return

            if not result.stdout.strip():
                self.status_message = f"No blame info for {rel_str}."
                return

            # Write to temp file and open in pager
            with tempfile.NamedTemporaryFile(mode='w', suffix='.blame', delete=False) as f:
                f.write(result.stdout)
                temp_path = f.name

            try:
                # Add -R flag for less to handle ANSI color codes
                if "less" in pager.lower():
                    pager_command = [pager, "-R", temp_path]
                else:
                    pager_command = [pager, temp_path]
                self._run_external(pager_command)
            finally:
                Path(temp_path).unlink(missing_ok=True)

        except OSError as err:
            self.status_message = f"Git blame failed: {err}"

    def _git_context(self, entry: "_PaneEntry") -> Tuple[Path, Path] | None:
        """Return ``(repository_root, relative_path)`` for ``entry``."""
        try:
            resolved = entry.path.resolve()
        except OSError as err:
            self.status_message = f"Cannot resolve path: {err}"
            return None
        search_dir = resolved if entry.is_dir else resolved.parent
        try:
            result = subprocess.run(
                ["git", "-C", str(search_dir), "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as err:
            self.status_message = f"Git not available: {err}"
            return None
        root_text = result.stdout.strip()
        if result.returncode != 0 or not root_text:
            self.status_message = "Not inside a git repository."
            return None
        repo_root = Path(root_text)
        try:
            relative = resolved.relative_to(repo_root)
        except ValueError:
            self.status_message = "Item is outside the repository."
            return None
        return repo_root, relative

    def _run_git_command(self, repo_root: Path, arguments: List[str]) -> bool:
        """Execute ``git`` with ``arguments`` and capture errors for the UI."""
        try:
            result = subprocess.run(
                ["git", "-C", str(repo_root), *arguments],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as err:
            self.status_message = f"Git command failed: {err}"
            return False
        if result.returncode != 0:
            stderr = result.stderr.strip() or result.stdout.strip() or "unknown error"
            self.status_message = f"Git command failed: {stderr}"
            return False
        return True


__all__ = ["GitOperationsMixin"]
