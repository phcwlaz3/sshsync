"""Tests for sshsync.conflict."""

from pathlib import Path

import pytest

from sshsync.conflict import (
    Conflict,
    ConflictReport,
    detect_line_conflicts,
    files_differ,
)


# ---------------------------------------------------------------------------
# Conflict / ConflictReport helpers
# ---------------------------------------------------------------------------

class TestConflict:
    def test_str_includes_filename(self):
        c = Conflict(filename="known_hosts", local_line="a", remote_line="b", line_number=3)
        assert "known_hosts" in str(c)

    def test_str_includes_line_number(self):
        c = Conflict(filename="known_hosts", local_line="a", remote_line="b", line_number=7)
        assert "7" in str(c)

    def test_str_no_line_number(self):
        c = Conflict(filename="config", local_line="x", remote_line="y")
        s = str(c)
        assert "line" not in s


class TestConflictReport:
    def test_empty_report_has_no_conflicts(self):
        r = ConflictReport()
        assert not r.has_conflicts

    def test_add_increases_count(self):
        r = ConflictReport()
        r.add(Conflict("f", "a", "b"))
        assert len(r.conflicts) == 1
        assert r.has_conflicts

    def test_summary_no_conflicts(self):
        r = ConflictReport()
        assert "No conflicts" in r.summary()

    def test_summary_with_conflicts(self):
        r = ConflictReport()
        r.add(Conflict("config", "HostA", "HostB", line_number=2))
        s = r.summary()
        assert "1 conflict" in s
        assert "config" in s


# ---------------------------------------------------------------------------
# files_differ
# ---------------------------------------------------------------------------

class TestFilesDiffer:
    def test_identical_files_not_different(self, tmp_path):
        a = tmp_path / "a"
        b = tmp_path / "b"
        a.write_text("hello")
        b.write_text("hello")
        assert not files_differ(a, b)

    def test_different_content_detected(self, tmp_path):
        a = tmp_path / "a"
        b = tmp_path / "b"
        a.write_text("hello")
        b.write_text("world")
        assert files_differ(a, b)

    def test_missing_local_differs(self, tmp_path):
        a = tmp_path / "missing"
        b = tmp_path / "b"
        b.write_text("data")
        assert files_differ(a, b)

    def test_both_missing_not_different(self, tmp_path):
        a = tmp_path / "x"
        b = tmp_path / "y"
        assert not files_differ(a, b)


# ---------------------------------------------------------------------------
# detect_line_conflicts
# ---------------------------------------------------------------------------

class TestDetectLineConflicts:
    def test_identical_texts_no_conflicts(self):
        r = detect_line_conflicts("config", "a\nb\nc", "a\nb\nc")
        assert not r.has_conflicts

    def test_differing_line_reported(self):
        r = detect_line_conflicts("config", "a\nX\nc", "a\nY\nc")
        assert r.has_conflicts
        assert r.conflicts[0].line_number == 2

    def test_extra_remote_lines_ignored(self):
        r = detect_line_conflicts("config", "a", "a\nb\nc")
        assert not r.has_conflicts

    def test_multiple_conflicts(self):
        r = detect_line_conflicts("known_hosts", "1\n2\n3", "X\n2\nZ")
        assert len(r.conflicts) == 2
