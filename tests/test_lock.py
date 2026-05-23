"""
Tests for sshsync.lock — advisory file locking.
"""

from __future__ import annotations

import os
import threading
from pathlib import Path

import pytest

from sshsync.lock import LockError, acquire, release, repo_lock, _lock_path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    return repo


# ---------------------------------------------------------------------------
# acquire / release
# ---------------------------------------------------------------------------


class TestAcquireRelease:
    def test_creates_lock_file(self, tmp_path):
        repo = _repo(tmp_path)
        lock = acquire(repo)
        assert lock.exists()
        release(lock)

    def test_lock_contains_pid(self, tmp_path):
        repo = _repo(tmp_path)
        lock = acquire(repo)
        assert lock.read_text().strip() == str(os.getpid())
        release(lock)

    def test_release_removes_file(self, tmp_path):
        repo = _repo(tmp_path)
        lock = acquire(repo)
        release(lock)
        assert not lock.exists()

    def test_release_idempotent(self, tmp_path):
        repo = _repo(tmp_path)
        lock = _lock_path(repo)
        # Should not raise even if file is already gone
        release(lock)

    def test_raises_lock_error_on_timeout(self, tmp_path):
        repo = _repo(tmp_path)
        # Pre-create the lock file to simulate another process holding it
        _lock_path(repo).write_text("99999")
        with pytest.raises(LockError, match="sshsync process"):
            acquire(repo, timeout=0.1)
        # Cleanup
        _lock_path(repo).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# repo_lock context manager
# ---------------------------------------------------------------------------


class TestRepoLock:
    def test_lock_acquired_and_released(self, tmp_path):
        repo = _repo(tmp_path)
        lock_path = _lock_path(repo)
        with repo_lock(repo):
            assert lock_path.exists()
        assert not lock_path.exists()

    def test_lock_released_on_exception(self, tmp_path):
        repo = _repo(tmp_path)
        lock_path = _lock_path(repo)
        with pytest.raises(RuntimeError):
            with repo_lock(repo):
                assert lock_path.exists()
                raise RuntimeError("boom")
        assert not lock_path.exists()

    def test_sequential_locks_succeed(self, tmp_path):
        repo = _repo(tmp_path)
        with repo_lock(repo):
            pass
        # Second acquisition must succeed immediately
        with repo_lock(repo):
            pass

    def test_concurrent_lock_blocks(self, tmp_path):
        """Second thread must wait until first releases the lock."""
        repo = _repo(tmp_path)
        order: list[str] = []
        barrier = threading.Event()

        def first():
            with repo_lock(repo, timeout=5):
                order.append("first-in")
                barrier.set()
                time.sleep(0.15)  # hold the lock briefly
                order.append("first-out")

        def second():
            barrier.wait()
            with repo_lock(repo, timeout=5):
                order.append("second-in")

        import time

        t1 = threading.Thread(target=first)
        t2 = threading.Thread(target=second)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert order.index("first-out") < order.index("second-in")
