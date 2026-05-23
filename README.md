# sshsync

> Keep your SSH config and known\_hosts in sync across multiple machines via a git repo.

---

## Installation

```bash
pip install sshsync
```

Or install from source:

```bash
git clone https://github.com/youruser/sshsync.git && cd sshsync && pip install .
```

---

## Usage

Initialize sshsync with your git repository:

```bash
sshsync init git@github.com:youruser/ssh-config-repo.git
```

Push your current SSH config and known\_hosts to the repo:

```bash
sshsync push
```

Pull and apply the latest config on another machine:

```bash
sshsync pull
```

Check sync status:

```bash
sshsync status
```

sshsync manages `~/.ssh/config` and `~/.ssh/known_hosts`, committing changes to your designated git repository so every machine stays up to date.

---

## How It Works

1. On first run, `sshsync init` links your SSH directory to a git repo.
2. `sshsync push` stages, commits, and pushes any local changes.
3. `sshsync pull` fetches the latest changes and merges them into your local SSH files.
4. Conflicts are flagged for manual review before applying.

---

## Requirements

- Python 3.8+
- Git installed and configured
- SSH key access to your sync repository

---

## License

MIT © 2024 youruser