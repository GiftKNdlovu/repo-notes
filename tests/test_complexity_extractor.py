"""Tests for the code complexity extractor."""
from pathlib import Path
from repo_notes.scanner import FileInfo
from repo_notes.extractors.complexity import ComplexityExtractor


def test_empty_project():
    result = ComplexityExtractor().extract(Path("/root"), [])
    assert result.complex_files == []


def test_simple_file(tmp_path: Path):
    f = tmp_path / "simple.py"
    f.write_text("x = 1\ny = 2\n")
    files = [FileInfo(f, Path("simple.py"), 12, ".py", False)]
    result = ComplexityExtractor().extract(tmp_path, files)
    assert result.avg_function_length == 0.0


def test_detects_long_function(tmp_path: Path):
    f = tmp_path / "long.py"
    lines = ["def long_fn():"]
    for i in range(20):
        lines.append(f"    x{i} = {i}")
    f.write_text("\n".join(lines) + "\n")
    files = [FileInfo(f, Path("long.py"), 200, ".py", False)]
    result = ComplexityExtractor().extract(tmp_path, files)
    assert any(e["file"] == "long.py" for e in result.complex_files)


def test_avg_function_length(tmp_path: Path):
    f = tmp_path / "stats.py"
    f.write_text("def short():\n    pass\n\ndef long_fn():\n    for i in range(10):\n        print(i)\n")
    files = [FileInfo(f, Path("stats.py"), 60, ".py", False)]
    result = ComplexityExtractor().extract(tmp_path, files)
    assert result.avg_function_length > 0


def test_max_nesting(tmp_path: Path):
    f = tmp_path / "deep.py"
    f.write_text("if a:\n    if b:\n        if c:\n            if d:\n                pass\n")
    files = [FileInfo(f, Path("deep.py"), 50, ".py", False)]
    result = ComplexityExtractor().extract(tmp_path, files)
    assert result.max_nesting >= 4
