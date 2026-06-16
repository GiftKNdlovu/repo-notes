"""Tests for the AI agent-focused notes generator."""

import subprocess
import tempfile
from pathlib import Path

from repo_notes.agents_generator import AgentsGenerator
from repo_notes.extractors import (
    ApiEndpointResult,
    ArchitectureResult,
    CicdResult,
    ComplexityResult,
    DatabaseResult,
    DetectedTool,
    GitResult,
    ProjectIntelligenceResult,
    ScriptsResult,
    SecurityResult,
    StatsResult,
)


def test_agents_generator_renders_project_brief():
    gen = AgentsGenerator(Path("repo"))
    md = gen.generate(
        project_intelligence=ProjectIntelligenceResult(
            tools={
                "Languages": [DetectedTool(name="Python", category="Languages")],
                "Testing": [DetectedTool(name="pytest", category="Testing")],
            }
        ),
        stats=StatsResult(
            total_files=10,
            total_lines=500,
            total_size=2048,
            by_language={"python": {"files": 8, "lines": 450, "size": 1800}},
        ),
        git=GitResult(is_repo=True, current_branch="main"),
    )

    assert md.startswith("# Agent Notes: repo")
    assert "## Project Brief" in md
    assert "Python" in md
    assert "10 files, 500 lines" in md
    assert "`main`" in md


def test_agents_generator_includes_commands_and_paths():
    gen = AgentsGenerator(Path("repo"))
    md = gen.generate(
        project_intelligence=ProjectIntelligenceResult(
            tools={
                "Testing": [DetectedTool(name="pytest", category="Testing")],
                "Linting": [DetectedTool(name="Ruff", category="Linting")],
            },
            categories={"readme": [Path("README.md")]},
        ),
        scripts=ScriptsResult(pyproject_scripts={"repo-notes": "repo_notes.__main__:main"}),
        arch=ArchitectureResult(
            entry_points=[Path("src/repo_notes/cli.py")],
            layers={"tests": [Path("tests/test_integration.py")]},
        ),
    )

    assert "## How To Work Here" in md
    assert "`repo-notes`" in md
    assert "`pytest`" in md
    assert "`ruff check src/ tests/`" in md
    assert "## Important Paths" in md
    assert "`src/repo_notes/cli.py`" in md
    assert "`README.md`" in md


def test_agents_generator_marks_test_fixture_findings():
    gen = AgentsGenerator(Path("repo"))
    md = gen.generate(
        security=SecurityResult(
            findings=[
                {
                    "file": "tests/test_extractors.py",
                    "type": "AWS Access Key",
                    "line": 1,
                    "preview": "AKIA************",
                }
            ],
        ),
        database=DatabaseResult(model_files=[Path("tests/test_database.py")], model_count=1),
        api_endpoints=ApiEndpointResult(
            endpoints=[{"file": "tests/test_api.py", "framework": "FastAPI"}]
        ),
        cicd=CicdResult(),
        complexity=ComplexityResult(
            complex_files=[{"file": "src/repo_notes/generator.py", "score": 100}]
        ),
    )

    assert "security finding(s) appear to be test fixtures" in md
    assert "Database/ORM signals appear only in tests" in md
    assert "API endpoint patterns appear only in tests" in md
    assert "`src/repo_notes/generator.py`" in md
    assert "No CI/CD configuration was detected" in md


def test_cli_agents_format_default():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "main.py").write_text("def main(): pass\n")

        result = subprocess.run(
            ["repo-notes", str(root), "--format", "agents"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        output = root / "REPO_NOTES_AGENTS.md"
        assert output.exists()
        content = output.read_text()
        assert content.startswith("# Agent Notes:")
        assert "## Agent Instructions" in content


def test_cli_agents_format_output_override():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "main.py").write_text("def main(): pass\n")
        output = root / "custom-agents.md"

        result = subprocess.run(
            ["repo-notes", str(root), "--format", "agents", "--output", str(output)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert output.exists()
        assert not (root / "REPO_NOTES_AGENTS.md").exists()


def test_cli_both_includes_agents_output():
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
        assert (root / "REPO_NOTES_AGENTS.md").exists()
