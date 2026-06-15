"""Tests for the build scripts extractor."""
from pathlib import Path
from repo_notes.scanner import FileInfo
from repo_notes.extractors.scripts import ScriptsExtractor


def test_empty_project():
    ext = ScriptsExtractor()
    result = ext.extract(Path("/root"), [])
    assert result.package_json == {}
    assert result.makefile_targets == []
    assert result.justfile_recipes == []
    assert result.pyproject_scripts == {}


def test_parses_package_json(tmp_path: Path):
    f = tmp_path / "package.json"
    f.write_text('{"scripts": {"test": "jest", "build": "tsc"}}')
    files = [FileInfo(f, Path("package.json"), 50, ".json", False)]
    result = ScriptsExtractor().extract(tmp_path, files)
    assert result.package_json["test"] == "jest"
    assert result.package_json["build"] == "tsc"


def test_parses_makefile(tmp_path: Path):
    f = tmp_path / "Makefile"
    f.write_text("build:\n\techo build\ntest:\n\techo test\n.PHONY: build test\n")
    files = [FileInfo(f, Path("Makefile"), 50, "", False)]
    result = ScriptsExtractor().extract(tmp_path, files)
    assert "build" in result.makefile_targets
    assert "test" in result.makefile_targets
    assert ".PHONY" not in result.makefile_targets


def test_parses_justfile(tmp_path: Path):
    f = tmp_path / "justfile"
    f.write_text("build:\n    cargo build\ntest:\n    cargo test\n")
    files = [FileInfo(f, Path("justfile"), 40, "", False)]
    result = ScriptsExtractor().extract(tmp_path, files)
    assert "build" in result.justfile_recipes
    assert "test" in result.justfile_recipes


def test_parses_pyproject_scripts(tmp_path: Path):
    f = tmp_path / "pyproject.toml"
    f.write_text('[project]\nscripts = {dev = "myapp dev"}\n')
    files = [FileInfo(f, Path("pyproject.toml"), 50, ".toml", False)]
    result = ScriptsExtractor().extract(tmp_path, files)
    assert result.pyproject_scripts["dev"] == "myapp dev"


def test_handles_missing_files(tmp_path: Path):
    ext = ScriptsExtractor()
    result = ext.extract(tmp_path, [])
    assert result.package_json == {}
    assert result.makefile_targets == []
