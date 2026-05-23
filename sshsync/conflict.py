"""Conflict detection and resolution helpers for sshsync."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class ConflictError(Exception):
    """Raised when an unresolvable conflict is detected."""


@dataclass
class Conflict:
    """Represents a single conflicting entry between local and remote."""

    filename: str
    local_line: str
    remote_line: str
    line_number: Optional[int] = None

    def __str__(self) -> str:
        loc = f" (line {self.line_number})" if self.line_number is not None else ""
        return (
            f"Conflict in {self.filename}{loc}:\n"
            f"  local : {self.local_line!r}\n"
            f"  remote: {self.remote_line!r}"
        )


@dataclass
class ConflictReport:
    """Aggregates all conflicts found during a sync check."""

    conflicts: List[Conflict] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return bool(self.conflicts)

    def add(self, conflict: Conflict) -> None:
        self.conflicts.append(conflict)

    def summary(self) -> str:
        if not self.has_conflicts:
            return "No conflicts detected."
        lines = [f"{len(self.conflicts)} conflict(s) detected:"]
        for c in self.conflicts:
            lines.append(str(c))
        return "\n".join(lines)


def _file_hash(path: Path) -> str:
    """Return the SHA-256 hex digest of a file's contents."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def files_differ(local: Path, remote: Path) -> bool:
    """Return True when *local* and *remote* have different content."""
    if not local.exists() or not remote.exists():
        return local.exists() != remote.exists()
    return _file_hash(local) != _file_hash(remote)


def detect_line_conflicts(filename: str, local_text: str, remote_text: str) -> ConflictReport:
    """Compare line-by-line and report lines that differ at the same position."""
    report = ConflictReport()
    local_lines = local_text.splitlines()
    remote_lines = remote_text.splitlines()
    for i, (loc, rem) in enumerate(zip(local_lines, remote_lines), start=1):
        if loc != rem:
            report.add(Conflict(filename=filename, local_line=loc, remote_line=rem, line_number=i))
    return report
