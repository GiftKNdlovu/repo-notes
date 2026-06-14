"""Tests for README generation."""

from pathlib import Path
import tempfile
import subprocess
from repo_notes.readme_generator import ReadmeGenerator
from repo_notes.extractors.readme_data import ReadmeData, ReadmeDataExtractor
from repo_notes.extractors.stats import StatsResult
from repo_notes.scanner import FileInfo


def test_header_with_name_and_description():
    gen = ReadmeGenerator(Path("proj"))
    data = ReadmeData(name="my-app", description="A cool app")
    md = gen.generate(readme_data=data)
    assert md.startswith("# my-app")
    assert "A cool app" in md


def test_header_without_description():
    gen = ReadmeGenerator(Path("proj"))
    data = ReadmeData(name="my-app")
    md = gen.generate(readme_data=data)
    assert md.startswith("# my-app")


def test_badges_with_version():
    gen = ReadmeGenerator(Path("proj"))
    data = ReadmeData(name="app", version="1.0.0")
    md = gen.generate(readme_data=data)
    assert "img.shields.io/badge/version-1.0.0-blue" in md


def test_badges_with_license():
    gen = ReadmeGenerator(Path("proj"))
    data = ReadmeData(name="app", license_type="MIT")
    md = gen.generate(readme_data=data)
    assert "img.shields.io/badge/license-MIT-green" in md


def test_badges_with_python():
    gen = ReadmeGenerator(Path("proj"))
    data = ReadmeData(name="app", python_requires=">=3.10")
    md = gen.generate(readme_data=data)
    assert "img.shields.io/badge/python" in md


def test_badges_with_ci():
    gen = ReadmeGenerator(Path("proj"))
    data = ReadmeData(name="app", ci_provider="GitHub Actions")
    md = gen.generate(readme_data=data)
    assert "img.shields.io/badge/ci-github_actions-orange" in md


def test_badges_with_tests():
    gen = ReadmeGenerator(Path("proj"))
    data = ReadmeData(name="app", has_tests=True)
    md = gen.generate(readme_data=data)
    assert "img.shields.io/badge/tests-passing-brightgreen" in md


def test_quick_start_with_install_cmd():
    gen = ReadmeGenerator(Path("proj"))
    data = ReadmeData(name="app", install_cmd="pip install app")
    md = gen.generate(readme_data=data)
    assert "## Quick Start" in md
    assert "pip install app" in md


def test_quick_start_without_install_cmd():
    gen = ReadmeGenerator(Path("proj"))
    data = ReadmeData(name="app")
    md = gen.generate(readme_data=data)
    assert "## Quick Start" in md


def test_features_with_deps():
    gen = ReadmeGenerator(Path("proj"))
    data = ReadmeData(name="app", runtime_deps=["click", "flask", "requests"])
    md = gen.generate(readme_data=data)
    assert "## Features" in md
    assert "click, flask, requests" in md


def test_features_with_tests_and_ci():
    gen = ReadmeGenerator(Path("proj"))
    data = ReadmeData(name="app", has_tests=True, has_ci=True, ci_provider="GitHub Actions")
    md = gen.generate(readme_data=data)
    assert "Test suite" in md
    assert "CI configured" in md


def test_stats_section():
    gen = ReadmeGenerator(Path("proj"))
    data = ReadmeData(name="app")
    md = gen.generate(
        readme_data=data,
        stats=StatsResult(
            total_files=10,
            total_lines=500,
            total_size=2048,
            by_language={"python": {"files": 8, "lines": 400, "size": 1500}},
            largest_files=[],
        ),
    )
    assert "## Code Statistics" in md
    assert "10" in md
    assert "500" in md
    assert "python" in md


def test_development_section():
    gen = ReadmeGenerator(Path("proj"))
    data = ReadmeData(name="app", dev_install_cmd="pip install -e .")
    md = gen.generate(readme_data=data)
    assert "## Development" in md
    assert "pip install -e ." in md
    assert "pytest" in md


def test_license_section():
    gen = ReadmeGenerator(Path("proj"))
    data = ReadmeData(name="app", license_type="MIT")
    md = gen.generate(readme_data=data)
    assert "## License" in md
    assert "MIT" in md


def test_license_default():
    gen = ReadmeGenerator(Path("proj"))
    data = ReadmeData(name="app")
    md = gen.generate(readme_data=data)
    assert "## License" in md
    assert "MIT" in md  # default fallback


# ReadmeDataExtractor tests


def test_extract_pyproject():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        pyproject = root / "pyproject.toml"
        pyproject.write_text("""[project]
name = "my-pkg"
version = "0.2.0"
description = "A test package"
requires-python = ">=3.11"
dependencies = ["click>=8.0", "rich>=12.0"]
""")
        files = [FileInfo(pyproject, Path("pyproject.toml"), pyproject.stat().st_size, ".toml", False)]
        data = ReadmeDataExtractor().extract(root, files)
        assert data.name == "my-pkg"
        assert data.version == "0.2.0"
        assert data.description == "A test package"
        assert data.python_requires == ">=3.11"
        assert "click" in data.runtime_deps
        assert "rich" in data.runtime_deps


def test_extract_package_json():
    import json
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        pkg = root / "package.json"
        pkg.write_text(json.dumps({
            "name": "my-js-pkg",
            "version": "1.0.0",
            "description": "A JS package",
            "dependencies": {"express": "^4.0", "lodash": "^4.0"},
            "devDependencies": {"jest": "^29.0"},
        }))
        files = [FileInfo(pkg, Path("package.json"), pkg.stat().st_size, ".json", False)]
        data = ReadmeDataExtractor().extract(root, files)
        assert data.name == "my-js-pkg"
        assert "express" in data.runtime_deps
        assert "jest" in data.dev_deps
        assert data.install_cmd == "npm install"


def test_extract_license_mit():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        lic = root / "LICENSE"
        lic.write_text("MIT License\nPermission is hereby granted...")
        name_file = root / "README.md"
        name_file.write_text("# proj")
        files = [
            FileInfo(lic, Path("LICENSE"), lic.stat().st_size, "", False),
            FileInfo(name_file, Path("README.md"), name_file.stat().st_size, ".md", False),
        ]
        data = ReadmeDataExtractor().extract(root, files)
        assert data.license_type == "MIT"


def test_extract_ci_github():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        workflow = root / ".github" / "workflows" / "test.yml"
        workflow.parent.mkdir(parents=True)
        workflow.write_text("name: CI")
        files = [FileInfo(workflow, Path(".github/workflows/test.yml"), workflow.stat().st_size, ".yml", False)]
        data = ReadmeDataExtractor().extract(root, files)
        assert data.has_ci
        assert data.ci_provider == "GitHub Actions"


def test_extract_has_tests():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        test_file = root / "tests" / "test_app.py"
        test_file.parent.mkdir()
        test_file.write_text("def test_pass(): pass")
        files = [
            FileInfo(test_file, Path("tests/test_app.py"), test_file.stat().st_size, ".py", False),
        ]
        data = ReadmeDataExtractor().extract(root, files)
        assert data.has_tests


def test_extract_docker():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        docker = root / "Dockerfile"
        docker.write_text("FROM python:3.11")
        files = [FileInfo(docker, Path("Dockerfile"), docker.stat().st_size, "", False)]
        data = ReadmeDataExtractor().extract(root, files)
        assert data.has_docker


def test_extract_empty_project():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = ReadmeDataExtractor().extract(root, [])
        assert data.name == root.name  # falls back to directory name
        assert data.install_cmd == "pip install ."


def test_extract_cargo_toml():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cargo = root / "Cargo.toml"
        cargo.write_text("""[package]
name = "my-rust-app"
version = "0.3.0"
description = "A Rust app"

[dependencies]
serde = "1.0"
tokio = "1.0"
""")
        files = [FileInfo(cargo, Path("Cargo.toml"), cargo.stat().st_size, ".toml", False)]
        data = ReadmeDataExtractor().extract(root, files)
        assert data.name == "my-rust-app"
        assert data.install_cmd == "cargo install"


def test_extract_go_mod():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        go_mod = root / "go.mod"
        go_mod.write_text("module github.com/user/my-go-app\n\ngo 1.21\n")
        files = [FileInfo(go_mod, Path("go.mod"), go_mod.stat().st_size, ".mod", False)]
        data = ReadmeDataExtractor().extract(root, files)
        assert data.name == "github.com/user/my-go-app"


# CLI integration test
def test_cli_readme_format_default():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "main.py").write_text("def main(): pass\n")
        result = subprocess.run(
            ["repo-notes", str(root), "--format", "readme"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        readme = root / "rnREADME.md"
        assert readme.exists()
        content = readme.read_text()
        assert "# " in content


def test_cli_readme_replace():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "main.py").write_text("def main(): pass\n")
        result = subprocess.run(
            ["repo-notes", str(root), "--format", "readme", "--replace-readme"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        readme = root / "README.md"
        assert readme.exists()
        content = readme.read_text()
        assert "# " in content


def test_cli_readme_replace_respects_existing():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "main.py").write_text("def main(): pass\n")
        (root / "README.md").write_text("existing content")
        result = subprocess.run(
            ["repo-notes", str(root), "--format", "readme", "--replace-readme"],
            capture_output=True,
            text=True,
        )
        assert "already exists" in result.stdout


def test_cli_readme_default_ignores_existing_readme():
    """rnREADME.md is always safe — no conflict with existing README.md."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "main.py").write_text("def main(): pass\n")
        (root / "README.md").write_text("existing content")
        result = subprocess.run(
            ["repo-notes", str(root), "--format", "readme"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert (root / "rnREADME.md").exists()


def test_cli_both_formats():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "main.py").write_text("def main(): pass\n")
        result = subprocess.run(
            ["repo-notes", str(root), "--format", "both"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert (root / "REPO_NOTES.md").exists()
        assert (root / "rnREADME.md").exists()