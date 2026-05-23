"""
High-level push / pull orchestration for sshsync.

Each operation acquires an advisory lock on the repo directory so that
concurrent invocations cannot corrupt state.
"""

from __future__ import annotations

from pathlib import Path

from sshsync.config import SyncConfig
from sshsync.git_ops import pull, push, commit
from sshsync.lock import repo_lock, LockError
from sshsync.merge import merge_known_hosts, merge_ssh_config
from sshsync.ssh_files import backup_file, read_file, write_file, ssh_dir


class SyncError(Exception):
    """Raised when a sync operation fails."""


def push_ssh_files(cfg: SyncConfig, repo_dir: Path) -> None:
    """Copy local SSH files into *repo_dir*, commit, and push.

    Acquires an advisory lock for the duration of the operation.
    """
    try:
        with repo_lock(repo_dir):
            for filename in cfg.managed_files:
                src = ssh_dir() / filename
                dst = repo_dir / filename
                try:
                    content = read_file(src)
                except FileNotFoundError:
                    continue  # skip files that don't exist locally
                write_file(dst, content)

            commit(repo_dir, message="sshsync: push")
            push(repo_dir, branch=cfg.branch)
    except LockError as exc:
        raise SyncError(str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise SyncError(f"Push failed: {exc}") from exc


def pull_ssh_files(cfg: SyncConfig, repo_dir: Path) -> None:
    """Pull from remote, merge SSH files into the local SSH directory.

    Acquires an advisory lock for the duration of the operation.
    """
    try:
        with repo_lock(repo_dir):
            pull(repo_dir, branch=cfg.branch)

            for filename in cfg.managed_files:
                remote = repo_dir / filename
                local = ssh_dir() / filename

                if not remote.exists():
                    continue

                remote_content = read_file(remote)

                if local.exists():
                    backup_file(local)
                    local_content = read_file(local)

                    if filename == "known_hosts":
                        merged = merge_known_hosts(local_content, remote_content)
                    else:
                        merged = merge_ssh_config(local_content, remote_content)

                    write_file(local, merged)
                else:
                    write_file(local, remote_content)
    except LockError as exc:
        raise SyncError(str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise SyncError(f"Pull failed: {exc}") from exc
