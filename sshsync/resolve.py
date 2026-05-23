"""Conflict resolution strategies for sshsync."""

from enum import Enum
from typing import List

from sshsync.conflict import Conflict, ConflictReport, ConflictError


class Strategy(str, Enum):
    LOCAL_WINS = "local"
    REMOTE_WINS = "remote"
    FAIL = "fail"


def _local_wins(conflicts: List[Conflict], local_lines: List[str], remote_lines: List[str]) -> List[str]:
    """Return local lines unchanged — local always wins."""
    return list(local_lines)


def _remote_wins(conflicts: List[Conflict], local_lines: List[str], remote_lines: List[str]) -> List[str]:
    """Return remote lines — remote always wins."""
    return list(remote_lines)


def _fail_on_conflict(conflicts: List[Conflict], local_lines: List[str], remote_lines: List[str]) -> List[str]:
    """Raise ConflictError if there are any conflicts."""
    if conflicts:
        raise ConflictError(
            f"{len(conflicts)} conflict(s) detected; resolve manually or choose a strategy.",
            conflicts=conflicts,
        )
    return list(local_lines)


_STRATEGY_MAP = {
    Strategy.LOCAL_WINS: _local_wins,
    Strategy.REMOTE_WINS: _remote_wins,
    Strategy.FAIL: _fail_on_conflict,
}


def get_resolver(strategy: Strategy):
    """Return the resolver callable for the given strategy.

    The returned callable has signature:
        (conflicts, local_lines, remote_lines) -> List[str]
    """
    try:
        return _STRATEGY_MAP[Strategy(strategy)]
    except (KeyError, ValueError):
        valid = ", ".join(s.value for s in Strategy)
        raise ValueError(f"Unknown strategy {strategy!r}. Valid options: {valid}")
