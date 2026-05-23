"""Read and write sshsync configuration from/to disk (INI format)."""

import configparser
from pathlib import Path
from typing import Optional

from sshsync.config import SyncConfig, DEFAULT_CONFIG_FILE


def load_config(path: Optional[Path] = None) -> SyncConfig:
    """Load SyncConfig from an INI file.  Returns defaults if file is absent."""
    config_path = Path(path) if path else DEFAULT_CONFIG_FILE
    parser = configparser.ConfigParser()

    if not config_path.exists():
        return SyncConfig()

    parser.read(config_path)
    data: dict = {}

    if "sshsync" in parser:
        section = parser["sshsync"]
        data["repo_url"] = section.get("repo_url", "")
        data["repo_dir"] = section.get("repo_dir", "")
        data["ssh_dir"] = section.get("ssh_dir", "")
        data["branch"] = section.get("branch", "main")
        data["auto_push"] = section.getboolean("auto_push", True)
        raw_files = section.get("managed_files", "config,known_hosts")
        data["managed_files"] = [f.strip() for f in raw_files.split(",") if f.strip()]

    return SyncConfig.from_dict(data)


def save_config(cfg: SyncConfig, path: Optional[Path] = None) -> None:
    """Persist a SyncConfig to an INI file, creating parent dirs as needed."""
    config_path = Path(path) if path else DEFAULT_CONFIG_FILE
    config_path.parent.mkdir(parents=True, exist_ok=True)

    parser = configparser.ConfigParser()
    d = cfg.to_dict()
    parser["sshsync"] = {
        "repo_url": d["repo_url"],
        "repo_dir": d["repo_dir"],
        "ssh_dir": d["ssh_dir"],
        "branch": d["branch"],
        "auto_push": str(d["auto_push"]).lower(),
        "managed_files": ", ".join(d["managed_files"]),
    }

    with config_path.open("w") as fh:
        parser.write(fh)
