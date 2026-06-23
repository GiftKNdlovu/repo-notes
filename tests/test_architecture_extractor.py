"""Tests for the architecture extractor."""
from pathlib import Path

from repo_notes.extractors.architecture import ArchitectureExtractor
from repo_notes.scanner import FileInfo


def test_empty_project():
    result = ArchitectureExtractor().extract(Path("/root"), [])
    assert result.layers == {}
    assert result.import_graph == {}
    assert result.entry_points == []
    assert result.circular_deps == []


def test_simple_import_chain(tmp_path: Path):
    (tmp_path / "a.py").write_text("import b\n")
    (tmp_path / "b.py").write_text("import c\n")
    (tmp_path / "c.py").write_text("x = 1\n")
    files = [
        FileInfo(tmp_path / "a.py", Path("a.py"), 10, ".py", False),
        FileInfo(tmp_path / "b.py", Path("b.py"), 10, ".py", False),
        FileInfo(tmp_path / "c.py", Path("c.py"), 10, ".py", False),
    ]
    result = ArchitectureExtractor().extract(tmp_path, files)
    assert result.import_graph == {"a.py": ["b"], "b.py": ["c"]}
    assert result.circular_deps == []
    assert "a.py" in result.import_graph


def test_no_imports(tmp_path: Path):
    (tmp_path / "x.py").write_text("x = 1\n")
    (tmp_path / "y.py").write_text("y = 2\n")
    files = [
        FileInfo(tmp_path / "x.py", Path("x.py"), 5, ".py", False),
        FileInfo(tmp_path / "y.py", Path("y.py"), 5, ".py", False),
    ]
    result = ArchitectureExtractor().extract(tmp_path, files)
    assert result.import_graph == {}
    assert result.circular_deps == []


def test_circular_dependency(tmp_path: Path):
    (tmp_path / "a.py").write_text("from b import bar\n")
    (tmp_path / "b.py").write_text("from c import baz\n")
    (tmp_path / "c.py").write_text("from a import foo\n")
    files = [
        FileInfo(tmp_path / "a.py", Path("a.py"), 25, ".py", False),
        FileInfo(tmp_path / "b.py", Path("b.py"), 25, ".py", False),
        FileInfo(tmp_path / "c.py", Path("c.py"), 25, ".py", False),
    ]
    result = ArchitectureExtractor().extract(tmp_path, files)
    assert result.import_graph == {"a.py": ["b"], "b.py": ["c"], "c.py": ["a"]}
    assert len(result.circular_deps) >= 1
    cycle = result.circular_deps[0]
    assert len(cycle) >= 3
    # The cycle should have a, b, c, a
    assert cycle[0] == cycle[-1]
    assert set(cycle) == {"a.py", "b.py", "c.py", "a.py"}


def test_circular_dependency_two_nodes(tmp_path: Path):
    (tmp_path / "a.py").write_text("from b import bar\n")
    (tmp_path / "b.py").write_text("from a import foo\n")
    files = [
        FileInfo(tmp_path / "a.py", Path("a.py"), 25, ".py", False),
        FileInfo(tmp_path / "b.py", Path("b.py"), 25, ".py", False),
    ]
    result = ArchitectureExtractor().extract(tmp_path, files)
    assert len(result.circular_deps) >= 1
    cycle = result.circular_deps[0]
    assert len(cycle) == 3
    assert cycle[0] == cycle[-1]
    assert cycle[0] == "a.py"


def test_dependency_across_languages(tmp_path: Path):
    (tmp_path / "app.js").write_text("import {x} from './utils';\n")
    (tmp_path / "utils.js").write_text("exports.y = 1;\n")
    files = [
        FileInfo(tmp_path / "app.js", Path("app.js"), 30, ".js", False),
        FileInfo(tmp_path / "utils.js", Path("utils.js"), 15, ".js", False),
    ]
    result = ArchitectureExtractor().extract(tmp_path, files)
    assert result.import_graph == {"app.js": ["./utils"]}
    assert result.circular_deps == []
