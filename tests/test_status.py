"""Tests for sshsync.status module."""

from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from sshsync.status import check_status, FileStatus, SyncStatus


MANAGED = ["config", "known_hosts"]


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


class TestSyncStatusHelpers:
    def test_all_in_sync_true(self):
        s = SyncStatus(files=[
            FileStatus("config", True, True, True, "ok"),
            FileStatus("known_hosts", True, True, True, "ok"),
        ])
        assert s.all_in_sync is True

    def test_all_in_sync_false(self):
        s = SyncStatus(files=[
            FileStatus("config", True, True, True, "ok"),
            FileStatus("known_hosts", True, True, False, "differs"),
        ])
        assert s.all_in_sync is False

    def test_summary_contains_filename(self):
        s = SyncStatus(files=[
            FileStatus("config", True, True, True, "up to date"),
        ])
        assert "config" in s.summary()
        assert "✓" in s.summary()

    def test_summary_empty(self):
        s = SyncStatus()
        assert "no managed files" in s.summary()


class TestCheckStatus:
    def test_both_absent(self, tmp_path):
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        local_dir = tmp_path / "ssh"
        local_dir.mkdir()

        with patch("sshsync.status.ssh_dir", return_value=local_dir):
            result = check_status(repo_dir, ["config"])

        assert len(result.files) == 1
        fs = result.files[0]
        assert fs.in_sync is True
        assert "absent" in fs.detail

    def test_missing_locally(self, tmp_path):
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        _write(repo_dir / "config", "Host *")
        local_dir = tmp_path / "ssh"
        local_dir.mkdir()

        with patch("sshsync.status.ssh_dir", return_value=local_dir):
            result = check_status(repo_dir, ["config"])

        fs = result.files[0]
        assert fs.in_sync is False
        assert "missing locally" in fs.detail

    def test_not_yet_pushed(self, tmp_path):
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        local_dir = tmp_path / "ssh"
        local_dir.mkdir()
        _write(local_dir / "config", "Host *")

        with patch("sshsync.status.ssh_dir", return_value=local_dir):
            result = check_status(repo_dir, ["config"])

        fs = result.files[0]
        assert fs.in_sync is False
        assert "not yet pushed" in fs.detail

    def test_in_sync(self, tmp_path):
        content = "Host example\n  User bob\n"
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        _write(repo_dir / "config", content)
        local_dir = tmp_path / "ssh"
        local_dir.mkdir()
        _write(local_dir / "config", content)

        with patch("sshsync.status.ssh_dir", return_value=local_dir):
            result = check_status(repo_dir, ["config"])

        fs = result.files[0]
        assert fs.in_sync is True
        assert fs.detail == "up to date"

    def test_differs(self, tmp_path):
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        _write(repo_dir / "config", "Host old\n")
        local_dir = tmp_path / "ssh"
        local_dir.mkdir()
        _write(local_dir / "config", "Host new\n")

        with patch("sshsync.status.ssh_dir", return_value=local_dir):
            result = check_status(repo_dir, ["config"])

        fs = result.files[0]
        assert fs.in_sync is False
        assert "differs" in fs.detail

    def test_multiple_files(self, tmp_path):
        content = "data\n"
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        local_dir = tmp_path / "ssh"
        local_dir.mkdir()
        for name in MANAGED:
            _write(repo_dir / name, content)
            _write(local_dir / name, content)

        with patch("sshsync.status.ssh_dir", return_value=local_dir):
            result = check_status(repo_dir, MANAGED)

        assert len(result.files) == 2
        assert result.all_in_sync is True
