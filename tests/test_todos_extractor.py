"""Tests for the TODO/FIXME/HACK extractor."""
from pathlib import Path
from repo_notes.scanner import FileInfo
from repo_notes.extractors.todos import TodosExtractor


def test_empty_project():
    ext = TodosExtractor()
    result = ext.extract(Path("/root"), [])
    assert result.items == []
    assert result.count_by_tag == {}


def test_detects_todo(tmp_path: Path):
    f = tmp_path / "main.py"
    f.write_text("# TODO: implement this\n")
    files = [FileInfo(f, Path("main.py"), 30, ".py", False)]
    result = TodosExtractor().extract(tmp_path, files)
    assert len(result.items) == 1
    assert result.items[0]["tag"] == "TODO"
    assert "implement this" in result.items[0]["message"]


def test_detects_fixme(tmp_path: Path):
    f = tmp_path / "buggy.py"
    f.write_text("# FIXME: off-by-one error\n")
    files = [FileInfo(f, Path("buggy.py"), 30, ".py", False)]
    result = TodosExtractor().extract(tmp_path, files)
    assert len(result.items) == 1
    assert result.items[0]["tag"] == "FIXME"


def test_detects_hack(tmp_path: Path):
    f = tmp_path / "workaround.py"
    f.write_text("# HACK: monkey-patch for speed\n")
    files = [FileInfo(f, Path("workaround.py"), 40, ".py", False)]
    result = TodosExtractor().extract(tmp_path, files)
    assert len(result.items) == 1
    assert result.items[0]["tag"] == "HACK"


def test_detects_multiple_in_one_file(tmp_path: Path):
    f = tmp_path / "main.py"
    f.write_text("# TODO: step 1\n# TODO: step 2\n# FIXME: crash\n")
    files = [FileInfo(f, Path("main.py"), 60, ".py", False)]
    result = TodosExtractor().extract(tmp_path, files)
    assert len(result.items) == 3
    assert result.count_by_tag["TODO"] == 2
    assert result.count_by_tag["FIXME"] == 1


def test_ignores_binary_files(tmp_path: Path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02")
    files = [FileInfo(f, Path("data.bin"), 3, ".bin", True)]
    result = TodosExtractor().extract(tmp_path, files)
    assert result.items == []


def test_correct_line_numbers(tmp_path: Path):
    f = tmp_path / "multi.py"
    f.write_text("line1\nline2\n# TODO: fix this\nline4\n")
    files = [FileInfo(f, Path("multi.py"), 35, ".py", False)]
    result = TodosExtractor().extract(tmp_path, files)
    assert len(result.items) == 1
    assert result.items[0]["line"] == 3


def test_tag_case_insensitive(tmp_path: Path):
    f = tmp_path / "main.py"
    f.write_text("# todo: lowercase\n")
    files = [FileInfo(f, Path("main.py"), 25, ".py", False)]
    result = TodosExtractor().extract(tmp_path, files)
    assert len(result.items) == 1
    assert result.items[0]["tag"] == "TODO"
