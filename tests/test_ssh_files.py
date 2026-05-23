"""Tests for sshsync.ssh_files module."""

import os
from pathlib import Path

import pytest

from sshsync.ssh_files import (
    SSHFileError,
    backup_file,
    copy_from_repo,
    copy_to_repo,
    list_managed_files,
    read_file,
    write_file,
)


# ---------------------------------------------------------------------------
# read_file / write_file
# ---------------------------------------------------------------------------

class TestReadFile:
    def test_reads_content(self, tmp_path):
        p = tmp_path / "config"
        p.write_text("Host *\n  ServerAliveInterval 60\n")
        assert "ServerAliveInterval" in read_file(p)

    def test_raises_on_missing(self, tmp_path):
        with pytest.raises(SSHFileError, match="Cannot read"):
            read_file(tmp_path / "nonexistent")


class TestWriteFile:
    def test_writes_content(self, tmp_path):
        p = tmp_path / "subdir" / "config"
        write_file(p, "Host example\n  User alice\n")
        assert p.read_text() == "Host example\n  User alice\n"

    def test_sets_permissions_600(self, tmp_path):
        p = tmp_path / "config"
        write_file(p, "content")
        mode = oct(os.stat(p).st_mode & 0o777)
        assert mode == oct(0o600)

    def test_creates_parent_dirs(self, tmp_path):
        p = tmp_path / "a" / "b" / "c" / "config"
        write_file(p, "data")
        assert p.exists()


# ---------------------------------------------------------------------------
# backup_file
# ---------------------------------------------------------------------------

class TestBackupFile:
    def test_creates_bak(self, tmp_path):
        p = tmp_path / "known_hosts"
        p.write_text("entry1")
        bak = backup_file(p)
        assert bak is not None
        assert bak.exists()
        assert bak.read_text() == "entry1"

    def test_returns_none_if_missing(self, tmp_path):
        result = backup_file(tmp_path / "no_file")
        assert result is None


# ---------------------------------------------------------------------------
# copy_to_repo / copy_from_repo
# ---------------------------------------------------------------------------

class TestCopyToRepo:
    def test_copies_file(self, tmp_path):
        src = tmp_path / "config"
        src.write_text("ssh config content")
        repo = tmp_path / "repo"
        repo.mkdir()
        dest = copy_to_repo(src, repo, "config")
        assert dest.read_text() == "ssh config content"

    def test_raises_on_missing_src(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        with pytest.raises(SSHFileError):
            copy_to_repo(tmp_path / "missing", repo, "config")


class TestCopyFromRepo:
    def test_copies_and_backs_up(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "config").write_text("new content")
        dest = tmp_path / "config"
        dest.write_text("old content")
        copy_from_repo(repo, "config", dest)
        assert dest.read_text() == "new content"
        assert (tmp_path / "config.bak").read_text() == "old content"

    def test_raises_if_not_in_repo(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        with pytest.raises(SSHFileError, match="File not found in repo"):
            copy_from_repo(repo, "config", tmp_path / "config")


# ---------------------------------------------------------------------------
# list_managed_files
# ---------------------------------------------------------------------------

def test_list_managed_files(tmp_path):
    (tmp_path / "config").touch()
    (tmp_path / "known_hosts").touch()
    result = list_managed_files(tmp_path, ["config", "known_hosts", "id_rsa"])
    names = [p.name for p in result]
    assert "config" in names
    assert "known_hosts" in names
    assert "id_rsa" not in names
