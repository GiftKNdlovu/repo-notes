"""Integration tests for repo-notes."""

import subprocess
import tempfile
from pathlib import Path


def test_cli_scans_directory():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "main.py").write_text("def main(): pass\n")
        (root / "README.md").write_text("# Project\n")
        (root / "src" / "app.py").parent.mkdir()
        (root / "src" / "app.py").write_text("from flask import Flask\napp = Flask(__name__)\n")

        result = subprocess.run(
            ["repo-notes", str(root)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Done!" in result.stdout

        output_path = root / "REPO_NOTES.md"
        assert output_path.exists()
        content = output_path.read_text()
        assert "# Repository Notes:" in content
        assert "## Project Structure" in content
        assert "## Key Files" in content
        assert "## Code Statistics" in content
        assert "main.py" in content


def test_cli_output_flag():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "hello.py").write_text("print('hello')\n")
        output = root / "custom.md"

        result = subprocess.run(
            ["repo-notes", str(root), "--output", str(output)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert output.exists()
        assert output.read_text().startswith("# Repository Notes:")


def test_cli_with_config():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "hello.py").write_text("print('hello')\n")
        (root / ".repo-notes.yaml").write_text("extractors:\n  security: false\n  architecture: false\n")

        result = subprocess.run(
            ["repo-notes", str(root)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        output = (root / "REPO_NOTES.md").read_text()
        assert "## Security Notes" not in output


def test_cli_on_nonexistent_path():
    result = subprocess.run(
        ["repo-notes", "/nonexistent/path"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0


def test_full_pipeline():
    """End-to-end test with a realistic project structure."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Create a realistic project structure
        (root / "src" / "app" / "__init__.py").parent.mkdir(parents=True)
        (root / "src" / "app" / "main.py").write_text("""import sys
from app.service import handler

def main():
    handler()
    return 0

if __name__ == "__main__":
    sys.exit(main())
""")
        (root / "src" / "app" / "service.py").write_text("""from app.models import User

def handler():
    user = User(name="test")
    return user
""")
        (root / "src" / "app" / "models.py").write_text("""from dataclasses import dataclass

@dataclass
class User:
    name: str
""")
        (root / "tests" / "test_app.py").parent.mkdir()
        (root / "tests" / "test_app.py").write_text("""from app.main import main

def test_main():
    assert main() == 0
""")
        (root / "README.md").write_text("# My App\n\nA cool app.\n")
        (root / "pyproject.toml").write_text("""[project]
name = "my-app"
dependencies = ["click", "flask"]
""")
        (root / "requirements.txt").write_text("""click>=8.0
flask>=2.0
""")
        (root / ".gitignore").write_text("*.pyc\n__pycache__/\n")

        result = subprocess.run(
            ["repo-notes", str(root)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        output = (root / "REPO_NOTES.md").read_text()

        # Verify all expected sections
        assert "# Repository Notes:" in output
        assert "## Project Structure" in output
        assert "## Key Files" in output
        assert "## Code Statistics" in output
        assert "## Dependencies" in output
        assert "## Architecture Overview" in output
        assert "## Security Notes" in output

        # Verify content
        assert "main.py" in output
        assert "service.py" in output
        assert "models.py" in output
        assert "README.md" in output
        assert "pyproject.toml" in output
        assert "requirements.txt" in output


def test_quiet_suppresses_success_output():
    """--quiet should suppress Done! and scan messages but still create output."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "main.py").write_text("def main(): pass\n")

        result = subprocess.run(
            ["repo-notes", str(root), "--quiet"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Done!" not in result.stdout
        assert result.stdout.strip() == ""
        assert (root / "REPO_NOTES.md").exists()
        assert "# Repository Notes:" in (root / "REPO_NOTES.md").read_text()


def test_quiet_does_not_suppress_warnings():
    """--quiet should still show warnings on stderr."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # No files — should produce warning
        result = subprocess.run(
            ["repo-notes", str(root), "--quiet"],
            capture_output=True,
            text=True,
        )
        # Warning about no files is on stderr
        assert "No files found to scan" in result.stderr


def test_output_readme_mode():
    """--format readme --output should respect custom path."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "main.py").write_text("def main(): pass\n")
        output_path = root / "custom_README.md"

        result = subprocess.run(
            ["repo-notes", str(root), "--format", "readme", "--output", str(output_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert output_path.exists()
        # rnREADME.md should NOT be at the default location
        assert not (root / "rnREADME.md").exists()
        content = output_path.read_text()
        assert "# " in content


def test_output_both_mode():
    """--format both --output: notes goes to output, readme goes to sibling."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "main.py").write_text("def main(): pass\n")
        notes_path = root / "custom_notes.md"
        sibling_path = root / "rnREADME.md"

        result = subprocess.run(
            ["repo-notes", str(root), "--format", "both", "--output", str(notes_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert notes_path.exists()
        assert sibling_path.exists()
        assert "# Repository Notes:" in notes_path.read_text()
        assert "# " in sibling_path.read_text()


def test_agents_output_outside_repo_root():
    """--agents --output outside repo root should not write AGENTS.md to repo root."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "main.py").write_text("def main(): pass\n")
        # Output is in an entirely different directory (like /tmp)
        out_dir = Path(tempfile.mkdtemp())
        try:
            output_path = out_dir / "my_notes.md"

            result = subprocess.run(
                ["repo-notes", str(root), "--agents", "--output", str(output_path)],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
            # AGENTS.md should NOT be written to repo root
            assert not (root / "AGENTS.md").exists(), "AGENTS.md written to repo root despite --output elsewhere"
            # Agents should be written as sibling of --output
            agents_path = out_dir / "AGENTS.md"
            assert agents_path.exists()
            assert "## Key Commands" in agents_path.read_text()
        finally:
            import shutil
            shutil.rmtree(out_dir, ignore_errors=True)


def test_agents_default_uses_repo_root():
    """--agents without --output should write AGENTS.md to repo root."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "main.py").write_text("def main(): pass\n")

        result = subprocess.run(
            ["repo-notes", str(root), "--agents"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        agents_path = root / "AGENTS.md"
        assert agents_path.exists()
        assert "## Key Commands" in agents_path.read_text()


def test_both_format_fails_on_existing_sibling():
    """--format both --output exits non-zero when sibling rnREADME.md exists without --force."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "main.py").write_text("def main(): pass\n")
        # Create sibling rnREADME.md
        sibling = root / "rnREADME.md"
        sibling.write_text("existing content")

        notes_path = root / "my_notes.md"
        result = subprocess.run(
            ["repo-notes", str(root), "--format", "both", "--output", str(notes_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "should exit non-zero when sibling exists"
        assert "already exists" in result.stderr
        # Notes should NOT have been written (early exit before write)
        assert not notes_path.exists()


def test_both_format_with_force_writes_both():
    """--format both --output --force writes both artifacts when sibling exists."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "main.py").write_text("def main(): pass\n")
        # Create sibling rnREADME.md
        sibling = root / "rnREADME.md"
        sibling.write_text("existing content")

        notes_path = root / "my_notes.md"
        result = subprocess.run(
            ["repo-notes", str(root), "--format", "both", "--output", str(notes_path), "--force"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert notes_path.exists()
        assert sibling.exists()
        assert "# Repository Notes:" in notes_path.read_text()


def test_no_readme_overwrite_without_replace_readme():
    """Default commands should never modify hand-written README.md."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "main.py").write_text("def main(): pass\n")
        (root / "README.md").write_text("Hand-written README content")
        original = (root / "README.md").read_text()

        # Run default notes format — should not touch README.md
        result = subprocess.run(
            ["repo-notes", str(root)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert (root / "README.md").read_text() == original

        # Run readme format (writes rnREADME.md, not README.md)
        result2 = subprocess.run(
            ["repo-notes", str(root), "--format", "readme"],
            capture_output=True,
            text=True,
        )
        assert result2.returncode == 0
        assert (root / "README.md").read_text() == original
        assert (root / "rnREADME.md").exists()


def test_exclude_test_fixtures_in_config():
    """Security findings in test files can be suppressed with config."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Create a test file with a fake secret
        test_dir = root / "tests"
        test_dir.mkdir()
        (test_dir / "test_config.py").write_text(
            'aws_access_key_id = "AKIAIOSFODNN7EXAMPLE"\n'
        )
        # Create a real source file with a secret
        src_dir = root / "src"
        src_dir.mkdir()
        (src_dir / "config.py").write_text(
            'aws_access_key_id = "AKIAIOSFODNN7REALKEY"\n'
        )
        # Also create a .repo-notes.yaml with exclude_test_fixtures
        (root / ".repo-notes.yaml").write_text(
            "security:\n  exclude_test_fixtures: true\n"
        )

        result = subprocess.run(
            ["repo-notes", str(root), "--format", "json", "--no-cache", "--quiet"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        import json
        data = json.loads((root / "REPO_NOTES.json").read_text())
        sec = data.get("security", {})
        findings = sec.get("findings", [])
        # Real secret should be found, test fixture secret should be suppressed
        src_findings = [f for f in findings if "src/config.py" in f.get("file", "")]
        test_findings = [f for f in findings if "tests/test_config.py" in f.get("file", "")]
        assert len(src_findings) >= 1, "real source secret should still be reported"
        assert len(test_findings) == 0, "test fixture secrets should be suppressed with exclude_test_fixtures"
