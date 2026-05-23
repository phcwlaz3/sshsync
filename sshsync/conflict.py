"""Conflict detection and reporting for sshsync."""

from dataclasses import dataclass, field
from typing import List, Optional


class ConflictError(Exception):
    """Raised when unresolvable conflicts are detected."""

    def __init__(self, message: str, conflicts: Optional[List["Conflict"]] = None):
        super().__init__(message)
        self.conflicts: List["Conflict"] = conflicts or []


@dataclass
class Conflict:
    """Represents a single conflicting line between local and remote."""

    filename: str
    local_line: str
    remote_line: str
    line_number: Optional[int] = None

    def __str__(self) -> str:
        loc = f" (line {self.line_number})" if self.line_number is not None else ""
        return (
            f"Conflict in {self.filename}{loc}:\n"
            f"  local:  {self.local_line.rstrip()}\n"
            f"  remote: {self.remote_line.rstrip()}"
        )


@dataclass
class ConflictReport:
    """Aggregates conflicts found across one or more files."""

    conflicts: List[Conflict] = field(default_factory=list)

    def add(self, conflict: Conflict) -> None:
        self.conflicts.append(conflict)

    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0

    def by_file(self, filename: str) -> List[Conflict]:
        return [c for c in self.conflicts if c.filename == filename]

    def filenames(self) -> List[str]:
        seen: List[str] = []
        for c in self.conflicts:
            if c.filename not in seen:
                seen.append(c.filename)
        return seen

    def summary(self) -> str:
        if not self.has_conflicts():
            return "No conflicts."
        lines = [f"{len(self.conflicts)} conflict(s) detected:"]
        for filename in self.filenames():
            count = len(self.by_file(filename))
            lines.append(f"  {filename}: {count} conflict(s)")
        return "\n".join(lines)

    def __len__(self) -> int:
        return len(self.conflicts)
