"""Tests for the code complexity extractor."""
from pathlib import Path

from repo_notes.extractors.complexity import ComplexityExtractor
from repo_notes.scanner import FileInfo


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
    assert result.max_nesting == 4


def test_python_nesting_dedent_siblings(tmp_path: Path):
    f = tmp_path / "siblings.py"
    f.write_text(
        "if a:\n"
        "    pass\n"
        "if b:\n"
        "    pass\n"
        "for x in range(10):\n"
        "    print(x)\n"
    )
    files = [FileInfo(f, Path("siblings.py"), 70, ".py", False)]
    result = ComplexityExtractor().extract(tmp_path, files)
    assert result.max_nesting == 1


def test_python_nesting_class_and_methods(tmp_path: Path):
    f = tmp_path / "class_method.py"
    f.write_text(
        "class Foo:\n"
        "    def bar(self):\n"
        "        if a:\n"
        "            if b:\n"
        "                pass\n"
        "    def baz(self):\n"
        "        pass\n"
    )
    files = [FileInfo(f, Path("class_method.py"), 85, ".py", False)]
    result = ComplexityExtractor().extract(tmp_path, files)
    # class (1) + def (2) + if a (3) + if b (4)
    assert result.max_nesting == 4


def test_python_nesting_flat_file(tmp_path: Path):
    f = tmp_path / "flat.py"
    f.write_text(
        "x = 1\n"
        "y = 2\n"
        "z = x + y\n"
    )
    files = [FileInfo(f, Path("flat.py"), 20, ".py", False)]
    result = ComplexityExtractor().extract(tmp_path, files)
    assert result.max_nesting == 0


def test_brace_nesting_non_python(tmp_path: Path):
    f = tmp_path / "deep.js"
    f.write_text(
        "if (a) {\n"
        "    if (b) {\n"
        "        if (c) {\n"
        "            console.log('deep');\n"
        "        }\n"
        "    }\n"
        "}\n"
    )
    files = [FileInfo(f, Path("deep.js"), 80, ".js", False)]
    result = ComplexityExtractor().extract(tmp_path, files)
    assert result.max_nesting >= 3


def test_python_nesting_max_nesting_reported(tmp_path: Path):
    """Verify max_nesting in ComplexityResult reflects deepest file."""
    f = tmp_path / "deep.py"
    f.write_text(
        "if a:\n"
        "    if b:\n"
        "        if c:\n"
        "            if d:\n"
        "                if e:\n"
        "                    pass\n"
    )
    files = [FileInfo(f, Path("deep.py"), 60, ".py", False)]
    result = ComplexityExtractor().extract(tmp_path, files)
    assert result.max_nesting == 5


def test_python_nesting_else_elif_same_level(tmp_path: Path):
    """else/elif should not increase nesting beyond their matching if."""
    f = tmp_path / "elif_else.py"
    f.write_text(
        "if a:\n"
        "    if b:\n"
        "        pass\n"
        "    elif c:\n"
        "        pass\n"
        "    else:\n"
        "        pass\n"
    )
    files = [FileInfo(f, Path("elif_else.py"), 60, ".py", False)]
    result = ComplexityExtractor().extract(tmp_path, files)
    assert result.max_nesting == 2
