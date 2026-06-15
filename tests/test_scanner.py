"""Tests for the scanner module."""

import tempfile
from pathlib import Path

from repo_notes.scanner import is_binary, scan_directory


def test_scan_empty_directory():
    with tempfile.TemporaryDirectory() as tmp:
        files = list(scan_directory(Path(tmp)))
        assert files == []


def test_scan_single_file():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "hello.py").write_text("print('hello')")
        files = list(scan_directory(Path(tmp)))
        assert len(files) == 1
        assert files[0].relative_path == Path("hello.py")
        assert files[0].extension == ".py"
        assert not files[0].is_binary


def test_scan_nested_files():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "src" / "app" / "main.py").parent.mkdir(parents=True)
        (Path(tmp) / "src" / "app" / "main.py").write_text("def main(): pass")
        (Path(tmp) / "README.md").write_text("# Project")
        files = list(scan_directory(Path(tmp)))
        assert len(files) == 2


def test_ignores_hidden_dirs():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / ".hidden" / "secret.txt").parent.mkdir()
        (Path(tmp) / ".hidden" / "secret.txt").write_text("secret")
        (Path(tmp) / "visible.txt").write_text("hello")
        files = list(scan_directory(Path(tmp)))
        assert len(files) == 1
        assert files[0].relative_path == Path("visible.txt")


def test_ignores_pycache():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "__pycache__" / "foo.cpython.py").parent.mkdir()
        (Path(tmp) / "__pycache__" / "foo.cpython.py").write_text("x = 1")
        (Path(tmp) / "real.py").write_text("x = 2")
        files = list(scan_directory(Path(tmp)))
        assert len(files) == 1
        assert files[0].relative_path == Path("real.py")


def test_respects_gitignore():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / ".gitignore").write_text("*.log\nbuild/")
        (Path(tmp) / "app.log").write_text("error")
        (Path(tmp) / "src" / "main.py").parent.mkdir()
        (Path(tmp) / "src" / "main.py").write_text("print('ok')")
        (Path(tmp) / "build" / "out.o").parent.mkdir()
        (Path(tmp) / "build" / "out.o").write_text("binary")
        files = list(scan_directory(Path(tmp)))
        assert len(files) == 1
        assert files[0].relative_path == Path("src/main.py")


def test_extra_excludes():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "node_modules" / "pkg" / "index.js").parent.mkdir(parents=True)
        (Path(tmp) / "node_modules" / "pkg" / "index.js").write_text("module.exports = {}")
        (Path(tmp) / "src" / "app.js").parent.mkdir()
        (Path(tmp) / "src" / "app.js").write_text("console.log('hi')")
        files = list(scan_directory(Path(tmp)))
        assert len(files) == 1
        assert files[0].relative_path == Path("src/app.js")


def test_binary_detection():
    with tempfile.TemporaryDirectory() as tmp:
        bin_path = Path(tmp) / "data.bin"
        with bin_path.open("wb") as f:
            f.write(b"\x00\x01\x02\x03")
        assert is_binary(bin_path)
        text_path = Path(tmp) / "text.txt"
        text_path.write_text("hello world")
        assert not is_binary(text_path)


def test_include_hidden():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / ".config" / "settings.yaml").parent.mkdir()
        (Path(tmp) / ".config" / "settings.yaml").write_text("key: value")
        (Path(tmp) / "app.py").write_text("print('ok')")
        files_hidden = list(scan_directory(Path(tmp), include_hidden=True))
        assert len(files_hidden) == 2
        files_no_hidden = list(scan_directory(Path(tmp), include_hidden=False))
        assert len(files_no_hidden) == 1
