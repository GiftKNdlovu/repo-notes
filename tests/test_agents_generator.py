"""Tests for AGENTS.md generation and JSON serialization."""

import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from repo_notes.agents_generator import AgentsGenerator
from repo_notes.cli import _json_convert
from repo_notes.extractors.architecture import ArchitectureResult
from repo_notes.extractors.readme_data import ReadmeData
from repo_notes.extractors.scripts import ScriptsResult
from repo_notes.extractors.stats import StatsResult
from repo_notes.extractors.structure import StructureResult


def test_header_with_name_and_description():
    gen = AgentsGenerator(Path("my-app"))
    data = ReadmeData(name="my-app", description="A cool app")
    md = gen.generate(readme_data=data)
    assert md.startswith("# my-app")
    assert "A cool app" in md


def test_header_falls_back_to_dir_name():
    gen = AgentsGenerator(Path("fallback-dir"))
    md = gen.generate()
    assert md.startswith("# fallback-dir")


def test_tech_stack_languages():
    gen = AgentsGenerator(Path("root"))
    stats = StatsResult(
        total_files=5, total_lines=100, total_size=500,
        by_language={"Python": {"files": 3, "lines": 60, "size": 300},
                     "TypeScript": {"files": 2, "lines": 40, "size": 200}},
        largest_files=[],
    )
    md = gen.generate(stats=stats)
    assert "## Tech Stack" in md
    assert "Python" in md
    assert "TypeScript" in md


def test_tech_stack_with_runtime_deps():
    gen = AgentsGenerator(Path("root"))
    data = ReadmeData(name="app", runtime_deps=["click", "flask", "requests"])
    md = gen.generate(readme_data=data)
    assert "Runtime deps" in md
    assert "click, flask, requests" in md


def test_tech_stack_filters_unknown():
    gen = AgentsGenerator(Path("root"))
    stats = StatsResult(
        total_files=5, total_lines=100, total_size=500,
        by_language={"python": {"files": 3, "lines": 60, "size": 300},
                     "unknown": {"files": 1, "lines": 10, "size": 50},
                     "": {"files": 1, "lines": 5, "size": 25}},
        largest_files=[],
    )
    md = gen.generate(stats=stats)
    assert "Python" in md
    assert "unknown" not in md


def test_tech_stack_omitted_when_no_data():
    gen = AgentsGenerator(Path("root"))
    md = gen.generate()
    assert "## Tech Stack" not in md


def test_project_structure():
    gen = AgentsGenerator(Path("root"))
    structure = StructureResult(tree="root/\n  main.py\n  src/\n    app.py", file_count=2, dir_count=1)
    md = gen.generate(structure=structure)
    assert "## Project Structure" in md
    assert "root/" in md
    assert "main.py" in md
    assert "2 files" in md
    assert "1 directories" in md


def test_project_structure_omitted_when_no_data():
    gen = AgentsGenerator(Path("root"))
    md = gen.generate()
    assert "## Project Structure" not in md


def test_repo_map():
    gen = AgentsGenerator(Path("root"))
    structure = StructureResult(tree="root/\nsrc/\n  app.py\ntests/\n  test_app.py\nREADME.md", file_count=3, dir_count=2)
    md = gen.generate(structure=structure)
    assert "## Repository Map" in md
    repo_map = md.split("## Repository Map", 1)[1].split("## Key Commands", 1)[0]
    assert "**src/**" in repo_map
    assert "**tests/**" in repo_map
    assert "**README.md**" in repo_map
    assert "Source code" in repo_map
    assert "Test suite" in repo_map
    assert "Project readme" in repo_map
    assert "app.py" not in repo_map
    assert "test_app.py" not in repo_map


def test_repo_map_file_labels():
    gen = AgentsGenerator(Path("root"))
    structure = StructureResult(tree="root/\nREADME.md\npyproject.toml\nMakefile\nunknown_file.x", file_count=4, dir_count=0)
    md = gen.generate(structure=structure)
    repo_map = md.split("## Repository Map", 1)[1].split("## Key Commands", 1)[0]
    assert "**README.md** — Project readme" in repo_map
    assert "**pyproject.toml** — Python project configuration" in repo_map
    assert "**Makefile** — Build automation" in repo_map
    assert "**unknown_file.x**" in repo_map
    assert "Build automation" in repo_map
    # unknown files get no label — line should not contain " — "
    for line in repo_map.split("\n"):
        if "unknown_file.x" in line:
            assert "—" not in line


def test_architecture_omitted_when_no_data():
    gen = AgentsGenerator(Path("root"))
    md = gen.generate()
    assert "## Architecture" not in md


def test_architecture_with_circular_deps():
    gen = AgentsGenerator(Path("root"))
    arch = ArchitectureResult(
        layers={},
        import_graph={"mod_a.py": ["mod_b"], "mod_b.py": ["mod_c"], "mod_c.py": ["mod_a"]},
        entry_points=[],
        circular_deps=[["mod_a.py", "mod_b.py", "mod_c.py", "mod_a.py"]],
    )
    md = gen.generate(arch=arch)
    arch_section = md.split("## Architecture", 1)[1].split("## Key Commands", 1)[0]
    assert "**1** circular dependency detected" in arch_section
    assert "mod_a.py" in arch_section
    assert "mod_b.py" in arch_section
    assert "mod_c.py" in arch_section


def test_architecture_with_coupling_hotspots():
    gen = AgentsGenerator(Path("root"))
    from repo_notes.extractors.architecture import CouplingHotspot
    arch = ArchitectureResult(
        layers={},
        import_graph={"hub.py": ["a", "b"], "a.py": ["b"]},
        coupling_hotspots=[
            CouplingHotspot(file="hub.py", outgoing=2, incoming=0, total=2),
            CouplingHotspot(file="a.py", outgoing=1, incoming=0, total=1),
        ],
    )
    md = gen.generate(arch=arch)
    arch_section = md.split("## Architecture", 1)[1].split("## Key Commands", 1)[0]
    assert "hub.py" in arch_section
    assert "2 connections" in arch_section
    assert "a.py" in arch_section


def test_architecture_with_dead_code_candidates():
    gen = AgentsGenerator(Path("root"))
    from repo_notes.extractors.architecture import DeadCodeCandidate
    arch = ArchitectureResult(
        import_graph={"a.py": ["b"]},
        dead_code_candidates=[
            DeadCodeCandidate(file="orphan.py", reason="no inbound local imports; no outbound local imports"),
        ],
    )
    md = gen.generate(arch=arch)
    arch_section = md.split("## Architecture", 1)[1].split("## Key Commands", 1)[0]
    assert "Low-reachability" in arch_section
    assert "orphan.py" in arch_section


def test_architecture_with_layers_only():
    gen = AgentsGenerator(Path("root"))
    arch = ArchitectureResult(
        layers={"routes": [Path("routes/")], "models": [Path("models/")]},
        import_graph={},
        entry_points=[],
        circular_deps=[],
    )
    md = gen.generate(arch=arch)
    arch_section = md.split("## Architecture", 1)[1].split("## Key Commands", 1)[0]
    assert "**2** layers detected" in arch_section
    assert "routes" in arch_section
    assert "models" in arch_section


def test_repo_map_omitted_when_no_structure():
    gen = AgentsGenerator(Path("root"))
    md = gen.generate()
    assert "## Repository Map" not in md


def test_key_commands_install():
    gen = AgentsGenerator(Path("root"))
    data = ReadmeData(name="app", install_cmd="pip install app")
    md = gen.generate(readme_data=data)
    assert "## Key Commands" in md
    assert "pip install app" in md


def test_key_commands_dev_install():
    gen = AgentsGenerator(Path("root"))
    data = ReadmeData(name="app", dev_install_cmd="pip install -e .")
    md = gen.generate(readme_data=data)
    assert "pip install -e ." in md


def test_key_commands_from_scripts():
    gen = AgentsGenerator(Path("root"))
    scripts = ScriptsResult(
        package_json={"test": "vitest run", "build": "vite build"},
    )
    md = gen.generate(scripts=scripts)
    assert "## Key Commands" in md
    assert "vitest run" in md
    assert "vite build" in md


def test_key_commands_install_with_test_lint_fallback():
    """Install commands should appear alongside the test/lint fallback when no test scripts exist."""
    gen = AgentsGenerator(Path("root"))
    data = ReadmeData(name="app", install_cmd="pip install app")
    md = gen.generate(readme_data=data)
    assert "pip install app" in md
    assert "pytest" in md
    assert "ruff check" in md


def test_key_commands_default_fallback():
    gen = AgentsGenerator(Path("root"))
    md = gen.generate()
    assert "## Key Commands" in md
    assert "pytest" in md
    assert "ruff check" in md


def test_how_to_work_on_project():
    gen = AgentsGenerator(Path("root"))
    stats = StatsResult(
        total_files=5, total_lines=100, total_size=500,
        by_language={"Python": {"files": 3, "lines": 60, "size": 300}},
        largest_files=[],
    )
    md = gen.generate(stats=stats)
    assert "## How to Work on This Project" in md
    assert "Python" in md
    assert "Before committing" in md
    assert "Generated by repo-notes" in md


def test_how_to_with_python_requires():
    gen = AgentsGenerator(Path("root"))
    stats = StatsResult(
        total_files=5, total_lines=100, total_size=500,
        by_language={"Python": {"files": 3, "lines": 60, "size": 300}},
        largest_files=[],
    )
    data = ReadmeData(name="app", python_requires=">=3.10")
    md = gen.generate(stats=stats, readme_data=data)
    assert ">=3.10" in md


def test_how_to_filters_unknown():
    gen = AgentsGenerator(Path("root"))
    stats = StatsResult(
        total_files=5, total_lines=100, total_size=500,
        by_language={"Python": {"files": 3, "lines": 60, "size": 300},
                     "unknown": {"files": 2, "lines": 40, "size": 200}},
        largest_files=[],
    )
    md = gen.generate(stats=stats)
    assert "Python" in md
    assert "unknown" not in md


def test_how_to_sentence_natural_with_languages():
    gen = AgentsGenerator(Path("root"))
    stats = StatsResult(
        total_files=5, total_lines=100, total_size=500,
        by_language={"Python": {"files": 3, "lines": 60, "size": 300}},
        largest_files=[],
    )
    md = gen.generate(stats=stats)
    assert "This is a **Python** project." in md


def test_how_to_sentence_with_python_requires():
    gen = AgentsGenerator(Path("root"))
    stats = StatsResult(
        total_files=5, total_lines=100, total_size=500,
        by_language={"Python": {"files": 3, "lines": 60, "size": 300}},
        largest_files=[],
    )
    data = ReadmeData(name="app", python_requires=">=3.10")
    md = gen.generate(stats=stats, readme_data=data)
    assert "This is a **Python** (requires Python >=3.10) project." in md


def test_how_to_sentence_fallback_no_data():
    gen = AgentsGenerator(Path("root"))
    md = gen.generate()
    assert "This is a project." in md


def test_how_to_fallback_no_data():
    gen = AgentsGenerator(Path("root"))
    md = gen.generate()
    assert "## How to Work on This Project" in md


def test_json_convert_nested_dataclass():
    @dataclass
    class Inner:
        name: str
        value: int

    @dataclass
    class Outer:
        items: list[Inner]
        label: str

    obj = Outer(items=[Inner(name="a", value=1), Inner(name="b", value=2)], label="test")
    result = _json_convert(obj)
    assert result == {"items": [{"name": "a", "value": 1}, {"name": "b", "value": 2}], "label": "test"}
    assert json.dumps(result)  # verify JSON serializable


def test_json_convert_dict_with_dataclass_values():
    @dataclass
    class Item:
        id: str

    obj = {"items": [Item(id="x"), Item(id="y")], "count": 2}
    result = _json_convert(obj)
    assert result == {"items": [{"id": "x"}, {"id": "y"}], "count": 2}
    assert json.dumps(result)


# CLI integration tests

def test_cli_agents_flag():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "main.py").write_text("def main(): pass\n")
        result = subprocess.run(
            ["repo-notes", str(root), "--agents"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        agents_md = root / "AGENTS.md"
        assert agents_md.exists()
        content = agents_md.read_text()
        assert "# " in content
        assert "## Key Commands" in content


def test_cli_agents_with_format_notes():
    """--agents works alongside normal output formats."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "main.py").write_text("def main(): pass\n")
        result = subprocess.run(
            ["repo-notes", str(root), "--agents", "--format", "notes"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert (root / "REPO_NOTES.md").exists()
        assert (root / "AGENTS.md").exists()


def test_cli_json_format():
    """--format json must not crash on nested dataclasses like ProjectIntelligenceResult > DetectedTool."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "main.py").write_text("def main(): pass\n")
        (root / "pyproject.toml").write_text("[project]\nname = 'test-proj'\nversion = '0.1.0'\n")
        result = subprocess.run(
            ["repo-notes", str(root), "--format", "json", "--no-cache", "--quiet"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        json_output = root / "REPO_NOTES.json"
        assert json_output.exists()
        data = json.loads(json_output.read_text())
        assert isinstance(data, dict)
        assert len(data) > 0  # at least some sections present


# Snapshot tests — stable, reviewable full-output checks

def test_agents_snapshot_matches():
    """Full AgentsGenerator output with consistent inputs — no version brittleness."""
    gen = AgentsGenerator(Path("test-project"))
    data = ReadmeData(
        name="test-project", description="A test project",
        python_requires=">=3.10", runtime_deps=["click", "pyyaml"],
    )
    stats = StatsResult(
        total_files=10, total_lines=500, total_size=2000,
        by_language={
            "Python": {"files": 8, "lines": 400, "size": 1600},
            "TypeScript": {"files": 2, "lines": 100, "size": 400},
        },
        largest_files=[],
    )
    structure = StructureResult(
        tree="test-project/\nsrc/\n  main.py\ntests/\n  test_main.py\npyproject.toml\nREADME.md",
        file_count=3, dir_count=2,
    )
    scripts = ScriptsResult(package_json={"test": "pytest", "build": "python build.py"})
    arch = ArchitectureResult(
        layers={"services": [Path("src/service.py")], "utils": [Path("src/helpers.py")]},
        import_graph={"src/main.py": ["src/service", "src/helpers"], "src/service.py": ["src/helpers"]},
        entry_points=[Path("src/main.py")],
        circular_deps=[],
    )
    md = gen.generate(readme_data=data, stats=stats, structure=structure, scripts=scripts, arch=arch)
    assert md == (
        "# test-project\n"
        "\n"
        "A test project\n"
        "\n"
        "## Tech Stack\n"
        "\n"
        "- **Languages**: Python, TypeScript\n"
        "- **Python**: >=3.10\n"
        "- **Runtime deps**: click, pyyaml\n"
        "\n"
        "## Project Structure\n"
        "\n"
        "```text\n"
        "test-project/\n"
        "src/\n"
        "  main.py\n"
        "tests/\n"
        "  test_main.py\n"
        "pyproject.toml\n"
        "README.md\n"
        "```\n"
        "\n"
        "*3 files, 2 directories*\n"
        "\n"
        "## Repository Map\n"
        "\n"
        "- **README.md** — Project readme\n"
        "- **pyproject.toml** — Python project configuration\n"
        "- **src/** — Source code\n"
        "- **tests/** — Test suite\n"
        "\n"
        "## Architecture\n"
        "\n"
        "- **2** modules import **3** other modules\n"
        "- **2** layers detected: services, utils\n"
        "- Entry points: src/main.py\n"
        "\n"
        "## Key Commands\n"
        "\n"
        "```bash\n"
        "# Test\n"
        "pytest\n"
        "```\n"
        "```bash\n"
        "# Build\n"
        "python build.py\n"
        "```\n"
        "\n"
        "## How to Work on This Project\n"
        "\n"
        "This is a **Python, TypeScript** (requires Python >=3.10) project.\n"
        "\n"
        "Before committing changes, run tests and lint to verify nothing is broken.\n"
        "\n"
        "_Generated by repo-notes_\n"
    )
