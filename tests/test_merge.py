"""Tests for sshsync.merge."""

import pytest

from sshsync.merge import merge_known_hosts, merge_ssh_config


# ---------------------------------------------------------------------------
# merge_known_hosts
# ---------------------------------------------------------------------------

class TestMergeKnownHosts:
    LOCAL = "github.com ssh-ed25519 AAAA1\ngitlab.com ssh-ed25519 AAAA2\n"
    REMOTE = "gitlab.com ssh-ed25519 AAAA2\nbitbucket.org ssh-ed25519 AAAA3\n"

    def test_local_lines_preserved(self):
        result = merge_known_hosts(self.LOCAL, self.REMOTE)
        assert "github.com ssh-ed25519 AAAA1" in result
        assert "gitlab.com ssh-ed25519 AAAA2" in result

    def test_new_remote_lines_added(self):
        result = merge_known_hosts(self.LOCAL, self.REMOTE)
        assert "bitbucket.org ssh-ed25519 AAAA3" in result

    def test_no_duplicates(self):
        result = merge_known_hosts(self.LOCAL, self.REMOTE)
        assert result.count("gitlab.com") == 1

    def test_local_order_first(self):
        result = merge_known_hosts(self.LOCAL, self.REMOTE)
        lines = [l for l in result.splitlines() if l.strip()]
        assert lines[0].startswith("github.com")
        assert lines[-1].startswith("bitbucket.org")

    def test_empty_local(self):
        result = merge_known_hosts("", self.REMOTE)
        assert "gitlab.com" in result
        assert "bitbucket.org" in result

    def test_empty_remote(self):
        result = merge_known_hosts(self.LOCAL, "")
        assert result.strip() == self.LOCAL.strip()

    def test_both_empty(self):
        assert merge_known_hosts("", "") == ""

    def test_trailing_newline(self):
        result = merge_known_hosts(self.LOCAL, self.REMOTE)
        assert result.endswith("\n")


# ---------------------------------------------------------------------------
# merge_ssh_config
# ---------------------------------------------------------------------------

class TestMergeSshConfig:
    LOCAL = "Host work\n    HostName work.example.com\n    User alice\n"
    REMOTE = (
        "Host work\n    HostName work.example.com\n    User bob\n\n"
        "Host personal\n    HostName personal.example.com\n    User alice\n"
    )

    def test_local_block_preferred(self):
        result = merge_ssh_config(self.LOCAL, self.REMOTE)
        # Local 'work' block uses 'alice', not 'bob'
        work_section = result.split("Host personal")[0]
        assert "User alice" in work_section
        assert "User bob" not in work_section

    def test_new_remote_block_added(self):
        result = merge_ssh_config(self.LOCAL, self.REMOTE)
        assert "Host personal" in result
        assert "personal.example.com" in result

    def test_no_duplicate_host_blocks(self):
        result = merge_ssh_config(self.LOCAL, self.REMOTE)
        assert result.count("Host work") == 1

    def test_empty_local(self):
        result = merge_ssh_config("", self.REMOTE)
        assert "Host work" in result
        assert "Host personal" in result

    def test_empty_remote(self):
        result = merge_ssh_config(self.LOCAL, "")
        assert "Host work" in result

    def test_both_empty(self):
        assert merge_ssh_config("", "") == ""
