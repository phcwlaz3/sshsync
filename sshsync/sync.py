"""High-level sync operations: push local SSH files to repo and pull from repo."""

from __future__ import annotations

from pathlib import Path
from typing import List

from sshsync.config import SyncConfig
from sshsync.git_ops import GitError, commit, pull, push
from sshsync.ssh_files import SSHFileError, copy_from_repo, copy_to_repo, ssh_dir


class SyncError(Exception):
    """Raised when a sync operation fails."""


def push_ssh_files(config: SyncConfig, repo_dir: Path) -> List[str]:
    """Copy managed SSH files into *repo_dir*, commit, and push.

    Returns the list of filenames that were staged.
    Raises SyncError on failure.
    """
    staged: List[str] = []
    local_ssh = ssh_dir()

    for filename in config.managed_files:
        src = local_ssh / filename
        if not src.exists():
            continue
        try:
            copy_to_repo(src, repo_dir, filename)
            staged.append(filename)
        except SSHFileError as exc:
            raise SyncError(f"Failed to stage {filename}: {exc}") from exc

    if not staged:
        return staged

    try:
        commit(repo_dir, f"sshsync: update {', '.join(staged)}")
        push(repo_dir, config.branch)
    except GitError as exc:
        raise SyncError(f"Git operation failed: {exc}") from exc

    return staged


def pull_ssh_files(config: SyncConfig, repo_dir: Path) -> List[str]:
    """Pull latest changes from remote and copy managed files to ~/.ssh.

    Returns the list of filenames that were updated.
    Raises SyncError on failure.
    """
    try:
        pull(repo_dir, config.branch)
    except GitError as exc:
        raise SyncError(f"Git pull failed: {exc}") from exc

    updated: List[str] = []
    local_ssh = ssh_dir()

    for filename in config.managed_files:
        repo_file = repo_dir / filename
        if not repo_file.exists():
            continue
        dest = local_ssh / filename
        try:
            copy_from_repo(repo_dir, filename, dest)
            updated.append(filename)
        except SSHFileError as exc:
            raise SyncError(f"Failed to apply {filename}: {exc}") from exc

    return updated
