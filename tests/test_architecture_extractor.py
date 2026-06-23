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


def test_coupling_hotspots_ordered(tmp_path: Path):
    (tmp_path / "hub.py").write_text("import a\nimport b\nimport c\n")
    (tmp_path / "a.py").write_text("import b\n")
    (tmp_path / "b.py").write_text("x = 1\n")
    (tmp_path / "c.py").write_text("import b\n")
    files = [
        FileInfo(tmp_path / "hub.py", Path("hub.py"), 30, ".py", False),
        FileInfo(tmp_path / "a.py", Path("a.py"), 10, ".py", False),
        FileInfo(tmp_path / "b.py", Path("b.py"), 5, ".py", False),
        FileInfo(tmp_path / "c.py", Path("c.py"), 10, ".py", False),
    ]
    result = ArchitectureExtractor().extract(tmp_path, files)
    assert len(result.coupling_hotspots) >= 1
    top = result.coupling_hotspots[0]
    # hub.py should be highest: total=3, outgoing=3, incoming=0
    assert top.file == "hub.py"
    assert top.total == 3
    assert top.outgoing == 3
    assert top.incoming == 0


def test_coupling_hotspots_limited_to_10():
    result = ArchitectureExtractor._compute_coupling_hotspots(
        {f"mod_{i}.py": [f"mod_{i+1}.py"] for i in range(20)},
        {f"mod_{i}.py" for i in range(21)},
    )
    assert len(result) == 10


def test_coupling_hotspots_empty_graph():
    result = ArchitectureExtractor._compute_coupling_hotspots({}, set())
    assert result == []


def test_coupling_hotspots_incoming_counted(tmp_path: Path):
    (tmp_path / "a.py").write_text("import b\n")
    (tmp_path / "b.py").write_text("import c\n")
    (tmp_path / "c.py").write_text("x = 1\n")
    (tmp_path / "d.py").write_text("import b\n")
    files = [
        FileInfo(tmp_path / "a.py", Path("a.py"), 10, ".py", False),
        FileInfo(tmp_path / "b.py", Path("b.py"), 10, ".py", False),
        FileInfo(tmp_path / "c.py", Path("c.py"), 5, ".py", False),
        FileInfo(tmp_path / "d.py", Path("d.py"), 10, ".py", False),
    ]
    result = ArchitectureExtractor().extract(tmp_path, files)
    hotspots = {h.file: h for h in result.coupling_hotspots}
    # a.py: outgoing=1 (b), incoming=0 => total=1
    assert hotspots["a.py"].outgoing == 1
    assert hotspots["a.py"].incoming == 0
    # b.py: outgoing=1 (c), incoming=2 (from a,d) => total=3
    assert hotspots["b.py"].outgoing == 1
    assert hotspots["b.py"].incoming == 2
    assert hotspots["b.py"].total == 3


def test_dead_code_true_unreferenced(tmp_path: Path):
    (tmp_path / "importer.py").write_text("import orphan\n")
    (tmp_path / "orphan.py").write_text("x = 1\n")
    files = [
        FileInfo(tmp_path / "importer.py", Path("importer.py"), 10, ".py", False),
        FileInfo(tmp_path / "orphan.py", Path("orphan.py"), 5, ".py", False),
    ]
    result = ArchitectureExtractor().extract(tmp_path, files)
    candidates = {c.file: c for c in result.dead_code_candidates}
    # importer.py has no inbound imports → candidate; orphan.py is imported → not a candidate
    assert "importer.py" in candidates
    assert "no inbound local imports" in candidates["importer.py"].reason
    assert "orphan.py" not in candidates


def test_dead_code_entry_point_excluded(tmp_path: Path):
    (tmp_path / "app.py").write_text("if __name__ == '__main__':\n    pass\n")
    (tmp_path / "orphan.py").write_text("import app\n")
    files = [
        FileInfo(tmp_path / "app.py", Path("app.py"), 30, ".py", False),
        FileInfo(tmp_path / "orphan.py", Path("orphan.py"), 10, ".py", False),
    ]
    result = ArchitectureExtractor().extract(tmp_path, files)
    candidates = {c.file: c for c in result.dead_code_candidates}
    assert "app.py" not in candidates  # entry point excluded
    assert "orphan.py" in candidates  # no inbound imports


def test_dead_code_test_file_excluded(tmp_path: Path):
    (tmp_path / "test_foo.py").write_text("def test_x(): pass\n")
    (tmp_path / "prod.py").write_text("x = 1\n")
    files = [
        FileInfo(tmp_path / "test_foo.py", Path("test_foo.py"), 20, ".py", False),
        FileInfo(tmp_path / "prod.py", Path("prod.py"), 5, ".py", False),
    ]
    result = ArchitectureExtractor().extract(tmp_path, files)
    candidates = {c.file: c for c in result.dead_code_candidates}
    assert "test_foo.py" not in candidates  # test file excluded
    assert "prod.py" in candidates  # no inbound imports


def test_dead_code_init_excluded(tmp_path: Path):
    (tmp_path / "__init__.py").write_text("x = 1\n")
    (tmp_path / "orphan.py").write_text("def f(): pass\n")
    files = [
        FileInfo(tmp_path / "__init__.py", Path("__init__.py"), 5, ".py", False),
        FileInfo(tmp_path / "orphan.py", Path("orphan.py"), 15, ".py", False),
    ]
    result = ArchitectureExtractor().extract(tmp_path, files)
    candidates = {c.file: c for c in result.dead_code_candidates}
    assert "__init__.py" not in candidates  # init file excluded
    assert "orphan.py" in candidates  # no inbound imports


def test_dead_code_scripts_dir_excluded(tmp_path: Path):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "tool.py").write_text("def run(): pass\n")
    (tmp_path / "orphan.py").write_text("def f(): pass\n")
    files = [
        FileInfo(tmp_path / "scripts" / "tool.py", Path("scripts/tool.py"), 15, ".py", False),
        FileInfo(tmp_path / "orphan.py", Path("orphan.py"), 10, ".py", False),
    ]
    result = ArchitectureExtractor().extract(tmp_path, files)
    candidates = {c.file: c for c in result.dead_code_candidates}
    assert "scripts/tool.py" not in candidates  # under scripts/ dir → excluded
    assert "orphan.py" in candidates


def test_dead_code_config_dir_excluded(tmp_path: Path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "settings.py").write_text("DEBUG = True\n")
    (tmp_path / "orphan.py").write_text("def f(): pass\n")
    files = [
        FileInfo(tmp_path / "config" / "settings.py", Path("config/settings.py"), 20, ".py", False),
        FileInfo(tmp_path / "orphan.py", Path("orphan.py"), 10, ".py", False),
    ]
    result = ArchitectureExtractor().extract(tmp_path, files)
    candidates = {c.file: c for c in result.dead_code_candidates}
    assert "config/settings.py" not in candidates  # under config/ dir → excluded
    assert "orphan.py" in candidates


def test_dead_code_imported_file_not_listed(tmp_path: Path):
    (tmp_path / "importer.py").write_text("import target\n")
    (tmp_path / "target.py").write_text("x = 1\n")
    files = [
        FileInfo(tmp_path / "importer.py", Path("importer.py"), 10, ".py", False),
        FileInfo(tmp_path / "target.py", Path("target.py"), 5, ".py", False),
    ]
    result = ArchitectureExtractor().extract(tmp_path, files)
    candidates = {c.file: c for c in result.dead_code_candidates}
    assert "target.py" not in candidates  # target.py IS imported by importer.py


def test_dead_code_importing_file_appears(tmp_path: Path):
    """A file that imports others but is not itself imported is a candidate."""
    (tmp_path / "a.py").write_text("import b\n")
    (tmp_path / "b.py").write_text("x = 1\n")
    files = [
        FileInfo(tmp_path / "a.py", Path("a.py"), 10, ".py", False),
        FileInfo(tmp_path / "b.py", Path("b.py"), 5, ".py", False),
    ]
    result = ArchitectureExtractor().extract(tmp_path, files)
    candidates = {c.file: c for c in result.dead_code_candidates}
    assert "a.py" in candidates  # a.py has no inbound imports
    assert "b.py" not in candidates  # b.py IS imported by a.py


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
