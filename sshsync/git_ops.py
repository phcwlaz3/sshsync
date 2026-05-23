"""Git operations for syncing SSH config via a git repository."""

import subprocess
import os
from pathlib import Path
from typing import Optional


class GitError(Exception):
    """Raised when a git operation fails."""
    pass


def _run(cmd: list[str], cwd: Optional[Path] = None) -> str:
    """Run a git command and return stdout. Raises GitError on failure."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise GitError(f"Command {' '.join(cmd)} failed: {e.stderr.strip()}") from e


def clone_repo(repo_url: str, dest: Path) -> None:
    """Clone a remote repository to dest if it doesn't already exist."""
    if dest.exists():
        raise GitError(f"Destination already exists: {dest}")
    _run(["git", "clone", repo_url, str(dest)])


def init_repo(path: Path) -> None:
    """Initialize a new git repository at path."""
    path.mkdir(parents=True, exist_ok=True)
    _run(["git", "init"], cwd=path)


def pull(repo_path: Path, branch: str = "main") -> None:
    """Pull latest changes from origin."""
    _run(["git", "pull", "origin", branch], cwd=repo_path)


def commit_and_push(repo_path: Path, message: str, branch: str = "main") -> bool:
    """Stage all changes, commit, and push. Returns True if a commit was made."""
    _run(["git", "add", "--all"], cwd=repo_path)

    status = _run(["git", "status", "--porcelain"], cwd=repo_path)
    if not status:
        return False

    author = _build_author()
    commit_cmd = ["git", "commit", "-m", message]
    if author:
        commit_cmd += ["--author", author]
    _run(commit_cmd, cwd=repo_path)
    _run(["git", "push", "origin", branch], cwd=repo_path)
    return True


def has_uncommitted_changes(repo_path: Path) -> bool:
    """Return True if the repo has uncommitted changes."""
    status = _run(["git", "status", "--porcelain"], cwd=repo_path)
    return bool(status)


def _build_author() -> Optional[str]:
    """Build a git author string from environment variables if set."""
    name = os.environ.get("SSHSYNC_GIT_AUTHOR_NAME")
    email = os.environ.get("SSHSYNC_GIT_AUTHOR_EMAIL")
    if name and email:
        return f"{name} <{email}>"
    return None
