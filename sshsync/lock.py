"""
Advisory file-locking for sshsync operations.

Prevents concurrent push/pull operations from corrupting the repo or
SSH files when multiple processes run simultaneously.
"""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

_DEFAULT_TIMEOUT = 30  # seconds
_POLL_INTERVAL = 0.2  # seconds


class LockError(Exception):
    """Raised when a lock cannot be acquired."""


def _lock_path(repo_dir: Path) -> Path:
    return repo_dir / ".sshsync.lock"


def acquire(repo_dir: Path, timeout: float = _DEFAULT_TIMEOUT) -> Path:
    """Create a lock file inside *repo_dir*; block until acquired or timeout.

    Returns the path to the lock file on success.
    Raises LockError if the lock cannot be obtained within *timeout* seconds.
    """
    lock = _lock_path(repo_dir)
    deadline = time.monotonic() + timeout

    while True:
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w") as fh:
                fh.write(str(os.getpid()))
            return lock
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise LockError(
                    f"Could not acquire lock '{lock}' within {timeout}s. "
                    "Another sshsync process may be running."
                ) from None
            time.sleep(_POLL_INTERVAL)


def release(lock: Path) -> None:
    """Remove the lock file, ignoring errors if it is already gone."""
    try:
        lock.unlink()
    except FileNotFoundError:
        pass


@contextmanager
def repo_lock(
    repo_dir: Path, timeout: float = _DEFAULT_TIMEOUT
) -> Generator[Path, None, None]:
    """Context manager that acquires and releases a lock on *repo_dir*."""
    lock = acquire(repo_dir, timeout=timeout)
    try:
        yield lock
    finally:
        release(lock)
