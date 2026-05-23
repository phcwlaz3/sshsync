"""Tests for sshsync.resolve."""

import pytest

from sshsync.conflict import Conflict, ConflictError
from sshsync.resolve import Strategy, get_resolver, _local_wins, _remote_wins, _fail_on_conflict


LOCAL = ["local line 1\n", "local line 2\n"]
REMOTE = ["remote line 1\n", "remote line 2\n"]
CONFLICTS = [Conflict(filename="known_hosts", local_line="a", remote_line="b", line_number=1)]


class TestLocalWins:
    def test_returns_local_lines(self):
        result = _local_wins(CONFLICTS, LOCAL, REMOTE)
        assert result == LOCAL

    def test_no_conflicts_still_returns_local(self):
        result = _local_wins([], LOCAL, REMOTE)
        assert result == LOCAL

    def test_returns_copy_not_same_object(self):
        result = _local_wins([], LOCAL, REMOTE)
        assert result is not LOCAL


class TestRemoteWins:
    def test_returns_remote_lines(self):
        result = _remote_wins(CONFLICTS, LOCAL, REMOTE)
        assert result == REMOTE

    def test_returns_copy_not_same_object(self):
        result = _remote_wins([], LOCAL, REMOTE)
        assert result is not REMOTE


class TestFailOnConflict:
    def test_raises_when_conflicts_present(self):
        with pytest.raises(ConflictError):
            _fail_on_conflict(CONFLICTS, LOCAL, REMOTE)

    def test_error_contains_conflict_count(self):
        with pytest.raises(ConflictError, match="1 conflict"):
            _fail_on_conflict(CONFLICTS, LOCAL, REMOTE)

    def test_no_conflict_returns_local(self):
        result = _fail_on_conflict([], LOCAL, REMOTE)
        assert result == LOCAL


class TestGetResolver:
    def test_local_strategy_returns_local_wins(self):
        resolver = get_resolver(Strategy.LOCAL_WINS)
        assert resolver is _local_wins

    def test_remote_strategy_returns_remote_wins(self):
        resolver = get_resolver(Strategy.REMOTE_WINS)
        assert resolver is _remote_wins

    def test_fail_strategy_returns_fail(self):
        resolver = get_resolver(Strategy.FAIL)
        assert resolver is _fail_on_conflict

    def test_string_value_accepted(self):
        resolver = get_resolver("local")
        assert resolver is _local_wins

    def test_unknown_strategy_raises(self):
        with pytest.raises(ValueError, match="Unknown strategy"):
            get_resolver("nonexistent")

    def test_resolver_callable(self):
        resolver = get_resolver(Strategy.LOCAL_WINS)
        result = resolver([], LOCAL, REMOTE)
        assert isinstance(result, list)
