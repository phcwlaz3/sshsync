"""Utilities for reading, writing, and merging SSH config and known_hosts files."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import List

SSH_DIR = Path.home() / ".ssh"
DEFAULT_MANAGED = ["config", "known_hosts"]


class SSHFileError(Exception):
    """Raised when an SSH file operation fails."""


def ssh_dir() -> Path:
    """Return the user's ~/.ssh directory path."""
    return SSH_DIR


def read_file(path: Path) -> str:
    """Read and return the contents of *path*.

    Raises SSHFileError if the file cannot be read.
    """
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SSHFileError(f"Cannot read {path}: {exc}") from exc


def write_file(path: Path, content: str) -> None:
    """Write *content* to *path*, creating parent directories as needed.

    Raises SSHFileError if the file cannot be written.
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        # Ensure SSH config files are not world-readable
        os.chmod(path, 0o600)
    except OSError as exc:
        raise SSHFileError(f"Cannot write {path}: {exc}") from exc


def backup_file(path: Path) -> Path | None:
    """Create a *.bak* copy of *path* if it exists.

    Returns the backup path, or None if the original did not exist.
    """
    if not path.exists():
        return None
    backup = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, backup)
    return backup


def copy_to_repo(src: Path, repo_dir: Path, filename: str) -> Path:
    """Copy an SSH file from *src* into *repo_dir*.

    Returns the destination path inside the repo.
    """
    dest = repo_dir / filename
    try:
        shutil.copy2(src, dest)
    except OSError as exc:
        raise SSHFileError(f"Cannot copy {src} -> {dest}: {exc}") from exc
    return dest


def copy_from_repo(repo_dir: Path, filename: str, dest: Path) -> None:
    """Copy *filename* from *repo_dir* to *dest*, backing up existing file first."""
    src = repo_dir / filename
    if not src.exists():
        raise SSHFileError(f"File not found in repo: {src}")
    backup_file(dest)
    write_file(dest, read_file(src))


def list_managed_files(repo_dir: Path, managed: List[str]) -> List[Path]:
    """Return a list of managed file paths that exist inside *repo_dir*."""
    return [repo_dir / name for name in managed if (repo_dir / name).exists()]
