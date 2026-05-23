"""Merge logic for combining local and remote SSH config/known_hosts entries."""

from __future__ import annotations

from typing import List, Set


class MergeError(Exception):
    """Raised when a merge operation fails."""


def _split_lines(text: str) -> List[str]:
    """Return non-empty, stripped lines from *text*."""
    return [line for line in text.splitlines() if line.strip()]


def merge_known_hosts(local: str, remote: str) -> str:
    """Return a deduplicated union of two known_hosts contents.

    Lines are compared verbatim after stripping.  Order is preserved:
    local lines come first, then any new lines from remote.
    """
    local_lines: List[str] = _split_lines(local)
    remote_lines: List[str] = _split_lines(remote)

    seen: Set[str] = set(local_lines)
    merged: List[str] = list(local_lines)

    for line in remote_lines:
        if line not in seen:
            seen.add(line)
            merged.append(line)

    return "\n".join(merged) + ("\n" if merged else "")


def merge_ssh_config(local: str, remote: str) -> str:
    """Merge two SSH config files, preferring local Host blocks.

    Each ``Host`` block is treated as a unit.  Remote blocks whose
    ``Host`` alias does not appear locally are appended.
    """
    def _parse_blocks(text: str):
        """Return ordered list of (host_alias, block_lines) tuples."""
        blocks: List[tuple] = []
        current_alias: str | None = None
        current_lines: List[str] = []

        for line in text.splitlines():
            stripped = line.strip()
            if stripped.lower().startswith("host "):
                if current_alias is not None:
                    blocks.append((current_alias, current_lines))
                current_alias = stripped.split(None, 1)[1]
                current_lines = [line]
            elif current_alias is not None:
                current_lines.append(line)
            # lines before any Host block are ignored

        if current_alias is not None:
            blocks.append((current_alias, current_lines))

        return blocks

    local_blocks = _parse_blocks(local)
    remote_blocks = _parse_blocks(remote)

    local_aliases: Set[str] = {alias for alias, _ in local_blocks}

    merged_blocks = list(local_blocks)
    for alias, lines in remote_blocks:
        if alias not in local_aliases:
            merged_blocks.append((alias, lines))

    sections = ["\n".join(lines) for _, lines in merged_blocks]
    return "\n\n".join(sections) + ("\n" if sections else "")
