"""High-level push/pull orchestration for sshsync."""

from __future__ import annotations

from pathlib import Path

from sshsync.config import SyncConfig
from sshsync.git_ops import GitError, pull, push, commit
from sshsync.merge import merge_known_hosts, merge_ssh_config
from sshsync.ssh_files import SSHFileError, backup_file, read_file, write_file


class SyncError(Exception):
    """Raised when a sync operation fails."""


_MERGE_FN = {
    "config": merge_ssh_config,
    "known_hosts": merge_known_hosts,
}


def push_ssh_files(cfg: SyncConfig, repo_dir: Path) -> None:
    """Copy managed SSH files into *repo_dir*, commit and push.

    Raises :class:`SyncError` on any failure.
    """
    try:
        for filename in cfg.managed_files:
            src = read_file(cfg.ssh_dir / filename)
            dest = repo_dir / filename
            write_file(dest, src)

        commit(repo_dir, message="sshsync: update SSH files")
        push(repo_dir, branch=cfg.branch)
    except (SSHFileError, GitError) as exc:
        raise SyncError(str(exc)) from exc


def pull_ssh_files(cfg: SyncConfig, repo_dir: Path) -> None:
    """Pull latest changes from remote and merge into local SSH files.

    For each managed file the remote version is merged with the local
    copy (preferring local content) before writing back.  A backup of
    the original local file is created first.

    Raises :class:`SyncError` on any failure.
    """
    try:
        pull(repo_dir, branch=cfg.branch)

        for filename in cfg.managed_files:
            local_path = cfg.ssh_dir / filename
            remote_path = repo_dir / filename

            if not remote_path.exists():
                continue

            remote_content = read_file(remote_path)
            local_content = read_file(local_path) if local_path.exists() else ""

            merge_fn = _MERGE_FN.get(filename)
            if merge_fn is None:
                # Unknown file type: remote wins only if local is absent
                merged = local_content or remote_content
            else:
                merged = merge_fn(local_content, remote_content)

            if local_path.exists():
                backup_file(local_path)

            write_file(local_path, merged)

    except (SSHFileError, GitError) as exc:
        raise SyncError(str(exc)) from exc
