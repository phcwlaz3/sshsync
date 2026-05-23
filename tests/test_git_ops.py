"""Tests for sshsync.git_ops module."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from sshsync.git_ops import (
    GitError,
    clone_repo,
    commit_and_push,
    has_uncommitted_changes,
    init_repo,
    pull,
)


def _make_cp_error(stderr: str = "error") -> subprocess.CalledProcessError:
    err = subprocess.CalledProcessError(1, "git")
    err.stderr = stderr
    return err


class TestRunHelper:
    @patch("sshsync.git_ops.subprocess.run")
    def test_raises_git_error_on_failure(self, mock_run):
        mock_run.side_effect = _make_cp_error("fatal: not a repo")
        with pytest.raises(GitError, match="fatal: not a repo"):
            pull(Path("/fake"), "main")


class TestCloneRepo:
    def test_raises_if_dest_exists(self, tmp_path):
        with pytest.raises(GitError, match="already exists"):
            clone_repo("git@github.com:user/repo.git", tmp_path)

    @patch("sshsync.git_ops.subprocess.run")
    def test_calls_git_clone(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        dest = tmp_path / "repo"
        clone_repo("git@github.com:user/repo.git", dest)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[:3] == ["git", "clone", "git@github.com:user/repo.git"]


class TestInitRepo:
    @patch("sshsync.git_ops.subprocess.run")
    def test_creates_dir_and_inits(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        dest = tmp_path / "new_repo"
        init_repo(dest)
        assert dest.exists()
        args = mock_run.call_args[0][0]
        assert args == ["git", "init"]


class TestPull:
    @patch("sshsync.git_ops.subprocess.run")
    def test_pull_uses_branch(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        pull(tmp_path, branch="develop")
        args = mock_run.call_args[0][0]
        assert args == ["git", "pull", "origin", "develop"]


class TestCommitAndPush:
    @patch("sshsync.git_ops.subprocess.run")
    def test_returns_false_when_nothing_to_commit(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        result = commit_and_push(tmp_path, "sync", branch="main")
        assert result is False

    @patch("sshsync.git_ops.subprocess.run")
    def test_returns_true_and_pushes_when_changes_exist(self, mock_run, tmp_path):
        responses = ["", "M config", "", ""]
        mock_run.side_effect = [
            MagicMock(stdout=r, returncode=0) for r in responses
        ]
        result = commit_and_push(tmp_path, "sync: update config", branch="main")
        assert result is True
        push_call = mock_run.call_args_list[-1][0][0]
        assert push_call == ["git", "push", "origin", "main"]


class TestHasUncommittedChanges:
    @patch("sshsync.git_ops.subprocess.run")
    def test_true_when_dirty(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(stdout="M known_hosts", returncode=0)
        assert has_uncommitted_changes(tmp_path) is True

    @patch("sshsync.git_ops.subprocess.run")
    def test_false_when_clean(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        assert has_uncommitted_changes(tmp_path) is False
