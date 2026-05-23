"""Configuration management for sshsync."""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


DEFAULT_SSH_DIR = Path.home() / ".ssh"
DEFAULT_REPO_DIR = Path.home() / ".sshsync"
DEFAULT_CONFIG_FILE = Path.home() / ".sshsync.conf"


@dataclass
class SyncConfig:
    """Holds runtime configuration for sshsync."""

    repo_url: str = ""
    repo_dir: Path = field(default_factory=lambda: DEFAULT_REPO_DIR)
    ssh_dir: Path = field(default_factory=lambda: DEFAULT_SSH_DIR)
    branch: str = "main"
    auto_push: bool = True
    managed_files: list = field(default_factory=lambda: ["config", "known_hosts"])

    @classmethod
    def from_dict(cls, data: dict) -> "SyncConfig":
        """Create a SyncConfig from a plain dictionary."""
        obj = cls()
        if "repo_url" in data:
            obj.repo_url = data["repo_url"]
        if "repo_dir" in data:
            obj.repo_dir = Path(data["repo_dir"])
        if "ssh_dir" in data:
            obj.ssh_dir = Path(data["ssh_dir"])
        if "branch" in data:
            obj.branch = data["branch"]
        if "auto_push" in data:
            obj.auto_push = bool(data["auto_push"])
        if "managed_files" in data:
            obj.managed_files = list(data["managed_files"])
        return obj

    def to_dict(self) -> dict:
        """Serialize config to a plain dictionary."""
        return {
            "repo_url": self.repo_url,
            "repo_dir": str(self.repo_dir),
            "ssh_dir": str(self.ssh_dir),
            "branch": self.branch,
            "auto_push": self.auto_push,
            "managed_files": self.managed_files,
        }

    def validate(self) -> list:
        """Return a list of validation error strings (empty means valid)."""
        errors = []
        if not self.repo_url:
            errors.append("repo_url must not be empty")
        if not self.branch:
            errors.append("branch must not be empty")
        if not self.managed_files:
            errors.append("managed_files must contain at least one entry")
        return errors
