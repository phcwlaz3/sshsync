"""Tests for sshsync config dataclass and config_io read/write helpers."""

import configparser
from pathlib import Path

import pytest

from sshsync.config import SyncConfig
from sshsync.config_io import load_config, save_config


# ---------------------------------------------------------------------------
# SyncConfig unit tests
# ---------------------------------------------------------------------------

class TestSyncConfigDefaults:
    def test_default_branch(self):
        cfg = SyncConfig()
        assert cfg.branch == "main"

    def test_default_managed_files(self):
        cfg = SyncConfig()
        assert "config" in cfg.managed_files
        assert "known_hosts" in cfg.managed_files

    def test_validate_missing_repo_url(self):
        cfg = SyncConfig()
        errors = cfg.validate()
        assert any("repo_url" in e for e in errors)

    def test_validate_ok(self):
        cfg = SyncConfig(repo_url="git@github.com:user/ssh-sync.git")
        assert cfg.validate() == []

    def test_round_trip_dict(self):
        cfg = SyncConfig(
            repo_url="git@github.com:user/repo.git",
            branch="dev",
            auto_push=False,
            managed_files=["config"],
        )
        restored = SyncConfig.from_dict(cfg.to_dict())
        assert restored.repo_url == cfg.repo_url
        assert restored.branch == cfg.branch
        assert restored.auto_push == cfg.auto_push
        assert restored.managed_files == cfg.managed_files


# ---------------------------------------------------------------------------
# config_io integration tests
# ---------------------------------------------------------------------------

class TestConfigIO:
    def test_load_missing_file_returns_defaults(self, tmp_path):
        cfg = load_config(tmp_path / "nonexistent.conf")
        assert isinstance(cfg, SyncConfig)
        assert cfg.branch == "main"

    def test_save_and_load_round_trip(self, tmp_path):
        path = tmp_path / "sshsync.conf"
        original = SyncConfig(
            repo_url="git@github.com:alice/ssh.git",
            branch="stable",
            auto_push=False,
            managed_files=["config", "known_hosts"],
        )
        save_config(original, path)
        loaded = load_config(path)

        assert loaded.repo_url == original.repo_url
        assert loaded.branch == original.branch
        assert loaded.auto_push == original.auto_push
        assert loaded.managed_files == original.managed_files

    def test_save_creates_parent_dirs(self, tmp_path):
        path = tmp_path / "nested" / "dir" / "sshsync.conf"
        cfg = SyncConfig(repo_url="git@github.com:bob/ssh.git")
        save_config(cfg, path)
        assert path.exists()

    def test_saved_file_is_valid_ini(self, tmp_path):
        path = tmp_path / "sshsync.conf"
        save_config(SyncConfig(repo_url="git@github.com:x/y.git"), path)
        parser = configparser.ConfigParser()
        parser.read(path)
        assert "sshsync" in parser
        assert parser["sshsync"]["repo_url"] == "git@github.com:x/y.git"
