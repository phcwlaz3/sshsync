"""Command-line interface for sshsync."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config_io import load_config, save_config
from .config import validate
from .git_ops import clone_repo, pull, push, GitError
from .sync import push_ssh_files, pull_ssh_files, SyncError
from .status import check_status


DEFAULT_CONFIG_PATH = Path.home() / ".sshsync.toml"


def _get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sshsync",
        description="Keep SSH config and known_hosts in sync via a git repo.",
    )
    parser.add_argument(
        "--config", default=str(DEFAULT_CONFIG_PATH),
        help="Path to sshsync config file (default: ~/.sshsync.toml)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Show sync status for managed files")
    sub.add_parser("push", help="Push local SSH files to the repo")
    sub.add_parser("pull", help="Pull SSH files from the repo")

    init_p = sub.add_parser("init", help="Initialise config and clone repo")
    init_p.add_argument("repo_url", help="Git remote URL to sync against")
    init_p.add_argument(
        "--repo-dir", default=str(Path.home() / ".sshsync_repo"),
        help="Local directory to clone into",
    )

    return parser


def cmd_status(cfg) -> int:
    status = check_status(cfg.repo_dir, cfg.managed_files)
    print("SSH sync status:")
    print(status.summary())
    return 0 if status.all_in_sync else 1


def cmd_push(cfg) -> int:
    try:
        pull(cfg.repo_dir)
        push_ssh_files(cfg.repo_dir, cfg.managed_files)
        push(cfg.repo_dir, cfg.branch)
        print("Push complete.")
        return 0
    except (SyncError, GitError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


def cmd_pull(cfg) -> int:
    try:
        pull(cfg.repo_dir)
        pull_ssh_files(cfg.repo_dir, cfg.managed_files)
        print("Pull complete.")
        return 0
    except (SyncError, GitError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


def cmd_init(args) -> int:
    from .config import SyncConfig
    cfg = SyncConfig(repo_url=args.repo_url, repo_dir=args.repo_dir)
    try:
        validate(cfg)
        clone_repo(cfg.repo_url, cfg.repo_dir)
        save_config(cfg, args.config)
        print(f"Initialised. Config written to {args.config}")
        return 0
    except (ValueError, GitError) as exc:
        print(f"Init failed: {exc}", file=sys.stderr)
        return 2


def main(argv=None) -> int:
    parser = _get_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        return cmd_init(args)

    try:
        cfg = load_config(args.config)
    except FileNotFoundError:
        print(
            f"Config not found at {args.config}. Run `sshsync init <repo_url>` first.",
            file=sys.stderr,
        )
        return 1

    dispatch = {"status": cmd_status, "push": cmd_push, "pull": cmd_pull}
    return dispatch[args.command](cfg)


if __name__ == "__main__":
    sys.exit(main())
