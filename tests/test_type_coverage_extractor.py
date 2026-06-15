"""Tests for the type coverage extractor."""
from pathlib import Path
from repo_notes.scanner import FileInfo
from repo_notes.extractors.type_coverage import TypeCoverageExtractor


def test_empty_project():
    result = TypeCoverageExtractor().extract(Path("/root"), [])
    assert result.typed_files == 0
    assert result.untyped_files == 0


def test_python_with_type_hints(tmp_path: Path):
    f = tmp_path / "typed.py"
    f.write_text("def greet(name: str) -> str:\n    return f'hello {name}'\n")
    files = [FileInfo(f, Path("typed.py"), 50, ".py", False)]
    result = TypeCoverageExtractor().extract(tmp_path, files)
    assert result.typed_files == 1
    assert result.untyped_files == 0


def test_python_without_type_hints(tmp_path: Path):
    f = tmp_path / "untyped.py"
    f.write_text("def greet(name):\n    return f'hello {name}'\n")
    files = [FileInfo(f, Path("untyped.py"), 45, ".py", False)]
    result = TypeCoverageExtractor().extract(tmp_path, files)
    assert result.typed_files == 0
    assert result.untyped_files == 1


def test_typescript_is_typed(tmp_path: Path):
    f = tmp_path / "app.ts"
    f.write_text("const x: number = 1;\n")
    files = [FileInfo(f, Path("app.ts"), 20, ".ts", False)]
    result = TypeCoverageExtractor().extract(tmp_path, files)
    assert result.typed_files == 1


def test_javascript_is_untyped(tmp_path: Path):
    f = tmp_path / "app.js"
    f.write_text("const x = 1;\n")
    files = [FileInfo(f, Path("app.js"), 15, ".js", False)]
    result = TypeCoverageExtractor().extract(tmp_path, files)
    assert result.untyped_files == 1


def test_mixed_types(tmp_path: Path):
    a = tmp_path / "typed.py"
    a.write_text("def f(x: int) -> int: return x\n")
    b = tmp_path / "untyped.py"
    b.write_text("def f(x): return x\n")
    files = [
        FileInfo(a, Path("typed.py"), 30, ".py", False),
        FileInfo(b, Path("untyped.py"), 25, ".py", False),
    ]
    result = TypeCoverageExtractor().extract(tmp_path, files)
    assert result.typed_files == 1
    assert result.untyped_files == 1
    assert result.by_extension[".py"]["files"] == 2
