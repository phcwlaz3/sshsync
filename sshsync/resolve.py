"""Conflict resolution strategies for sshsync."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Callable

from sshsync.conflict import ConflictError, ConflictReport, files_differ


class Strategy(str, Enum):
    """Available conflict resolution strategies."""

    LOCAL_WINS = "local"
    REMOTE_WINS = "remote"
    FAIL = "fail"


# Type alias for a resolver callable: (local_path, remote_path) -> resolved_text
Resolver = Callable[[Path, Path], str]


def _local_wins(local: Path, _remote: Path) -> str:
    return local.read_text(encoding="utf-8")


def _remote_wins(_local: Path, remote: Path) -> str:
    return remote.read_text(encoding="utf-8")


def _fail_on_conflict(local: Path, remote: Path) -> str:
    raise ConflictError(
        f"Conflict detected between {local} and {remote}. "
        "Resolve manually or choose a different strategy."
    )


_RESOLVERS: dict[Strategy, Resolver] = {
    Strategy.LOCAL_WINS: _local_wins,
    Strategy.REMOTE_WINS: _remote_wins,
    Strategy.FAIL: _fail_on_conflict,
}


def get_resolver(strategy: Strategy) -> Resolver:
    """Return the resolver function for the given strategy."""
    try:
        return _RESOLVERS[strategy]
    except KeyError:
        raise ValueError(f"Unknown strategy: {strategy!r}")


def resolve_file(
    local: Path,
    remote: Path,
    strategy: Strategy,
    report: ConflictReport | None = None,
) -> str:
    """Resolve a conflict between *local* and *remote* using *strategy*.

    If *report* is provided and the files do not differ, the original local
    content is returned immediately without invoking the resolver.
    """
    if not files_differ(local, remote):
        return local.read_text(encoding="utf-8")

    if report is not None and not report.has_conflicts:
        # Byte-level difference but no line conflicts — safe to take local.
        return local.read_text(encoding="utf-8")

    resolver = get_resolver(strategy)
    return resolver(local, remote)
