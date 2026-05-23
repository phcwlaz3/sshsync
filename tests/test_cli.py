"""Tests for sshsync.cli module."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from sshsync.cli import main
from sshsync.config import SyncConfig
from sshsync.git_ops import GitError
from sshsync.sync import SyncError
from sshsync.status import SyncStatus, FileStatus


DEFAULT_CFG = SyncConfig(
    repo_url="git@github.com:user/ssh-sync.git",
    repo_dir="/tmp/repo",
    managed_files=["config", "known_hosts"],
)


def _run(argv, cfg=DEFAULT_CFG):
    with patch("sshsync.cli.load_config", return_value=cfg):
        return main(argv)


class TestStatusCommand:
    def test_returns_0_when_in_sync(self):
        good = SyncStatus(files=[
            FileStatus("config", True, True, True, "up to date"),
        ])
        with patch("sshsync.cli.check_status", return_value=good):
            assert _run(["status"]) == 0

    def test_returns_1_when_out_of_sync(self):
        bad = SyncStatus(files=[
            FileStatus("config", True, True, False, "differs"),
        ])
        with patch("sshsync.cli.check_status", return_value=bad):
            assert _run(["status"]) == 1


class TestPushCommand:
    def test_returns_0_on_success(self):
        with patch("sshsync.cli.pull"), \
             patch("sshsync.cli.push_ssh_files"), \
             patch("sshsync.cli.push"):
            assert _run(["push"]) == 0

    def test_returns_2_on_git_error(self):
        with patch("sshsync.cli.pull", side_effect=GitError("fail")):
            assert _run(["push"]) == 2

    def test_returns_2_on_sync_error(self):
        with patch("sshsync.cli.pull"), \
             patch("sshsync.cli.push_ssh_files", side_effect=SyncError("fail")):
            assert _run(["push"]) == 2


class TestPullCommand:
    def test_returns_0_on_success(self):
        with patch("sshsync.cli.pull"), \
             patch("sshsync.cli.pull_ssh_files"):
            assert _run(["pull"]) == 0

    def test_returns_2_on_error(self):
        with patch("sshsync.cli.pull", side_effect=GitError("oops")):
            assert _run(["pull"]) == 2


class TestInitCommand:
    def test_returns_0_on_success(self, tmp_path):
        cfg_path = str(tmp_path / "sshsync.toml")
        with patch("sshsync.cli.clone_repo"), \
             patch("sshsync.cli.save_config"):
            code = main(["--config", cfg_path, "init",
                         "git@github.com:user/repo.git",
                         "--repo-dir", str(tmp_path / "repo")])
        assert code == 0

    def test_returns_2_on_clone_failure(self, tmp_path):
        cfg_path = str(tmp_path / "sshsync.toml")
        with patch("sshsync.cli.clone_repo", side_effect=GitError("clone failed")):
            code = main(["--config", cfg_path, "init",
                         "git@github.com:user/repo.git"])
        assert code == 2


class TestMissingConfig:
    def test_returns_1_when_config_missing(self, tmp_path):
        cfg_path = str(tmp_path / "nonexistent.toml")
        with patch("sshsync.cli.load_config", side_effect=FileNotFoundError):
            code = main(["--config", cfg_path, "status"])
        assert code == 1
