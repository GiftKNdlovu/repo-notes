"""Tests for the duplicate files extractor."""
from pathlib import Path

from repo_notes.extractors.duplicates import DuplicateExtractor
from repo_notes.scanner import FileInfo


def test_empty_project():
    result = DuplicateExtractor().extract(Path("/root"), [])
    assert result.total_duplicates == 0


def test_no_duplicates(tmp_path: Path):
    a = tmp_path / "a.py"
    a.write_text("x = 1\n")
    b = tmp_path / "b.py"
    b.write_text("y = 2\n")
    files = [
        FileInfo(a, Path("a.py"), 5, ".py", False),
        FileInfo(b, Path("b.py"), 5, ".py", False),
    ]
    result = DuplicateExtractor().extract(tmp_path, files)
    assert result.total_duplicates == 0


def test_detects_exact_duplicate(tmp_path: Path):
    a = tmp_path / "a.py"
    a.write_text("x = 1\n")
    b = tmp_path / "b.py"
    b.write_text("x = 1\n")
    files = [
        FileInfo(a, Path("a.py"), 5, ".py", False),
        FileInfo(b, Path("b.py"), 5, ".py", False),
    ]
    result = DuplicateExtractor().extract(tmp_path, files)
    assert result.total_duplicates == 1
    assert result.duplicates[0]["similarity"] == 1.0


def test_detects_multiple_duplicates(tmp_path: Path):
    a = tmp_path / "a.py"
    a.write_text("x = 1\n")
    b = tmp_path / "b.py"
    b.write_text("x = 1\n")
    c = tmp_path / "c.py"
    c.write_text("x = 1\n")
    files = [
        FileInfo(a, Path("a.py"), 5, ".py", False),
        FileInfo(b, Path("b.py"), 5, ".py", False),
        FileInfo(c, Path("c.py"), 5, ".py", False),
    ]
    result = DuplicateExtractor().extract(tmp_path, files)
    assert result.total_duplicates == 2


def test_ignores_binary_files(tmp_path: Path):
    a = tmp_path / "a.bin"
    a.write_bytes(b"\x00\x01\x02")
    b = tmp_path / "b.bin"
    b.write_bytes(b"\x00\x01\x02")
    files = [
        FileInfo(a, Path("a.bin"), 3, ".bin", True),
        FileInfo(b, Path("b.bin"), 3, ".bin", True),
    ]
    result = DuplicateExtractor().extract(tmp_path, files)
    assert result.total_duplicates == 0
