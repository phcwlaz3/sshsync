"""Status reporting: compare local SSH files against the repo snapshot."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from .ssh_files import ssh_dir, read_file, SSHFileError


@dataclass
class FileStatus:
    filename: str
    local_exists: bool
    repo_exists: bool
    in_sync: bool
    detail: str = ""


@dataclass
class SyncStatus:
    files: List[FileStatus] = field(default_factory=list)

    @property
    def all_in_sync(self) -> bool:
        return all(f.in_sync for f in self.files)

    def summary(self) -> str:
        lines = []
        for fs in self.files:
            icon = "✓" if fs.in_sync else "✗"
            lines.append(f"  [{icon}] {fs.filename}: {fs.detail}")
        return "\n".join(lines) if lines else "  (no managed files)"


def check_status(repo_dir: str | Path, managed_files: List[str]) -> SyncStatus:
    """Compare each managed file between local SSH dir and repo snapshot."""
    repo_path = Path(repo_dir)
    local_dir = ssh_dir()
    status = SyncStatus()

    for filename in managed_files:
        local_file = local_dir / filename
        repo_file = repo_path / filename

        local_exists = local_file.exists()
        repo_exists = repo_file.exists()

        if not local_exists and not repo_exists:
            status.files.append(FileStatus(
                filename=filename,
                local_exists=False,
                repo_exists=False,
                in_sync=True,
                detail="absent in both local and repo",
            ))
        elif not local_exists:
            status.files.append(FileStatus(
                filename=filename,
                local_exists=False,
                repo_exists=True,
                in_sync=False,
                detail="missing locally (repo has content)",
            ))
        elif not repo_exists:
            status.files.append(FileStatus(
                filename=filename,
                local_exists=True,
                repo_exists=False,
                in_sync=False,
                detail="not yet pushed to repo",
            ))
        else:
            try:
                local_content = read_file(local_file)
                repo_content = read_file(repo_file)
            except SSHFileError as exc:
                status.files.append(FileStatus(
                    filename=filename,
                    local_exists=local_exists,
                    repo_exists=repo_exists,
                    in_sync=False,
                    detail=f"read error: {exc}",
                ))
                continue

            if local_content == repo_content:
                status.files.append(FileStatus(
                    filename=filename,
                    local_exists=True,
                    repo_exists=True,
                    in_sync=True,
                    detail="up to date",
                ))
            else:
                status.files.append(FileStatus(
                    filename=filename,
                    local_exists=True,
                    repo_exists=True,
                    in_sync=False,
                    detail="local differs from repo snapshot",
                ))

    return status
