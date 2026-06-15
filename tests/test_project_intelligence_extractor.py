"""Tests for the Project Intelligence extractor."""
from pathlib import Path

from repo_notes.extractors.project_intelligence import (
    ProjectIntelligenceExtractor,
    _extract_versions_from_package_json,
    _extract_versions_from_pyproject,
    _extract_versions_from_requirements,
)
from repo_notes.scanner import FileInfo


def test_empty_project():
    result = ProjectIntelligenceExtractor().extract(Path("/root"), [])
    assert result.total_tools == 0
    assert result.categories == {}


def test_detects_pytest(tmp_path: Path):
    f = tmp_path / "pyproject.toml"
    f.write_text("[tool.pytest.ini_options]\n")
    files = [FileInfo(f, Path("pyproject.toml"), 30, ".toml", False)]
    result = ProjectIntelligenceExtractor().extract(tmp_path, files)
    assert result.total_tools > 0
    tools = result.tools.get("Testing", [])
    assert any(t.name == "pytest" for t in tools)
    assert any(t.config_file == "pyproject.toml" for t in tools)


def test_detects_jest(tmp_path: Path):
    f = tmp_path / "package.json"
    f.write_text('{"devDependencies": {"jest": "^29.0.0"}}\n')
    files = [FileInfo(f, Path("package.json"), 50, ".json", False)]
    result = ProjectIntelligenceExtractor().extract(tmp_path, files)
    tools = result.tools.get("Testing", [])
    assert any(t.name == "jest" for t in tools)


def test_detects_docker(tmp_path: Path):
    f = tmp_path / "Dockerfile"
    f.write_text("FROM python:3.12\n")
    files = [FileInfo(f, Path("Dockerfile"), 20, "", False)]
    result = ProjectIntelligenceExtractor().extract(tmp_path, files)
    tools = result.tools.get("Containers", [])
    assert any(t.name == "Docker" for t in tools)


def test_detects_eslint(tmp_path: Path):
    f = tmp_path / ".eslintrc.json"
    f.write_text('{"rules": {}}\n')
    files = [FileInfo(f, Path(".eslintrc.json"), 15, ".json", False)]
    result = ProjectIntelligenceExtractor().extract(tmp_path, files)
    tools = result.tools.get("Linting", [])
    assert any(t.name == "ESLint" for t in tools)


def test_detects_fastapi(tmp_path: Path):
    f = tmp_path / "pyproject.toml"
    f.write_text('[project]\ndependencies = ["fastapi>=0.100.0"]\n')
    files = [FileInfo(f, Path("pyproject.toml"), 50, ".toml", False)]
    result = ProjectIntelligenceExtractor().extract(tmp_path, files)
    tools = result.tools.get("Frameworks", [])
    assert any(t.name == "FastAPI" for t in tools)


def test_detects_version_from_package_json(tmp_path: Path):
    f = tmp_path / "package.json"
    f.write_text('{"dependencies": {"express": "^4.18.0", "react": "^18.2.0"}}\n')
    files = [FileInfo(f, Path("package.json"), 70, ".json", False)]
    result = ProjectIntelligenceExtractor().extract(tmp_path, files)
    tools = result.tools.get("Frameworks", [])
    express = [t for t in tools if t.name == "Express"]
    assert len(express) > 0
    assert express[0].version == "^4.18.0"


def test_detects_version_from_pyproject():
    versions = _extract_versions_from_pyproject('[project]\ndependencies = ["flask>=2.3.0", "pytest>=7.0.0"]\n')
    assert versions.get("flask") == ">=2.3.0"
    assert versions.get("pytest") == ">=7.0.0"


def test_detects_version_from_requirements():
    versions = _extract_versions_from_requirements("flask>=2.3.0\npytest==7.4.0\n")
    assert versions.get("flask") == ">=2.3.0"
    assert versions.get("pytest") == "==7.4.0"


def test_extract_versions_from_package_json_direct():
    versions = _extract_versions_from_package_json('{"dependencies": {"express": "^4.18.0"}}')
    assert versions.get("express") == "^4.18.0"


def test_file_categories(tmp_path: Path):
    f = tmp_path / "README.md"
    f.write_text("# Project\n")
    g = tmp_path / ".gitignore"
    g.write_text("*.pyc\n")
    files = [
        FileInfo(f, Path("README.md"), 10, ".md", False),
        FileInfo(g, Path(".gitignore"), 7, "", False),
    ]
    result = ProjectIntelligenceExtractor().extract(tmp_path, files)
    assert "readme" in result.categories
    assert "git" in result.categories


def test_multiple_tools_same_file(tmp_path: Path):
    f = tmp_path / "package.json"
    f.write_text('{"dependencies": {"react": "^18.0.0", "express": "^4.0.0"}, "devDependencies": {"jest": "^29.0.0", "eslint": "^8.0.0"}}\n')
    files = [FileInfo(f, Path("package.json"), 120, ".json", False)]
    result = ProjectIntelligenceExtractor().extract(tmp_path, files)
    assert result.total_tools >= 4


def test_skips_binary(tmp_path: Path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02")
    files = [FileInfo(f, Path("data.bin"), 3, ".bin", True)]
    result = ProjectIntelligenceExtractor().extract(tmp_path, files)
    assert result.total_tools == 0
