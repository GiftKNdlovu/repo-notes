"""Tests for the HTML generator."""

from pathlib import Path

from repo_notes.extractors.architecture import ArchitectureResult
from repo_notes.extractors.dependencies import DependenciesResult
from repo_notes.extractors.git import GitResult
from repo_notes.extractors.security import SecurityResult
from repo_notes.extractors.stats import StatsResult
from repo_notes.extractors.structure import StructureResult
from repo_notes.html_generator import HtmlGenerator


def test_generates_html():
    gen = HtmlGenerator(Path("proj"))
    html = gen.generate()
    assert html.startswith("<!DOCTYPE html>")
    assert "</html>" in html


def test_title_in_html():
    gen = HtmlGenerator(Path("my-project"))
    html = gen.generate()
    assert "my-project" in html


def test_includes_structure():
    gen = HtmlGenerator(Path("proj"))
    html = gen.generate(
        structure=StructureResult(tree="proj/\n  main.py", file_count=1, dir_count=1)
    )
    assert "Project Structure" in html
    assert '<div class="tree">' in html
    assert 'class="tf"' in html
    assert 'class="tt"' in html
    assert 'class="ti"' in html


def test_includes_project_intelligence():
    from repo_notes.extractors import ProjectIntelligenceResult
    gen = HtmlGenerator(Path("proj"))
    html = gen.generate(
        project_intelligence=ProjectIntelligenceResult(categories={"readme": [Path("README.md")]})
    )
    assert "Project Intelligence" in html
    assert "README.md" in html


def test_includes_stats():
    gen = HtmlGenerator(Path("proj"))
    html = gen.generate(
        stats=StatsResult(
            total_files=10,
            total_lines=500,
            total_size=2048,
            by_language={"python": {"files": 5, "lines": 300, "size": 1024}},
            largest_files=[(Path("main.py"), 200)],
        )
    )
    assert "Code Statistics" in html
    assert "10" in html
    assert "python" in html


def test_includes_git():
    gen = HtmlGenerator(Path("proj"))
    html = gen.generate(
        git=GitResult(
            is_repo=True,
            current_branch="main",
            recent_commits=[
                {"hash": "abc12345", "author": "Alice", "date": "2024-01-01", "message": "Initial commit"}
            ],
            branches=["main", "dev"],
            contributors=[{"name": "Alice", "commits": 10}],
            remote_url="https://github.com/user/repo.git",
        )
    )
    assert "Git Information" in html
    assert "main" in html
    assert "Alice" in html


def test_includes_architecture():
    gen = HtmlGenerator(Path("proj"))
    html = gen.generate(
        arch=ArchitectureResult(
            layers={"models": [Path("user.py"), Path("post.py")]},
            entry_points=[Path("main.py")],
        )
    )
    assert "Architecture Overview" in html
    assert "Models" in html
    assert "main.py" in html


def test_includes_security():
    gen = HtmlGenerator(Path("proj"))
    html = gen.generate(
        security=SecurityResult(
            findings=[{"file": "config.py", "type": "API Key", "line": 5, "preview": "sk-*****"}],
            env_files=[Path(".env")],
        )
    )
    assert "Security Notes" in html
    assert ".env" in html
    assert "API Key" in html


def test_includes_dependencies():
    gen = HtmlGenerator(Path("proj"))
    html = gen.generate(
        deps=DependenciesResult(
            python={"requirements.txt": ["flask", "requests"]},
        )
    )
    assert "Dependencies" in html
    assert "Python" in html
    assert "requirements.txt" in html


def test_omits_git_when_not_repo():
    gen = HtmlGenerator(Path("proj"))
    html = gen.generate(
        git=GitResult(is_repo=False)
    )
    assert "Git Information" not in html


def test_includes_sidebar():
    gen = HtmlGenerator(Path("proj"))
    html = gen.generate(
        structure=StructureResult(tree="proj/", file_count=1, dir_count=0),
        stats=StatsResult(total_files=1, total_lines=10, total_size=100, by_language={}, largest_files=[]),
    )
    assert 'class="sidebar"' in html
    assert "sidebar-link" in html


def test_includes_badges():
    gen = HtmlGenerator(Path("proj"))
    html = gen.generate(
        stats=StatsResult(total_files=5, total_lines=100, total_size=500, by_language={}, largest_files=[]),
    )
    assert 'class="badges"' in html
    assert "5 files" in html


def test_theme_toggle():
    gen = HtmlGenerator(Path("proj"))
    html = gen.generate()
    assert "toggleTheme" in html


def test_search():
    gen = HtmlGenerator(Path("proj"))
    html = gen.generate()
    assert "filterSections" in html


def test_section_order():
    gen = HtmlGenerator(Path("proj"))
    html = gen.generate(
        structure=StructureResult(tree="proj/", file_count=1, dir_count=0),
        stats=StatsResult(total_files=1, total_lines=10, total_size=100, by_language={}, largest_files=[]),
        section_order=["stats", "structure"],
    )
    assert html.index("Code Statistics") < html.index("Project Structure")


def test_empty_sections():
    gen = HtmlGenerator(Path("proj"))
    html = gen.generate()
    assert 'class="section"' not in html  # no sections rendered when nothing passed


def test_has_css():
    gen = HtmlGenerator(Path("proj"))
    html = gen.generate()
    assert "<style>" in html
    assert ":root" in html
    assert ".dark " in html


def test_has_js():
    gen = HtmlGenerator(Path("proj"))
    html = gen.generate()
    assert "<script>" in html


def test_security_badge_high():
    gen = HtmlGenerator(Path("proj"))
    html = gen.generate(
        security=SecurityResult(
            findings=[{"file": "x.py", "type": "Key", "line": 1, "preview": "sk-****", "test_fixture": False}],
            env_files=[],
        ),
        stats=StatsResult(total_files=1, total_lines=10, total_size=100, by_language={}, largest_files=[]),
    )
    assert "badge-danger" in html
    assert ">1 high<" in html


def test_security_badge_mild():
    gen = HtmlGenerator(Path("proj"))
    html = gen.generate(
        security=SecurityResult(
            findings=[],
            high_entropy_strings=[{"file": "x.py", "entropy": 4.5, "line": 1, "preview": "abc", "test_fixture": False}],
            env_files=[],
        ),
        stats=StatsResult(total_files=1, total_lines=10, total_size=100, by_language={}, largest_files=[]),
    )
    assert "badge-warning" in html
    assert ">1 mild<" in html


def test_security_badge_none():
    gen = HtmlGenerator(Path("proj"))
    html = gen.generate(
        security=SecurityResult(findings=[], high_entropy_strings=[], env_files=[]),
        stats=StatsResult(total_files=1, total_lines=10, total_size=100, by_language={}, largest_files=[]),
    )
    assert "badge-success" in html
    assert "0 issues" in html


def test_security_badge_fixture_only():
    gen = HtmlGenerator(Path("proj"))
    html = gen.generate(
        security=SecurityResult(
            findings=[{"file": "tests/x.py", "type": "Key", "line": 1, "preview": "sk-****", "test_fixture": True}],
            high_entropy_strings=[{"file": "tests/y.py", "entropy": 4.5, "line": 1, "preview": "abc123", "test_fixture": True}],
            env_files=[],
        ),
        stats=StatsResult(total_files=1, total_lines=10, total_size=100, by_language={}, largest_files=[]),
    )
    assert "0 real" in html
    assert "1 fixture high" in html
    assert "1 fixture mild" in html


def test_security_badge_mixed():
    gen = HtmlGenerator(Path("proj"))
    html = gen.generate(
        security=SecurityResult(
            findings=[
                {"file": "config.py", "type": "Key", "line": 1, "preview": "sk-****", "test_fixture": False},
                {"file": "tests/test_keys.py", "type": "Key", "line": 5, "preview": "sk-****", "test_fixture": True},
            ],
            high_entropy_strings=[
                {"file": "main.py", "entropy": 4.5, "line": 1, "preview": "abc123", "test_fixture": False},
            ],
            env_files=[],
        ),
        stats=StatsResult(total_files=1, total_lines=10, total_size=100, by_language={}, largest_files=[]),
    )
    assert ">1 high<" in html
    assert ">1 fixture high<" in html
    assert ">1 mild<" in html


def test_tree_nested_directories():
    gen = HtmlGenerator(Path("proj"))
    tree = "proj/\n  src/\n    main.py\n  README.md"
    html = gen.generate(
        structure=StructureResult(tree=tree, file_count=2, dir_count=2)
    )
    assert 'class="tf"' in html
    assert 'class="tt"' in html
    assert 'class="ti"' in html
    assert "2 files, 2 directories" in html
    assert html.count("<ul>") > 1


def test_tree_empty():
    gen = HtmlGenerator(Path("proj"))
    html = gen.generate()
    assert "<div" not in html or 'class="section"' not in html


def test_security_high_entropy_see_more():
    gen = HtmlGenerator(Path("proj"))
    html = gen.generate(
        security=SecurityResult(
            findings=[],
            high_entropy_strings=[{"file": "x.py", "entropy": 4.5, "line": 1, "preview": "abcdef123456"}],
            env_files=[],
        )
    )
    assert "class='see-more'" in html
    assert "<summary>High Entropy Strings" in html


def test_security_findings_open_by_default():
    gen = HtmlGenerator(Path("proj"))
    html = gen.generate(
        security=SecurityResult(
            findings=[{"file": "config.py", "type": "API Key", "line": 5, "preview": "sk-*****"}],
            env_files=[],
        )
    )
    assert "Potential Secrets" in html
    assert "config.py" in html


# CLI integration tests
def test_cli_html_format():
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "main.py").write_text("def main(): pass\n")
        result = subprocess.run(
            ["repo-notes", str(root), "--format", "html"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        html_file = root / "REPO_NOTES.html"
        assert html_file.exists()
        content = html_file.read_text()
        assert "<!DOCTYPE html>" in content
        assert "</html>" in content
